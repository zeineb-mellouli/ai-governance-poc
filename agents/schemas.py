"""Shared data contracts for the runtime AGA pipeline (Repository -> Auditor -> Remediation -> Orchestrator)."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field

SEVERITY_WEIGHT = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

# There was a PASS / NEEDS_WORK / FAIL grade here, from a weighted pass rate
# banded at 98% and 90% with a cap forced by severity. It is gone deliberately.
#
# The bands were never validated against anything -- they were a first guess --
# and on the reference corpus they graded 8 of 10 repositories FAIL, including
# four sitting above 90% whose only high-severity finding was a single policy.
# A verdict that lands on almost everything carries no information, and its
# thresholds were doing more work than the evidence behind them justified.
#
# This tool reports; deciding what is acceptable is the reader's call, and the
# CI gate makes it explicitly with --fail-on <severity>. What is published now
# is the measurement -- the weighted pass rate plus counts by severity -- which
# is a fact about the repository rather than an opinion about it.


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


class Dissent(BaseModel):
    """What the samples that lost the vote actually said.

    Without this, a non-unanimous verdict can only report that disagreement
    happened -- the minority opinion was discarded with the losing samples, so
    "2 of 3 runs agreed" was the entire content. Keeping the dissenting verdict
    is what makes a near-miss reviewable: a check that passed 2-1 is worth a
    human's time only if you can read the argument for the other side.
    """

    status: FindingStatus
    samples: int
    evidence: str


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
    # Set only when the samples did not agree. See Dissent.
    dissent: Optional[Dissent] = None

    # There was a per-finding `risk_score = SEVERITY_WEIGHT * confidence` here.
    # It is gone: once confidence became a measured agreement rate it sat at 1.0
    # for 89% of findings, so risk_score equalled the severity weight in 66 of 69
    # violations and restated `severity` with occasional noise. Severity and
    # confidence are both on the finding already, and ComplianceReport.
    # compliance_score is the aggregate that actually normalises for repo size.

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
    # The self-consistency k this run used. Recorded because it changes what
    # confidence_score means: at k=1 no disagreement is measurable, so every
    # confidence is 1.0 and the remediation confidence gate never fires. Two
    # reports are only comparable if this matches.
    audit_samples: int = 1

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
        """Severity-weighted pass rate over applicable checks, plus severity counts.

        Replaces the previous practice of summing per-finding risk_score, which
        was unnormalised: a 345-check repository with 5 violations and a 66-check
        repository with 5 violations scored three points apart, so repo size
        moved the number as much as repo quality did.

        NOT_APPLICABLE is excluded from the denominator -- a check that was
        correctly skipped is not a check that passed. NEEDS_REVIEW is excluded
        from both sides and reported separately: an undecided verdict is not
        evidence either way, and burying it in the rate would let a repository
        score well by being unreadable.

        No pass/fail verdict is derived from any of this -- see the note at the
        top of the module.
        """
        earned = possible = 0
        high_failures = medium_failures = low_failures = 0
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
                else:
                    low_failures += 1
            elif finding.status == FindingStatus.NEEDS_REVIEW:
                undecided += 1

        return {
            "weighted_pass_rate": round(earned / possible, 4) if possible else None,
            "high_failures": high_failures,
            "medium_failures": medium_failures,
            "low_failures": low_failures,
            "undecided": undecided,
            "weight_earned": earned,
            "weight_possible": possible,
        }
