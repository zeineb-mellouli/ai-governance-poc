import json

import jsonschema

from agents import remediation_agent
from agents.orchestrator import run_audit, write_reports
from agents.schemas import ComplianceReport, Finding, FindingStatus, RemediationStatus
from tests.fakes import FAKE_FINGERPRINT, FakeOpenAIClient, verdict

NON_COMPLIANT_REPO = "sample_repos/non_compliant/FinalProject"

SECRET_QUOTE = 'api_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"'


def _finding(policy_id: str, severity: str, status: FindingStatus) -> Finding:
    return Finding(
        policy_id=policy_id, title=policy_id, severity=severity, file_path="a.py",
        status=status, confidence_score=1.0, evidence="e",
        retrieval_chunk_id=policy_id, retrieval_score=0.1,
    )


def _report(*findings: Finding) -> ComplianceReport:
    return ComplianceReport(repo_name="r", repo_path="/r", findings=list(findings))


def test_run_audit_end_to_end_attaches_remediation_above_confidence_threshold():
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "final_v2_ACTUAL.py": [
                verdict("SEC-3", quote=SECRET_QUOTE,
                        evidence="hardcoded api_key and connection_string"),
            ],
        },
        remediation_by_policy_id={
            "SEC-3": {"description": "Move secrets to environment variables",
                      "fix": 'api_key = os.environ["API_KEY"]'},
        },
    )

    report = run_audit(NON_COMPLIANT_REPO, client=client)

    assert report.repo_name == "FinalProject"
    sec3 = [f for f in report.findings if f.policy_id == "SEC-3" and f.file_path == "final_v2_ACTUAL.py"]
    assert len(sec3) == 1
    assert sec3[0].status == FindingStatus.NON_COMPLIANT
    assert sec3[0].remediation_status == RemediationStatus.AUTO_FIXED
    assert "API_KEY" in sec3[0].remediation.fix


def test_low_confidence_finding_keeps_its_verdict_but_gets_no_fix():
    """The confidence gate withholds the fix. It must not restate the verdict.

    An uncertain verdict still stands as the Auditor's finding; what an uncertain
    verdict must not do is produce an executable command. Those are separate
    axes, and collapsing them is what buried real violations in the review queue.

    Confidence is now the sample agreement rate, so the gate is exercised
    directly on a finding rather than by scripting a model into low confidence.
    """
    finding = Finding(
        policy_id="REPRO-6", title="Random seeds fixed for stochastic steps", severity="MEDIUM",
        file_path="final_v2_ACTUAL.py", status=FindingStatus.NON_COMPLIANT,
        confidence_score=0.33, evidence="no random_state set",
        retrieval_chunk_id="REPRO-6", retrieval_score=0.1,
    )

    errors = remediation_agent.remediate([finding], {}, client=FakeOpenAIClient())

    assert not errors
    assert finding.status == FindingStatus.NON_COMPLIANT
    assert finding.remediation is None
    assert finding.remediation_status == RemediationStatus.SKIPPED_LOW_CONFIDENCE
    assert finding.needs_human_attention


def test_deterministic_naming_violations_do_not_reach_the_review_queue():
    """Regression: every NAM-5 naming violation used to land in NEEDS_REVIEW.

    The Remediation Agent was handed a confidence-1.0 filename violation along
    with the file's *contents*, found nothing wrong in the contents, answered
    NO_FIX_REQUIRED, and the pipeline rewrote the verdict as needing human
    review. 30 of 32 review-queue entries across the sample corpus were this.
    """
    client = FakeOpenAIClient()

    report = run_audit(NON_COMPLIANT_REPO, client=client)

    naming = [f for f in report.findings if f.policy_id == "NAM-5" and f.file_path is not None]
    assert naming, "expected deterministic naming findings"
    assert not [f for f in naming if f.status == FindingStatus.NEEDS_REVIEW]

    fixed = [f for f in naming if f.remediation_status == RemediationStatus.AUTO_FIXED]
    assert fixed, "expected at least one auto-derived rename"
    assert all(f.remediation.fix.startswith("git mv ") for f in fixed)


def test_report_records_the_serving_backend_fingerprint():
    report = run_audit(NON_COMPLIANT_REPO, client=FakeOpenAIClient())
    assert report.model_fingerprints == [FAKE_FINGERPRINT]


