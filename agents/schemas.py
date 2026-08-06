"""Shared data contracts for the runtime AGA pipeline (Repository -> Auditor -> Remediation -> Orchestrator)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field

SEVERITY_WEIGHT = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# Grades, worst-last. A repository's grade is the worse of what its pass rate
# earns and what the severity gate allows.
GRADE_ORDER = ["PASS", "NEEDS_WORK", "FAIL"]

# Pass-rate bands. Deliberately demanding: these are checks a repository is
# expected to satisfy by construction, not a test suite where 90% is good.
PASS_RATE_THRESHOLD = 0.98
NEEDS_WORK_RATE_THRESHOLD = 0.90

# Severity gate. A weighted rate alone lets one hardcoded credential drown in
# 300 passing checks, which is how a compliant-looking score hides the finding
# that actually matters. This is the same shape as a CIS Benchmark or AWS
# Security Hub score: a rate, plus a floor that severity can force.
MEDIUM_FAILURES_BEFORE_CAP = 3


class FileType(str, Enum):
    PYTHON = "python"
    SQL = "sql"
    NOTEBOOK = "notebook"
    YAML = "yaml"
    CSV = "csv"
    MARKDOWN = "markdown"
    OTHER = "other"


class FindingStatus(str, Enum):
    """The Auditor's verdict. Only the Auditor may set this.

    The Remediation Agent must never write to it: whether a fix could be
    generated says nothing about whether the violation is real, and conflating
    the two put 30 confidence-1.0 deterministic naming violations into the
    "low-confidence, needs human review" bucket. Remediation outcome lives on
    its own axis, in RemediationStatus.
    """

    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class RemediationStatus(str, Enum):
    """What happened when we tried to produce a fix -- orthogonal to FindingStatus."""

    NOT_REQUIRED = "NOT_REQUIRED"                  # not a violation, so nothing to fix
    AUTO_FIXED = "AUTO_FIXED"                      # a fix is attached and passed the safety net
    NO_FIX_AVAILABLE = "NO_FIX_AVAILABLE"          # no fix derivable without author judgement
    UNSAFE_FIX_REJECTED = "UNSAFE_FIX_REJECTED"    # model produced a fix the safety net refused
    SKIPPED_LOW_CONFIDENCE = "SKIPPED_LOW_CONFIDENCE"  # verdict too uncertain to auto-fix
    FAILED = "FAILED"                              # the remediation call itself errored


class FileRecord(BaseModel):
    path: str
    file_type: FileType
    content: str
    csv_columns: Optional[list[str]] = None


class RepositorySnapshot(BaseModel):
    repo_root_name: str
    repo_path: str
    has_readme: bool
    files: list[FileRecord]


class Remediation(BaseModel):
    description: str
    fix: str


class Finding(BaseModel):
    policy_id: str
    title: str
    severity: str
    file_path: Optional[str] = None
    status: FindingStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence: str
    # The model's own working-out. Given its own field so the model stops using
    # `evidence` as a scratchpad -- deliberation leaking into evidence ("...does
    # it end with Fact? It does... Overall compliant.") is what the retired
    # prose-regex guard was trying to catch after the fact.
    reasoning: str = ""
    retrieval_chunk_id: str
    retrieval_score: float
    remediation: Optional[Remediation] = None
    remediation_status: RemediationStatus = RemediationStatus.NOT_REQUIRED
    remediation_note: Optional[str] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def risk_score(self) -> float:
        return round(SEVERITY_WEIGHT.get(self.severity, 0) * self.confidence_score, 3)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def needs_human_attention(self) -> bool:
        """True when a person has to act: an undecided verdict, or a violation with no usable fix."""
        if self.status == FindingStatus.NEEDS_REVIEW:
            return True
        return (
            self.status == FindingStatus.NON_COMPLIANT
            and self.remediation_status != RemediationStatus.AUTO_FIXED
        )


class ComplianceReport(BaseModel):
    repo_name: str
    repo_path: str
    run_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    findings: list[Finding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    # Distinct OpenAI system_fingerprint values seen during the run. More than
    # one value, or a change between runs, means the serving backend moved --
    # which distinguishes "our pipeline is non-deterministic" from "the model
    # underneath us changed". Without it the two are indistinguishable.
    model_fingerprints: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def summary(self) -> dict:
        by_status: dict[str, int] = {}
        by_remediation_status: dict[str, int] = {}
        non_compliant_by_severity: dict[str, int] = {}
        for f in self.findings:
            by_status[f.status.value] = by_status.get(f.status.value, 0) + 1
            if f.status == FindingStatus.NON_COMPLIANT:
                non_compliant_by_severity[f.severity] = non_compliant_by_severity.get(f.severity, 0) + 1
                by_remediation_status[f.remediation_status.value] = (
                    by_remediation_status.get(f.remediation_status.value, 0) + 1
                )
        # applicable_checks is the denominator any compliance rate has to use:
        # NOT_APPLICABLE is a check that was correctly skipped, not one that passed.
        applicable = by_status.get("COMPLIANT", 0) + by_status.get("NON_COMPLIANT", 0)
        return {
            "total_findings": len(self.findings),
            "checks_evaluated": len(self.findings),
            "applicable_checks": applicable,
            "by_status": by_status,
            "non_compliant_by_severity": non_compliant_by_severity,
            "non_compliant_by_remediation_status": by_remediation_status,
            "needs_human_attention": sum(1 for f in self.findings if f.needs_human_attention),
        }

    @computed_field  # type: ignore[prop-decorator]
    @property
    def compliance_score(self) -> dict:
        """Severity-weighted pass rate over applicable checks, plus a severity gate.

        Replaces the previous practice of summing per-finding risk_score, which
        was unnormalised: a 345-check repository with 5 violations and a 66-check
        repository with 5 violations scored three points apart, so repo size
        moved the number as much as repo quality did.

        NOT_APPLICABLE is excluded from the denominator -- a check that was
        correctly skipped is not a check that passed. NEEDS_REVIEW is excluded
        from both sides and reported separately: an undecided verdict is not
        evidence either way, and burying it in the rate would let a repository
        score well by being unreadable.
        """
        earned = possible = 0
        high_failures = medium_failures = 0
        undecided = 0

        for finding in self.findings:
            weight = SEVERITY_WEIGHT.get(finding.severity, 0)
            if finding.status == FindingStatus.COMPLIANT:
                possible += weight
                earned += weight
            elif finding.status == FindingStatus.NON_COMPLIANT:
                possible += weight
                if finding.severity == "HIGH":
                    high_failures += 1
                elif finding.severity == "MEDIUM":
                    medium_failures += 1
            elif finding.status == FindingStatus.NEEDS_REVIEW:
                undecided += 1

        if not possible:
            return {
                "weighted_pass_rate": None,
                "grade": "NOT_SCORED",
                "gate": None,
                "high_failures": high_failures,
                "medium_failures": medium_failures,
                "undecided": undecided,
                "weight_earned": earned,
                "weight_possible": possible,
            }

        rate = round(earned / possible, 4)

        if rate >= PASS_RATE_THRESHOLD:
            rate_grade = "PASS"
        elif rate >= NEEDS_WORK_RATE_THRESHOLD:
            rate_grade = "NEEDS_WORK"
        else:
            rate_grade = "FAIL"

        if high_failures:
            gate_grade = "FAIL"
            gate = f"{high_failures} HIGH-severity violation(s) cap the grade at FAIL"
        elif medium_failures >= MEDIUM_FAILURES_BEFORE_CAP:
            gate_grade = "NEEDS_WORK"
            gate = f"{medium_failures} MEDIUM-severity violations cap the grade at NEEDS_WORK"
        else:
            gate_grade = "PASS"
            gate = None

        grade = max([rate_grade, gate_grade], key=GRADE_ORDER.index)

        return {
            "weighted_pass_rate": rate,
            "grade": grade,
            "gate": gate,
            "high_failures": high_failures,
            "medium_failures": medium_failures,
            "undecided": undecided,
            "weight_earned": earned,
            "weight_possible": possible,
        }
