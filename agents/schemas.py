"""Shared data contracts for pipeline.

Repository -> Auditor -> Remediation -> Orchestrator.

These models publish measurements: a weighted pass rate and counts by severity. 
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, computed_field

SEVERITY_WEIGHT = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}


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
    generated says nothing about whether the violation is real. Remediation
    outcome lives on its own axis, in RemediationStatus.
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


class RepositorySnapshot(BaseModel):
    repo_root_name: str
    repo_path: str
    has_readme: bool
    files: list[FileRecord]


class Remediation(BaseModel):
    description: str
    fix: str


class Dissent(BaseModel):
    """What the samples that lost the vote argued.

    A check that passed 2-1 is worth a human's time only if the losing argument
    is readable.
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
    reasoning: str = ""
    retrieval_chunk_id: str
    retrieval_score: float
    remediation: Optional[Remediation] = None
    remediation_status: RemediationStatus = RemediationStatus.NOT_REQUIRED
    remediation_note: Optional[str] = None
    # Set only when the samples did not agree. See Dissent.
    dissent: Optional[Dissent] = None

    @property
    def has_computed_fix(self) -> bool:
        """True when the fix was derived in code and re-checked, not written by the
        model. Plain property, not computed_field, so it stays out of the report JSON."""
        return self.policy_id == "NAM-5" and self.confidence_score == 1.0

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
    model_fingerprints: list[str] = Field(default_factory=list)
    audit_samples: int = 1

    @computed_field  
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

    @computed_field  
    @property
    def compliance_score(self) -> dict:
        """Severity-weighted pass rate over applicable checks, plus severity counts.

        NOT_APPLICABLE is excluded from the denominator: a check correctly skipped
        is not a check passed. NEEDS_REVIEW is excluded from both sides and
        reported separately, since an undecided verdict is evidence for neither

        Weighting normalises for repository size.
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
