"""Shared data contracts for the runtime AGA pipeline (Repository -> Auditor -> Remediation -> Orchestrator)."""

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
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


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
    retrieval_chunk_id: str
    retrieval_score: float
    remediation: Optional[Remediation] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def risk_score(self) -> float:
        return round(SEVERITY_WEIGHT.get(self.severity, 0) * self.confidence_score, 3)


class ComplianceReport(BaseModel):
    repo_name: str
    repo_path: str
    run_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    findings: list[Finding] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def summary(self) -> dict:
        by_status: dict[str, int] = {}
        non_compliant_by_severity: dict[str, int] = {}
        for f in self.findings:
            by_status[f.status.value] = by_status.get(f.status.value, 0) + 1
            if f.status == FindingStatus.NON_COMPLIANT:
                non_compliant_by_severity[f.severity] = non_compliant_by_severity.get(f.severity, 0) + 1
        return {
            "total_findings": len(self.findings),
            "by_status": by_status,
            "non_compliant_by_severity": non_compliant_by_severity,
        }
