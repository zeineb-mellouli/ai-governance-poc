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
from dotenv import load_dotenv

load_dotenv()  # the audit needs the Azure credentials in this process too

from agents.orchestrator import load_reports, run_audit, write_reports  # noqa: E402
from agents.schemas import ComplianceReport, FindingStatus  # noqa: E402

SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
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

    cols = st.columns(3)
    cols[0].metric("Repositories", len(reports))
    cols[1].metric("Violations", total_violations)
    cols[2].metric("High severity", high)

    rows = []
    # Worst first: most high-severity violations, then lowest pass rate.
    for report in sorted(
        reports,
        key=lambda r: (-r.compliance_score["high_failures"],
                       r.compliance_score["weighted_pass_rate"] or 0.0),
    ):
        score, counts = report.compliance_score, report.summary["by_status"]
        rows.append({
            "Repository": report.repo_name,
            "High": score["high_failures"],
            # Stored 0-100, not 0-1: ProgressColumn applies `format` to the raw
            # value, so a 0-1 fraction renders 0.397 as "0.4%" instead of "39.7%".
            "Pass rate": (score["weighted_pass_rate"] or 0.0) * 100,
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
            # A bar, not a bare number: it is the only cross-repo comparison on
            # the page now that there is no grade to sort by.
            "Pass rate": st.column_config.ProgressColumn(
                "Weighted pass rate", format="%.1f%%", min_value=0.0, max_value=100.0,
            ),
        },
    )
    with st.expander("What the weighted pass rate means"):
        st.markdown(
            "Of the checks that **applied** to a repository, the share of "
            "severity-weighted checks it passed:\n\n"
            "```\nrate = weight of passing checks / weight of (passing + failing) checks\n"
            "HIGH = 3   MEDIUM = 2   LOW = 1\n```\n"
            "Weighting means one failed HIGH costs as much as three failed LOWs, so "
            "a pile of naming violations cannot outweigh a hardcoded credential.\n\n"
            "**Not-applicable checks are excluded** — a check correctly skipped is not "
            "a check passed, and counting them would let a repository score well by "
            "having little the policies cover. **Undecided verdicts are excluded from "
            "both sides** and listed per repository; they are not evidence either way.\n\n"
            "There is deliberately no pass/fail grade. The rate is a measurement; "
            "whether a repository is acceptable depends on which policies matter to "
            "you, and the CI gate decides that explicitly with `--fail-on <severity>`. "
            "Read the rate together with the high-severity count — a repository at 95% "
            "with one hardcoded credential is not the same as one at 95% with a "
            "naming violation."
        )


def render_finding(finding, show_agreement: bool = True, header: str | None = None) -> None:
    sentence, quote = _split_evidence(finding.evidence)
    location = finding.file_path or "repository-level"
    header = header or f"{finding.severity} · {finding.policy_id} · {location}"

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

        if show_agreement and finding.dissent:
            # The minority verdict, kept verbatim. Reporting only that the runs
            # disagreed gave a reader nothing to weigh; the argument for the
            # other side is the whole reason to look at a near miss.
            d = finding.dissent
            other_sentence, other_quote = _split_evidence(d.evidence)
            st.caption(f"Dissenting verdict — {d.samples} run(s) said {d.status.value}")
            st.info(other_sentence or "(no evidence given)")
            if other_quote:
                st.code(other_quote, language=None)
        elif show_agreement and finding.confidence_score < 1.0:
            st.warning(f"Samples agreed {finding.confidence_score:.0%} of the time.")

        if finding.reasoning:
            with st.popover("Model reasoning"):
                st.write(finding.reasoning)


