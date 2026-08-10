"""The CI gate: what blocks a merge, and what must never silently pass."""

from agents import gate
from agents.schemas import ComplianceReport, Finding, FindingStatus


def _finding(policy_id: str, severity: str, status: FindingStatus) -> Finding:
    return Finding(
        policy_id=policy_id, title=policy_id, severity=severity, file_path="a.py",
        status=status, confidence_score=1.0, evidence="e",
        retrieval_chunk_id=policy_id, retrieval_score=0.1,
    )


def _report(*findings: Finding, errors: list[str] | None = None) -> ComplianceReport:
    return ComplianceReport(
        repo_name="r", repo_path="/r", findings=list(findings), errors=errors or [],
    )


def test_no_thresholds_never_blocks():
    """Gating is opt-in: the default must not change anyone's exit code."""
    report = _report(_finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT))
    result = gate.evaluate(report)
    assert result.passed
    assert result.exit_code == 0
    assert result.reasons == []


def test_fail_on_high_blocks_a_high_violation():
    report = _report(_finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT))
    result = gate.evaluate(report, fail_on="HIGH")
    assert not result.passed
    assert result.exit_code == 1
    assert [f.policy_id for f in result.tripped] == ["SEC-3"]


def test_fail_on_high_ignores_lower_severities():
    report = _report(
        _finding("NAM-5", "LOW", FindingStatus.NON_COMPLIANT),
        _finding("GIT-8", "MEDIUM", FindingStatus.NON_COMPLIANT),
    )
    assert gate.evaluate(report, fail_on="HIGH").passed


def test_severity_threshold_is_inclusive_upward():
    """--fail-on MEDIUM must also catch HIGH, not only MEDIUM."""
    report = _report(_finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT))
    result = gate.evaluate(report, fail_on="MEDIUM")
    assert not result.passed
    assert [f.policy_id for f in result.tripped] == ["SEC-3"]


def test_only_non_compliant_findings_trip_the_gate():
    """A compliant or undecided check is not a violation."""
    report = _report(
        _finding("SEC-3", "HIGH", FindingStatus.COMPLIANT),
        _finding("DQ-1", "HIGH", FindingStatus.NEEDS_REVIEW),
        _finding("PII-4", "HIGH", FindingStatus.NOT_APPLICABLE),
    )
    assert gate.evaluate(report, fail_on="HIGH").passed


def test_tripped_findings_are_worst_first():
    """A truncated CI log must still show the worst offender."""
    report = _report(
        _finding("NAM-5", "LOW", FindingStatus.NON_COMPLIANT),
        _finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT),
        _finding("GIT-8", "MEDIUM", FindingStatus.NON_COMPLIANT),
    )
    result = gate.evaluate(report, fail_on="LOW")
    assert [f.severity for f in result.tripped] == ["HIGH", "MEDIUM", "LOW"]


def test_fail_on_grade_blocks_at_or_below_the_threshold():
    report = _report(
        *[_finding(f"P-{i}", "LOW", FindingStatus.COMPLIANT) for i in range(300)],
        _finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT),
    )
    assert report.compliance_score["grade"] == "FAIL"
    assert not gate.evaluate(report, fail_on_grade="FAIL").passed
    assert not gate.evaluate(report, fail_on_grade="NEEDS_WORK").passed  # FAIL is worse
    # A clean repo grades PASS and clears even the strictest grade threshold.
    clean = _report(*[_finding(f"P-{i}", "HIGH", FindingStatus.COMPLIANT) for i in range(10)])
    assert gate.evaluate(clean, fail_on_grade="NEEDS_WORK").passed


def test_a_crashed_audit_must_not_read_as_a_pass():
    """The reason fail_on_error exists.

    A run that errors on most of its files produces few findings and a
    flattering rate. Without this gate the build goes green because the audit
    broke, which is worse than having no gate.
    """
    report = _report(
        _finding("SEC-3", "HIGH", FindingStatus.COMPLIANT),
        errors=["Auditor Agent failed on a.py: timeout",
                "Auditor Agent failed on b.py: timeout"],
    )
    assert gate.evaluate(report, fail_on="HIGH").passed          # nothing to flag
    assert gate.evaluate(report, fail_on="HIGH", fail_on_error=True).passed is False
    assert "did not complete" in gate.evaluate(report, fail_on_error=True).reasons[0]


def test_counts_are_reported_even_when_the_gate_passes():
    """A green build should still say what was evaluated."""
    report = _report(
        _finding("NAM-5", "LOW", FindingStatus.NON_COMPLIANT),
        _finding("DQ-1", "HIGH", FindingStatus.NEEDS_REVIEW),
    )
    result = gate.evaluate(report, fail_on="HIGH")
    assert result.passed
    assert result.low == 1
    assert result.undecided == 1


def test_thresholds_combine_and_report_every_reason():
    report = _report(
        _finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT),
        errors=["boom"],
    )
    result = gate.evaluate(report, fail_on="HIGH", fail_on_grade="FAIL", fail_on_error=True)
    assert not result.passed
    assert len(result.reasons) == 3


def test_enum_values_are_accepted_as_well_as_strings():
    report = _report(_finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT))
    assert not gate.evaluate(report, fail_on=gate.SeverityGate.HIGH).passed
    assert not gate.evaluate(report, fail_on_grade=gate.GradeGate.FAIL).passed


def test_batch_fails_if_any_single_repo_fails():
    passing = gate.GateResult(passed=True, grade="PASS", high=0)
    failing = gate.GateResult(passed=False, grade="FAIL", high=2, reasons=["nope"])

    assert gate.worst([passing, passing]).passed
    combined = gate.worst([passing, failing, passing])
    assert not combined.passed
    assert combined.high == 2
    assert combined.grade == "FAIL"          # worst grade across the batch
    assert "1 of 3 repositories failed" in combined.reasons[-1]


def test_batch_of_nothing_passes():
    assert gate.worst([]).passed
