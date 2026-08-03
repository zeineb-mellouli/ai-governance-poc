"""Orchestrator: sequential handoff between the Repository, Auditor, and Remediation agents.

Each stage is wrapped so a failure is recorded on the report rather than
crashing the run (partial-failure handling).
"""

from pathlib import Path

from openai import OpenAI

from agents import auditor_agent, remediation_agent, repository_agent
from agents.llm_client import get_client
from agents.schemas import ComplianceReport, Finding, FindingStatus

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_audit(repo_path: str, client: OpenAI | None = None) -> ComplianceReport:
    client = client or get_client()

    try:
        snapshot = repository_agent.scan(repo_path)
    except Exception as exc:  # noqa: BLE001 - nothing downstream can run without a snapshot
        return ComplianceReport(
            repo_name=Path(repo_path).name,
            repo_path=repo_path,
            errors=[f"Repository Agent failed: {exc}"],
        )

    report = ComplianceReport(repo_name=snapshot.repo_root_name, repo_path=snapshot.repo_path)

    try:
        findings, audit_errors = auditor_agent.audit(snapshot, client=client)
        report.findings.extend(findings)
        report.errors.extend(audit_errors)
    except Exception as exc:  # noqa: BLE001 - e.g. ChromaDB unreachable
        report.errors.append(f"Auditor Agent failed: {exc}")
        return report

    try:
        file_content_by_path = {f.path: f.content for f in snapshot.files}
        remediation_errors = remediation_agent.remediate(report.findings, file_content_by_path, client=client)
        report.errors.extend(remediation_errors)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"Remediation Agent failed: {exc}")

    return report


def write_reports(report: ComplianceReport, out_base_dir: str) -> tuple[Path, Path]:
    out_dir = Path(out_base_dir) / report.repo_name
    out_dir.mkdir(parents=True, exist_ok=True)

    machine_path = out_dir / "machine_report.json"
    machine_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    draft_path = out_dir / "draft_report.md"
    draft_path.write_text(_render_draft_report(report), encoding="utf-8")

    return machine_path, draft_path


def _sort_key(finding: Finding) -> tuple:
    return (SEVERITY_ORDER.get(finding.severity, 99), -finding.risk_score)


def _render_finding(finding: Finding) -> list[str]:
    block = [
        f"### {finding.policy_id} · {finding.title} [{finding.severity}]",
        "",
        f"**Location:** {finding.file_path or '(repository-level)'}",
        f"**Confidence:** {finding.confidence_score:.2f}  |  **Risk score:** {finding.risk_score}",
        f"**Evidence:** {finding.evidence}",
    ]
    if finding.remediation:
        block += [
            "",
            f"**Suggested fix:** {finding.remediation.description}",
            "",
            "```",
            finding.remediation.fix,
            "```",
        ]
    block.append("")
    return block


def _render_draft_report(report: ComplianceReport) -> str:
    summary = report.summary
    lines = [
        f"# Compliance Report — {report.repo_name}",
        "",
        f"Run at: {report.run_timestamp}",
        f"Repository path: {report.repo_path}",
        "",
        "## Summary",
        "",
        f"- Total findings evaluated: {summary['total_findings']}",
    ]
    for status, count in summary["by_status"].items():
        lines.append(f"- {status}: {count}")
    lines.append("")

    if report.errors:
        lines += ["## Run errors (partial failures)", ""]
        lines += [f"- {err}" for err in report.errors]
        lines.append("")

    non_compliant = sorted((f for f in report.findings if f.status == FindingStatus.NON_COMPLIANT), key=_sort_key)
    needs_review = sorted((f for f in report.findings if f.status == FindingStatus.NEEDS_REVIEW), key=_sort_key)
    compliant = [f for f in report.findings if f.status == FindingStatus.COMPLIANT]

    if non_compliant:
        lines += ["## Non-compliant findings", ""]
        for finding in non_compliant:
            lines += _render_finding(finding)

    if needs_review:
        lines += ["## Needs human review (low-confidence findings)", ""]
        for finding in needs_review:
            lines += _render_finding(finding)

    lines += [
        "## Compliant checks",
        "",
        f"{len(compliant)} checks passed. See machine_report.json for the full list.",
        "",
    ]

    return "\n".join(lines)
