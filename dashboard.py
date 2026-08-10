"""Interactive governance dashboard.

    streamlit run dashboard.py -- --reports reports_v3 [--repo FinalProject]

Launched for you by `python main.py audit --repo <path> --open`, or on its own
via `python main.py dashboard`.

It reads finished machine_report.json files and never calls the API, so
filtering, searching and re-styling cost nothing and a report can be explored
long after the run that produced it. Auditing is the CLI's job; this only reads.

The layout answers three questions in order, which is also the order a sceptical
reader asks them: how bad is it, what exactly is wrong, and how much of this
should I believe.
"""

import argparse
import sys
from pathlib import Path

import streamlit as st

from agents.orchestrator import load_reports
from agents.schemas import ComplianceReport, FindingStatus

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
GRADE_ORDER = {"FAIL": 0, "NEEDS_WORK": 1, "PASS": 2, "NOT_SCORED": 3}
GRADE_COLOR = {"PASS": "#1f6f4a", "NEEDS_WORK": "#8a5a00", "FAIL": "#b3261e", "NOT_SCORED": "#6b7684"}
SEVERITY_COLOR = {"HIGH": "#b3261e", "MEDIUM": "#8a5a00", "LOW": "#4a5568"}

ALL_REPOS = "All repositories"


def _args() -> argparse.Namespace:
    """Streamlit hands everything after `--` through in sys.argv."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", default="reports")
    parser.add_argument("--repo", default=None)
    known, _ = parser.parse_known_args(sys.argv[1:])
    return known


def _split_evidence(evidence: str) -> tuple[str, str | None]:
    """Pull the quoted source line back out of the packed evidence string."""
    import ast
    import re

    evidence = re.sub(r"\s{2}\[[^\]]*\]\s*$", "", evidence)
    match = re.search(r"\s{2}Quoted:\s(.+)$", evidence, re.DOTALL)
    if not match:
        return evidence.strip(), None
    raw = match.group(1).strip()
    try:
        quote = ast.literal_eval(raw)
    except (ValueError, SyntaxError):
        quote = raw
    return evidence[: match.start()].strip(), quote


def _chip(text: str, color: str) -> str:
    return (
        f'<span style="background:{color}1a;color:{color};padding:2px 9px;border-radius:3px;'
        f'font-size:.72rem;font-weight:700;letter-spacing:.06em;white-space:nowrap">{text}</span>'
    )


# --- views -------------------------------------------------------------------


def render_overview(reports: list[ComplianceReport]) -> None:
    st.subheader("All repositories")

    total_violations = sum(r.summary["by_status"].get("NON_COMPLIANT", 0) for r in reports)
    high = sum(r.compliance_score["high_failures"] for r in reports)
    passing = sum(1 for r in reports if r.compliance_score["grade"] == "PASS")
    action = sum(r.summary["needs_human_attention"] for r in reports)

    cols = st.columns(5)
    cols[0].metric("Repositories", len(reports))
    cols[1].metric("Violations", total_violations)
    cols[2].metric("High severity", high)
    cols[3].metric("Passing", f"{passing}/{len(reports)}")
    cols[4].metric("Need a person", action)

    rows = []
    for report in sorted(
        reports,
        key=lambda r: (GRADE_ORDER.get(r.compliance_score["grade"], 9),
                       r.compliance_score["weighted_pass_rate"] or 0.0),
    ):
        score, counts = report.compliance_score, report.summary["by_status"]
        rows.append({
            "Repository": report.repo_name,
            "Grade": score["grade"],
            "Pass rate": score["weighted_pass_rate"] or 0.0,
            "Violations": counts.get("NON_COMPLIANT", 0),
            "Passed": counts.get("COMPLIANT", 0),
            "N/A": counts.get("NOT_APPLICABLE", 0),
            "To action": report.summary["needs_human_attention"],
        })

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        column_config={
            # A bar, not a bare number: 41% and 90% both grade FAIL, and the
            # grade alone makes a wreck and a single hardcoded secret look alike.
            "Pass rate": st.column_config.ProgressColumn(
                "Weighted pass rate", format="%.1f%%", min_value=0.0, max_value=1.0,
            ),
        },
    )
    st.caption(
        "Not-applicable checks are excluded from the pass rate — a check correctly "
        "skipped is not a check passed. Undecided verdicts are excluded from both "
        "sides and listed per repository."
    )


def render_finding(finding, show_agreement: bool = True) -> None:
    sentence, quote = _split_evidence(finding.evidence)
    location = finding.file_path or "repository-level"
    header = f"{finding.severity} · {finding.policy_id} · {location}"

    with st.expander(header, expanded=False):
        st.markdown(
            _chip(finding.severity, SEVERITY_COLOR.get(finding.severity, "#6b7684"))
            + f"&nbsp;&nbsp;**{finding.title}**",
            unsafe_allow_html=True,
        )
        if sentence:
            st.write(sentence)

        if quote:
            st.caption("Evidence — copied verbatim from the file")
            st.code(quote, language=None)

        if finding.remediation:
            # A NAM-5 rename is computed from the filename by a total function and
            # re-checked before it is offered. Everything else was written by the
            # model and nothing verified it. Labelling them the same would imply
            # confidence the second kind has not earned.
            computed = finding.policy_id == "NAM-5" and finding.confidence_score == 1.0
            st.caption("Computed fix — derived and re-checked" if computed
                       else "Suggested fix — model-written, review before applying")
            st.write(finding.remediation.description)
            st.code(finding.remediation.fix, language="bash")
        elif finding.status == FindingStatus.NON_COMPLIANT:
            st.caption(f"No fix attached — {finding.remediation_status.value}")
            if finding.remediation_note:
                st.write(finding.remediation_note)

        if show_agreement and finding.confidence_score < 1.0:
            st.warning(f"Samples agreed {finding.confidence_score:.0%} of the time.")

        if finding.reasoning:
            with st.popover("Model reasoning"):
                st.write(finding.reasoning)


def render_repo(report: ComplianceReport) -> None:
    score, summary = report.compliance_score, report.summary
    grade = score["grade"]

    st.markdown(
        f"## {report.repo_name} &nbsp; {_chip(grade.replace('_', ' '), GRADE_COLOR.get(grade, '#6b7684'))}",
        unsafe_allow_html=True,
    )
    if score["weighted_pass_rate"] is not None:
        st.progress(score["weighted_pass_rate"],
                    text=f"Weighted pass rate {score['weighted_pass_rate']:.1%} "
                         f"({score['weight_earned']}/{score['weight_possible']})")
    if score["gate"]:
        st.error(score["gate"])

    cols = st.columns(4)
    cols[0].metric("Violations", summary["by_status"].get("NON_COMPLIANT", 0))
    cols[1].metric("Passed", summary["by_status"].get("COMPLIANT", 0))
    cols[2].metric("Not applicable", summary["by_status"].get("NOT_APPLICABLE", 0))
    cols[3].metric("Need a person", summary["needs_human_attention"])

    violations = sorted(
        (f for f in report.findings if f.status == FindingStatus.NON_COMPLIANT),
        key=lambda f: (SEVERITY_ORDER.get(f.severity, 9), -f.confidence_score, f.policy_id),
    )
    undecided = [f for f in report.findings if f.status == FindingStatus.NEEDS_REVIEW]
    near_misses = [
        f for f in report.findings
        if f.status == FindingStatus.COMPLIANT and f.confidence_score < 1.0
    ]

    # --- filters, in the sidebar so they apply to whatever is on screen
    st.sidebar.markdown("### Filter violations")
    severities = st.sidebar.multiselect(
        "Severity", ["HIGH", "MEDIUM", "LOW"], default=["HIGH", "MEDIUM", "LOW"],
    )
    policies = sorted({f.policy_id for f in violations})
    chosen = st.sidebar.multiselect("Policy", policies, default=policies)
    needle = st.sidebar.text_input("Search evidence and file paths", "")

    shown = [
        f for f in violations
        if f.severity in severities and f.policy_id in chosen
        and (not needle
             or needle.lower() in f.evidence.lower()
             or needle.lower() in (f.file_path or "").lower())
    ]

    tab_v, tab_u, tab_all, tab_run = st.tabs([
        f"Violations ({len(shown)})",
        f"Not certain ({len(undecided) + len(near_misses)})",
        f"Every check ({len(report.findings)})",
        "Run",
    ])

    with tab_v:
        if not violations:
            st.success("No violations. Every applicable check passed.")
        elif not shown:
            st.info("No violations match the current filters.")
        else:
            current = None
            for finding in shown:
                if finding.severity != current:
                    current = finding.severity
                    count = sum(1 for f in shown if f.severity == current)
                    st.markdown(f"**{current}** &nbsp;·&nbsp; {count}")
                render_finding(finding)

    with tab_u:
        st.caption(
            f"Each check runs {report.audit_samples} times and the verdict is the "
            "majority. Confidence is the share of runs that agreed — it measures "
            "self-consistency, not correctness."
        )
        if undecided:
            st.markdown(f"**Could not be settled** — {len(undecided)}")
            for finding in undecided:
                render_finding(finding)
        if near_misses:
            st.markdown(f"**Passed, but not unanimously** — {len(near_misses)}")
            st.caption("A check most runs called clean and at least one called a violation.")
            for finding in near_misses:
                render_finding(finding)
        if not undecided and not near_misses:
            st.success("Every check was unanimous across all samples.")

    with tab_all:
        st.dataframe(
            [{
                "Policy": f.policy_id,
                "Severity": f.severity,
                "Status": f.status.value,
                "File": f.file_path or "(repository-level)",
                "Agreement": f.confidence_score,
                "Evidence": _split_evidence(f.evidence)[0][:160],
            } for f in report.findings],
            use_container_width=True, hide_index=True,
            column_config={"Agreement": st.column_config.NumberColumn(format="%.0f%%")},
        )

    with tab_run:
        st.write(f"**Repository path** `{report.repo_path}`")
        st.write(f"**Run at** {report.run_timestamp}")
        st.write(f"**Samples per check (k)** {report.audit_samples}")
        if report.audit_samples == 1:
            st.warning(
                "At k=1 no disagreement is measurable, so every confidence is 100% "
                "and the remediation confidence gate never fires."
            )
        if report.model_fingerprints:
            st.write("**Serving backend** " + ", ".join(report.model_fingerprints))
        if report.errors:
            st.error(f"{len(report.errors)} partial failure(s) during the run")
            for err in report.errors:
                st.write(f"- {err}")
        else:
            st.success("The run completed with no errors.")


# --- app ---------------------------------------------------------------------


def main() -> None:
    st.set_page_config(page_title="Governance audit", page_icon="🛡️", layout="wide")
    args = _args()

    st.sidebar.title("Governance audit")
    reports_dir = st.sidebar.text_input("Reports directory", args.reports)

    reports = load_reports(reports_dir)
    if not reports:
        st.warning(f"No `machine_report.json` found under `{reports_dir}`.")
        st.write("Run an audit first:")
        st.code(f"python main.py batch --root sample_repos --out {reports_dir} -k 3", language="bash")
        return

    names = [r.repo_name for r in reports]
    default = args.repo if args.repo in names else ALL_REPOS
    choice = st.sidebar.selectbox(
        "Repository", [ALL_REPOS, *names], index=([ALL_REPOS, *names]).index(default),
    )
    st.sidebar.caption(f"{len(reports)} report(s) loaded")

    if choice == ALL_REPOS:
        render_overview(reports)
    else:
        render_repo(next(r for r in reports if r.repo_name == choice))


if __name__ == "__main__":
    main()
