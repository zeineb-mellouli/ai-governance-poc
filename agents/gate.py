"""CI gate: turn a compliance report into a pass/fail decision and an exit code.

Lives outside main.py so that "what blocks a merge" is testable without going
through the CLI, and so the `audit` and `batch` commands cannot drift apart on
the question.

Three independent thresholds, all off by default:

  fail_on        a NON_COMPLIANT finding at this severity or above
  fail_on_grade  the repository's computed grade is this or worse
  fail_on_error  the audit did not complete cleanly

The third exists because the first two are only meaningful if the audit
actually ran. A run that errors on most of its files produces few findings, a
flattering pass rate and a green build -- a gate that passes because the audit
crashed is worse than no gate at all. It is opt-in rather than always-on
because partial failure is tolerated by design elsewhere in the pipeline
(one bad file must not abort a run), so whether it should block is the
caller's policy decision, not ours.
"""

from dataclasses import dataclass, field
from enum import Enum

from agents.schemas import ComplianceReport, Finding, FindingStatus

# Worst-last, matching schemas.GRADE_ORDER.
SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
GRADE_RANK = {"PASS": 0, "NEEDS_WORK": 1, "FAIL": 2}


# Enums rather than plain strings so the CLI renders the allowed values in
# --help and rejects a typo before the audit spends anything.
class SeverityGate(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class GradeGate(str, Enum):
    PASS = "PASS"
    NEEDS_WORK = "NEEDS_WORK"
    FAIL = "FAIL"


@dataclass
class GateResult:
    """The gate's decision, plus enough detail for a CI log to be actionable."""

    passed: bool
    reasons: list[str] = field(default_factory=list)
    tripped: list[Finding] = field(default_factory=list)
    # Counts shown whether the gate passes or fails, so a green build still
    # reports what was actually evaluated.
    high: int = 0
    medium: int = 0
    low: int = 0
    grade: str = "NOT_SCORED"
    undecided: int = 0
    errors: int = 0

    @property
    def exit_code(self) -> int:
        return 0 if self.passed else 1

    @property
    def label(self) -> str:
        return "PASS" if self.passed else "FAIL"


def evaluate(
    report: ComplianceReport,
    fail_on: SeverityGate | str | None = None,
    fail_on_grade: GradeGate | str | None = None,
    fail_on_error: bool = False,
) -> GateResult:
    """Decide whether this report should block. No threshold set means never block."""
    fail_on = fail_on.value if isinstance(fail_on, SeverityGate) else fail_on
    fail_on_grade = fail_on_grade.value if isinstance(fail_on_grade, GradeGate) else fail_on_grade

    by_severity = report.summary["non_compliant_by_severity"]
    score = report.compliance_score

    result = GateResult(
        passed=True,
        high=by_severity.get("HIGH", 0),
        medium=by_severity.get("MEDIUM", 0),
        low=by_severity.get("LOW", 0),
        grade=score["grade"],
        undecided=score["undecided"],
        errors=len(report.errors),
    )

    if fail_on:
        threshold = SEVERITY_RANK[fail_on.upper()]
        tripped = [
            f for f in report.findings
            if f.status == FindingStatus.NON_COMPLIANT
            and SEVERITY_RANK.get(f.severity, -1) >= threshold
        ]
        if tripped:
            # Worst first, so a truncated CI log still shows the worst offender.
            tripped.sort(key=lambda f: (-SEVERITY_RANK.get(f.severity, -1), f.policy_id, f.file_path or ""))
            result.passed = False
            result.tripped = tripped
            result.reasons.append(
                f"{len(tripped)} NON_COMPLIANT finding(s) at severity {fail_on.upper()} or above"
            )

    if fail_on_grade:
        # NOT_SCORED means nothing applicable was evaluated. It is not a passing
        # grade, but it is not a failing one either -- it means the run did not
        # produce a judgement, which is what fail_on_error is for.
        if result.grade in GRADE_RANK and GRADE_RANK[result.grade] >= GRADE_RANK[fail_on_grade.upper()]:
            result.passed = False
            result.reasons.append(
                f"grade {result.grade} is at or below the threshold {fail_on_grade.upper()}"
            )

    if fail_on_error and report.errors:
        result.passed = False
        result.reasons.append(
            f"{len(report.errors)} partial failure(s) during the run -- "
            f"the audit did not complete, so a pass would be vacuous"
        )

    return result


def worst(results: list[GateResult]) -> GateResult:
    """Combine per-repo gate results for a batch: any failure fails the batch."""
    combined = GateResult(passed=all(r.passed for r in results))
    for r in results:
        combined.high += r.high
        combined.medium += r.medium
        combined.low += r.low
        combined.undecided += r.undecided
        combined.errors += r.errors
    failed = [r for r in results if not r.passed]
    combined.grade = max(
        (r.grade for r in results if r.grade in GRADE_RANK),
        key=lambda g: GRADE_RANK[g],
        default="NOT_SCORED",
    )
    if failed:
        combined.reasons.append(f"{len(failed)} of {len(results)} repositories failed the gate")
    return combined
