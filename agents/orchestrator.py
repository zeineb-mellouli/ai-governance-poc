"""Orchestrator: sequential handoff between the Repository, Auditor, and Remediation agents.

Each stage is wrapped so a failure is recorded on the report rather than
crashing the run (partial-failure handling).
"""

from pathlib import Path

from openai import OpenAI

from agents import auditor_agent, remediation_agent, repository_agent
from agents.html_report import render_batch_html
from agents.llm_client import get_client
from agents.schemas import ComplianceReport, Finding, FindingStatus, RemediationStatus

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_audit(
    repo_path: str,
    client: OpenAI | None = None,
    samples: int | None = None,
) -> ComplianceReport:
    """Run the full pipeline. `samples` is the self-consistency k (None = default)."""
    client = client or get_client()
    samples = auditor_agent._resolve_samples(samples)

    try:
        snapshot = repository_agent.scan(repo_path)
    except Exception as exc:  # noqa: BLE001 - nothing downstream can run without a snapshot
        return ComplianceReport(
            repo_name=Path(repo_path).name,
            repo_path=repo_path,
            audit_samples=samples,
            errors=[f"Repository Agent failed: {exc}"],
        )

    report = ComplianceReport(
        repo_name=snapshot.repo_root_name,
        repo_path=snapshot.repo_path,
        audit_samples=samples,
    )
    fingerprints: list[str] = []

    try:
        findings, audit_errors = auditor_agent.audit(
            snapshot, client=client, fingerprints=fingerprints, samples=samples
        )
        report.findings.extend(findings)
        report.errors.extend(audit_errors)
    except Exception as exc:  # noqa: BLE001 - e.g. ChromaDB unreachable
        report.errors.append(f"Auditor Agent failed: {exc}")
        report.model_fingerprints = sorted(set(fingerprints))
        return report

    try:
        file_content_by_path = {f.path: f.content for f in snapshot.files}
        remediation_errors = remediation_agent.remediate(
            report.findings, file_content_by_path, client=client, fingerprints=fingerprints
        )
        report.errors.extend(remediation_errors)
    except Exception as exc:  # noqa: BLE001
        report.errors.append(f"Remediation Agent failed: {exc}")

    report.model_fingerprints = sorted(set(fingerprints))
    return report


def load_reports(reports_dir: str | Path) -> list[ComplianceReport]:
    """Read every machine_report.json under a reports directory.

    Lets the HTML page be regenerated from a finished run without re-auditing --
    layout can be iterated on for free.
    """
    reports = []
    for path in sorted(Path(reports_dir).glob("*/machine_report.json")):
        reports.append(ComplianceReport.model_validate_json(path.read_text(encoding="utf-8")))
    return reports


def write_batch_html(reports: list[ComplianceReport], out_base_dir: str) -> Path:
    path = Path(out_base_dir) / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_batch_html(reports), encoding="utf-8")
    return path


def write_reports(report: ComplianceReport, out_base_dir: str) -> tuple[Path, Path]:
    out_dir = Path(out_base_dir) / report.repo_name
    out_dir.mkdir(parents=True, exist_ok=True)

    machine_path = out_dir / "machine_report.json"
    machine_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    draft_path = out_dir / "draft_report.md"
    draft_path.write_text(_render_draft_report(report), encoding="utf-8")

    return machine_path, draft_path


def _sort_key(finding: Finding) -> tuple:
    # Severity first, then most-agreed-on first: a unanimous violation is more
    # actionable than one two of three samples reached.
    return (SEVERITY_ORDER.get(finding.severity, 99), -finding.confidence_score)


_NO_FIX_LABEL = {
    RemediationStatus.NO_FIX_AVAILABLE: "No automated fix",
    RemediationStatus.UNSAFE_FIX_REJECTED: "Proposed fix rejected as unsafe",
    RemediationStatus.SKIPPED_LOW_CONFIDENCE: "Fix withheld",
    RemediationStatus.FAILED: "Fix generation failed",
}