def render_repo(report: ComplianceReport) -> None:
    score, summary = report.compliance_score, report.summary

    chips = "".join(
        _chip(f"{n} {name}", SEVERITY_COLOR[name.upper()])
        for n, name in ((score["high_failures"], "HIGH"),
                        (score["medium_failures"], "MEDIUM"),
                        (score["low_failures"], "LOW")) if n
    ) or _chip("no violations", "#1f6f4a")
    st.markdown(f"## {report.repo_name} &nbsp; {chips}", unsafe_allow_html=True)
    if score["weighted_pass_rate"] is not None:
        st.progress(score["weighted_pass_rate"],
                    text=f"Weighted pass rate {score['weighted_pass_rate']:.1%} "
                         f"({score['weight_earned']}/{score['weight_possible']})")

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
    # Streamlit renders its colour markdown in widget labels, so the severity
    # scale reads red -> amber -> grey without injecting CSS at its internals.
    severities = [
        level for level, colour in (("HIGH", "red"), ("MEDIUM", "orange"), ("LOW", "gray"))
        if st.sidebar.checkbox(
            f":{colour}[**{level}**] &nbsp;·&nbsp; {sum(1 for f in violations if f.severity == level)}",
            value=True, key=f"sev_{level}",
        )
    ]
    policies = sorted({f.policy_id for f in violations})
    chosen = st.sidebar.multiselect("Policy", policies, default=policies)

    shown = [
        f for f in violations
        if f.severity in severities and f.policy_id in chosen
    ]

    tab_v, tab_u, tab_run = st.tabs([
        f"Violations ({len(shown)})",
        f"Not certain ({len(undecided) + len(near_misses)})",
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
            "majority. These are the checks the runs did not agree on — the "
            "dissenting verdict is shown so you can weigh it yourself. Agreement "
            "measures self-consistency, not correctness."
        )

        def _unsure_header(f) -> str:
            k = report.audit_samples
            agreed = round(f.confidence_score * k)
            verdict = "clean" if f.status == FindingStatus.COMPLIANT else f.status.value
            other = f" · {f.dissent.samples} said {f.dissent.status.value}" if f.dissent else ""
            where = f.file_path or "repository-level"
            return f"{agreed}/{k} runs said {verdict}{other}  —  {f.policy_id} · {where}"

        if undecided:
            st.markdown(f"**Could not be settled** — {len(undecided)}")
            st.caption("No verdict won a majority, so the check is unresolved.")
            for finding in undecided:
                render_finding(finding, header=_unsure_header(finding))
        if near_misses:
            st.markdown(f"**Passed, but not unanimously** — {len(near_misses)}")
            st.caption(
                "Most runs called these clean and at least one called a violation. "
                "They are the likeliest place a real violation was missed."
            )
            for finding in near_misses:
                render_finding(finding, header=_unsure_header(finding))
        if not undecided and not near_misses:
            st.success("Every check was unanimous across all runs.")

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


def _audit_panel(reports_dir: str) -> None:
    """Run a new audit from the UI, so a demo is not limited to what is on disk."""
    with st.sidebar.expander("Audit a repository", expanded=False):
        repo_path = st.text_input("Repository path", "", placeholder="/path/to/repo",
                                  key="audit_repo_path")
        samples = st.number_input(
            "Samples per check (k)", min_value=1, max_value=5, value=3, step=1,
            help="Each check runs k times and the verdict is the majority. "
                 "k=1 is fastest but measures no disagreement, so every confidence "
                 "reads 100%. Capped at 5: cost is linear in k and agreement past "
                 "5 runs tells you nothing 3 did not.",
        )
        if st.button("Run audit", type="primary", use_container_width=True):
            if not repo_path or not Path(repo_path).is_dir():
                st.error("That path is not a directory.")
                return
            bar = st.progress(0.0, text="Reading the repository…")

            def on_progress(done: int, total: int, label: str) -> None:
                bar.progress(min(done / total, 1.0), text=f"{done}/{total} · {label}")

            try:
                report = run_audit(repo_path, samples=samples, progress=on_progress)
                write_reports(report, reports_dir)
            except Exception as exc:  # noqa: BLE001 - surface it rather than a stack trace
                bar.empty()
                st.error(f"The audit could not run: {exc}")
                return
            bar.empty()
            violations = report.summary["by_status"].get("NON_COMPLIANT", 0)
            st.success(f"{report.repo_name}: {violations} violation(s)")
            # Land on the repository that was just audited.
            st.session_state["selected_repo"] = report.repo_name
            st.rerun()


# --- app ---------------------------------------------------------------------


def main() -> None:
    st.set_page_config(page_title="Governance audit", page_icon="🛡️", layout="wide")
    args = _args()

    st.sidebar.title("Governance audit")
    reports_dir = st.sidebar.text_input("Reports directory", args.reports)

    _audit_panel(reports_dir)

    reports = load_reports(reports_dir)
    if not reports:
        st.warning(f"No `machine_report.json` found under `{reports_dir}`.")
        st.write("Run an audit first:")
        st.code(f"python main.py batch --root sample_repos --out {reports_dir} -k 3", language="bash")
        return

    names = [r.repo_name for r in reports]
    wanted = st.session_state.pop("selected_repo", None) or args.repo
    default = wanted if wanted in names else ALL_REPOS
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