def test_samples_flag_is_honoured_and_recorded_on_the_report():
    """k has to be on the report: it changes what confidence_score means."""
    client = FakeOpenAIClient()
    report = run_audit(NON_COMPLIANT_REPO, client=client, samples=1)

    assert report.audit_samples == 1
    # One model call per file that has candidate policies, not three.
    assert client.call_count("File path: final_v2_ACTUAL.py") == 1

    client3 = FakeOpenAIClient()
    report3 = run_audit(NON_COMPLIANT_REPO, client=client3, samples=3)
    assert report3.audit_samples == 3
    assert client3.call_count("File path: final_v2_ACTUAL.py") == 3


# --- repo-level compliance score --------------------------------------------


def test_clean_repo_scores_a_full_pass():
    report = _report(*[_finding(f"P-{i}", "HIGH", FindingStatus.COMPLIANT) for i in range(20)])
    score = report.compliance_score
    assert score["weighted_pass_rate"] == 1.0
    assert score["grade"] == "PASS"
    assert score["gate"] is None


def test_not_applicable_is_excluded_from_the_denominator():
    """A check that was correctly skipped is not a check that passed."""
    report = _report(
        _finding("A", "HIGH", FindingStatus.COMPLIANT),
        *[_finding(f"N-{i}", "HIGH", FindingStatus.NOT_APPLICABLE) for i in range(50)],
    )
    assert report.compliance_score["weighted_pass_rate"] == 1.0
    assert report.compliance_score["weight_possible"] == 3


def test_one_high_violation_caps_the_grade_at_fail_however_good_the_rate():
    """The gate is the point: one hardcoded credential must not drown in 300 passes."""
    report = _report(
        *[_finding(f"P-{i}", "LOW", FindingStatus.COMPLIANT) for i in range(300)],
        _finding("SEC-3", "HIGH", FindingStatus.NON_COMPLIANT),
    )
    score = report.compliance_score
    assert score["weighted_pass_rate"] > 0.98
    assert score["grade"] == "FAIL"
    assert "HIGH-severity" in score["gate"]


def test_three_medium_violations_cap_the_grade_at_needs_work():
    report = _report(
        *[_finding(f"P-{i}", "LOW", FindingStatus.COMPLIANT) for i in range(300)],
        *[_finding(f"M-{i}", "MEDIUM", FindingStatus.NON_COMPLIANT) for i in range(3)],
    )
    assert report.compliance_score["grade"] == "NEEDS_WORK"


def test_score_separates_a_small_dirty_repo_from_a_large_clean_one():
    """The failure of the old summed risk_score: repo size moved it as much as quality.

    345 checks with 5 violations used to score within 3 points of 66 checks with
    5 violations. A rate plus a gate puts them in different categories.
    """
    large_clean = _report(
        *[_finding(f"P-{i}", "MEDIUM", FindingStatus.COMPLIANT) for i in range(340)],
        *[_finding(f"L-{i}", "LOW", FindingStatus.NON_COMPLIANT) for i in range(2)],
    )
    small_dirty = _report(
        *[_finding(f"P-{i}", "MEDIUM", FindingStatus.COMPLIANT) for i in range(60)],
        *[_finding(f"H-{i}", "HIGH", FindingStatus.NON_COMPLIANT) for i in range(2)],
    )
    assert large_clean.compliance_score["grade"] == "PASS"
    assert small_dirty.compliance_score["grade"] == "FAIL"
    assert large_clean.compliance_score["weighted_pass_rate"] > small_dirty.compliance_score["weighted_pass_rate"]


def test_undecided_verdicts_are_excluded_and_surfaced():
    """An undecided verdict is not evidence either way, and must not be hidden."""
    report = _report(
        _finding("A", "HIGH", FindingStatus.COMPLIANT),
        _finding("B", "HIGH", FindingStatus.NEEDS_REVIEW),
    )
    score = report.compliance_score
    assert score["weighted_pass_rate"] == 1.0
    assert score["undecided"] == 1


def test_write_reports_produces_schema_valid_json_and_readable_markdown(tmp_path):
    client = FakeOpenAIClient(
        verdicts_by_path_substring={
            "final_v2_ACTUAL.py": [verdict("SEC-3", quote=SECRET_QUOTE)],
        },
        remediation_by_policy_id={"SEC-3": {"description": "d", "fix": "f"}},
    )
    report = run_audit(NON_COMPLIANT_REPO, client=client)

    machine_path, draft_path = write_reports(report, str(tmp_path))

    schema = json.loads(open("report_schema.json").read())
    machine_report = json.loads(machine_path.read_text())
    jsonschema.validate(instance=machine_report, schema=schema)

    draft_text = draft_path.read_text()
    assert "Non-compliant findings" in draft_text
    assert "SEC-3" in draft_text