def _render_finding(finding: Finding) -> list[str]:
    block = [
        f"### {finding.policy_id} · {finding.title} [{finding.severity}]",
        "",
        f"**Location:** {finding.file_path or '(repository-level)'}",
        f"**Sample agreement:** {finding.confidence_score:.0%}",
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
    elif finding.status == FindingStatus.NON_COMPLIANT:
        # Say why there is no fix, rather than silently omitting the section.
        # The violation stands either way -- only the automation stopped.
        label = _NO_FIX_LABEL.get(finding.remediation_status, "No fix attached")
        note = f": {finding.remediation_note}" if finding.remediation_note else "."
        block += ["", f"**{label}**{note}"]
    block.append("")
    return block


def _render_draft_report(report: ComplianceReport) -> str:
    summary = report.summary
    lines = [
        f"# Compliance Report — {report.repo_name}",
        "",
        f"Run at: {report.run_timestamp}",
        f"Repository path: {report.repo_path}",
    ]
    lines.append(f"Self-consistency samples (k): {report.audit_samples}")
    if report.audit_samples == 1:
        lines.append(
            "> At k=1 no disagreement is measurable, so every confidence is 1.0 "
            "and the remediation confidence gate does not fire."
        )
    if report.model_fingerprints:
        lines.append(f"Model backend fingerprint(s): {', '.join(report.model_fingerprints)}")
    lines += [
        "",
        "## Summary",
        "",
    ]

    score = report.compliance_score
    if score["weighted_pass_rate"] is not None:
        lines += [
            f"**Grade: {score['grade']}** — severity-weighted pass rate "
            f"{score['weighted_pass_rate']:.1%} "
            f"({score['weight_earned']}/{score['weight_possible']} weighted checks)",
            "",
        ]
        if score["gate"]:
            lines += [f"> {score['gate']}.", ""]
        if score["undecided"]:
            lines += [
                f"> {score['undecided']} verdict(s) were undecided and are excluded from the rate.",
                "",
            ]

    lines += [
        f"- Checks evaluated: {summary['checks_evaluated']}",
        f"- Applicable checks (compliant + non-compliant): {summary['applicable_checks']}",
    ]
    for status, count in sorted(summary["by_status"].items()):
        lines.append(f"- {status}: {count}")
    lines.append(f"- Requiring human action: {summary['needs_human_attention']}")
    if summary["non_compliant_by_remediation_status"]:
        lines.append("")
        lines.append("Remediation outcome for non-compliant findings:")
        for name, count in sorted(summary["non_compliant_by_remediation_status"].items()):
            lines.append(f"- {name}: {count}")
    lines.append("")

    if report.errors:
        lines += ["## Run errors (partial failures)", ""]
        lines += [f"- {err}" for err in report.errors]
        lines.append("")

    non_compliant = sorted((f for f in report.findings if f.status == FindingStatus.NON_COMPLIANT), key=_sort_key)
    needs_review = sorted((f for f in report.findings if f.status == FindingStatus.NEEDS_REVIEW), key=_sort_key)
    compliant = [f for f in report.findings if f.status == FindingStatus.COMPLIANT]
    not_applicable = [f for f in report.findings if f.status == FindingStatus.NOT_APPLICABLE]

    if non_compliant:
        lines += ["## Non-compliant findings", ""]
        for finding in non_compliant:
            lines += _render_finding(finding)

    if needs_review:
        # Undecided verdicts only. A violation that simply has no automated fix
        # is still a violation and stays in the section above, annotated.
        lines += [
            "## Needs human review (the audit could not settle these)",
            "",
        ]
        for finding in needs_review:
            lines += _render_finding(finding)

    lines += [
        "## Checks that passed or did not apply",
        "",
        f"{len(compliant)} checks passed; {len(not_applicable)} did not apply to this repository. "
        f"See machine_report.json for the full list.",
        "",
    ]

    return "\n".join(lines)
