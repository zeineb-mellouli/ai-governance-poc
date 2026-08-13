"""CLI entrypoint for the runtime audit pipeline (Git-only path)."""

import subprocess
import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Before the agents imports, not after: auditor_agent reads AGA_AUDIT_SAMPLES at
# import time and freezes it, so loading .env later would silently ignore it.
load_dotenv()

from agents.auditor_agent import _resolve_samples as resolve_samples
from agents.orchestrator import (  
    load_reports,
    run_audit,
    write_batch_html,
    write_reports,
)

app = typer.Typer()
console = Console()


SAMPLES_HELP = (
    "Self-consistency samples per prompt (k). Each prompt is asked k times and the "
    "verdict is the majority; confidence is the fraction that agreed. k=1 is cheapest "
    "but measures no disagreement, so every confidence is 1.0. Default: 3."
)


@app.command()
def audit(
    repo: str = typer.Option(..., "--repo", help="Path to the local repository to audit"),
    out: str = typer.Option("reports", "--out", help="Base directory for machine_report.json / draft_report.md"),
    samples: int = typer.Option(None, "--samples", "-k", min=1, help=SAMPLES_HELP),
    open_dashboard: bool = typer.Option(False, "--open",
                                        help="Open the interactive dashboard on this repository afterwards."),
) -> None:
    """Run Repository -> Auditor -> Remediation against a local repo and write a compliance report."""
    report = run_audit(repo, samples=samples)
    machine_path, draft_path = write_reports(report, out)

    console.print(f"[bold]Audit complete[/bold] for {report.repo_name}")
    console.print(report.summary)
    if report.errors:
        console.print(f"[yellow]{len(report.errors)} error(s) during the run — see {draft_path}[/yellow]")
    console.print(f"Machine report: {machine_path}")
    console.print(f"Draft report:   {draft_path}")

    if open_dashboard:
        _launch_dashboard(out, report.repo_name)


@app.command()
def batch(
    root: str = typer.Option("sample_repos", "--root", help="Root folder containing category subfolders and repos"),
    out: str = typer.Option("reports", "--out", help="Base directory for all reports"),
    category: str = typer.Option("", "--category", help="Only run repos under this category subfolder (e.g. compliant)"),
    samples: int = typer.Option(None, "--samples", "-k", min=1, help=SAMPLES_HELP),
) -> None:
    """Audit every repository found under --root and print a summary table.

    Expects the structure: <root>/<category>/<repo-name>/
    Skips any leaf directory that contains no recognised source files.
    """
    root_path = Path(root)
    if not root_path.is_dir():
        console.print(f"[red]Root path not found: {root_path}[/red]")
        raise typer.Exit(1)

    # Collect all repo paths: two levels deep (category/repo)
    repo_paths: list[tuple[str, Path]] = []
    for category_dir in sorted(root_path.iterdir()):
        if not category_dir.is_dir():
            continue
        if category and category_dir.name != category:
            continue
        for repo_dir in sorted(category_dir.iterdir()):
            if repo_dir.is_dir():
                repo_paths.append((category_dir.name, repo_dir))

    if not repo_paths:
        console.print(f"[yellow]No repos found under {root_path}[/yellow]")
        raise typer.Exit(0)

    effective_k = resolve_samples(samples)
    console.print(f"\n[bold]Batch audit — {len(repo_paths)} repos, k={effective_k}[/bold]\n")

    results = []
    failed = 0
    for cat, repo_dir in repo_paths:
        console.print(f"  Auditing [cyan]{cat}/{repo_dir.name}[/cyan] ...")
        try:
            report = run_audit(str(repo_dir), samples=samples)
            write_reports(report, out)
            s = report.summary
            sc = report.compliance_score
            results.append({
                "category": cat,
                "repo": report.repo_name,
                "rate": "—" if sc["weighted_pass_rate"] is None else f"{sc['weighted_pass_rate']:.1%}",
                "non_compliant": s["by_status"].get("NON_COMPLIANT", 0),
                "needs_review": s["by_status"].get("NEEDS_REVIEW", 0),
                "human_action": s["needs_human_attention"],
                "errors": len(report.errors),
            })
        except Exception as exc:  # one crashed repo must not stop the batch
            console.print(f"    [red]FAILED: {exc}[/red]")
            results.append({"category": cat, "repo": repo_dir.name, "rate": "—",
                             "non_compliant": "—", "needs_review": "—",
                             "human_action": "—", "errors": "CRASH"})
            failed += 1

    table = Table(title="\nBatch Audit Summary", show_lines=True)
    table.add_column("Category", style="dim")
    table.add_column("Repo")
    table.add_column("Rate", justify="right")
    table.add_column("Violations", justify="right", style="red")
    table.add_column("Undecided", justify="right", style="yellow")
    # Non-compliant findings with no usable auto-fix, plus undecided verdicts.
    # The queue a person actually has to work through , distinct from
    # "Undecided", which is only the verdicts the audit could not settle.
    table.add_column("To action", justify="right", style="yellow")
    table.add_column("Errors", justify="right")

    for r in results:
        err_str = str(r["errors"])
        table.add_row(
            r["category"], r["repo"], str(r["rate"]),
            str(r["non_compliant"]), str(r["needs_review"]), str(r["human_action"]),
            f"[red]{err_str}[/red]" if r["errors"] else err_str,
        )

    console.print(table)
    console.print(f"\nReports written to: [bold]{Path(out).resolve()}[/bold]")
    written = load_reports(out)
    if written:
        console.print(f"Dashboard:          [bold]{write_batch_html(written, out)}[/bold]")
    if failed:
        console.print(f"[red]{failed} repo(s) crashed during audit.[/red]")
        raise typer.Exit(1)


DASHBOARD_SCRIPT = Path(__file__).parent / "dashboard.py"


def _launch_dashboard(reports_dir: str, repo: str | None = None) -> None:
    """Hand the terminal over to Streamlit. Blocks until Ctrl+C, as a server should."""
    command = [sys.executable, "-m", "streamlit", "run", str(DASHBOARD_SCRIPT),
               "--", "--reports", reports_dir]
    if repo:
        command += ["--repo", repo]
    console.print(f"\n[bold]Opening dashboard[/bold] — Ctrl+C to stop\n[dim]{' '.join(command)}[/dim]\n")
    try:
        subprocess.run(command, check=False)
    except FileNotFoundError:
        console.print("[red]Streamlit is not installed.[/red]  pip install -r requirements.txt")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Dashboard stopped.[/dim]")


@app.command()
def dashboard(
    reports: str = typer.Option("reports", "--reports", help="Directory holding <repo>/machine_report.json"),
    repo: str = typer.Option(None, "--repo", help="Open this repository first"),
) -> None:
    """Open the interactive dashboard for an existing run.

    Viewing costs nothing, but the sidebar can start a new audit, which does
    call the API — so this needs the Azure credentials in the environment.
    """
    if not load_reports(reports):
        console.print(f"[red]No machine_report.json found under {reports}[/red]")
        raise typer.Exit(1)
    _launch_dashboard(reports, repo)


@app.command()
def html(
    reports: str = typer.Option("reports", "--reports", help="Directory holding <repo>/machine_report.json"),
    out: str = typer.Option("", "--out", help="Where to write index.html (defaults to --reports)"),
    title: str = typer.Option("Governance audit", "--title", help="Page heading"),
) -> None:
    """Render one self-contained HTML dashboard from an existing run. No API calls."""
    loaded = load_reports(reports)
    if not loaded:
        console.print(f"[red]No machine_report.json found under {reports}[/red]")
        raise typer.Exit(1)

    from agents.html_report import render_batch_html

    destination = Path(out or reports) / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render_batch_html(loaded, title=title), encoding="utf-8")
    size_kb = destination.stat().st_size / 1024
    console.print(f"[green]{len(loaded)} repositories[/green] → [bold]{destination}[/bold] ({size_kb:.0f} KB)")


def _fmt(value: float | None) -> str:
    return "—" if value is None else f"{value:.2f}"


@app.command("eval")
def evaluate(
    reports: str = typer.Option("reports", "--reports", help="Directory holding <repo>/machine_report.json"),
    baseline: str = typer.Option("", "--baseline", help="Second reports directory to compare against"),
    details: bool = typer.Option(True, "--details/--no-details", help="List the individual FN / FP / unlabelled findings"),
) -> None:
    """Score existing reports against evaluation/expected/*.yaml. Makes no API calls."""
    from evaluation.score import aggregate, missing_reports, score_all  # keeps CLI startup light

    reports_dir = Path(reports)
    if not reports_dir.is_dir():
        console.print(f"[red]Reports directory not found: {reports_dir}[/red]")
        raise typer.Exit(1)

    results = score_all(reports_dir)
    if not results:
        console.print(f"[yellow]No scorable reports in {reports_dir}. Run an audit first.[/yellow]")
        raise typer.Exit(1)

    absent = missing_reports(reports_dir)
    if absent:
        console.print(f"[yellow]No report for: {', '.join(absent)} — excluded from scoring.[/yellow]\n")

    totals = aggregate(results)
    base_totals = aggregate(score_all(Path(baseline))) if baseline else {}

    table = Table(title="Audit accuracy vs. ground truth", show_lines=False)
    table.add_column("Policy")
    table.add_column("TP", justify="right", style="green")
    table.add_column("FP", justify="right", style="red")
    table.add_column("FN", justify="right", style="red")
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("F1", justify="right")
    table.add_column("Review", justify="right", style="yellow")
    table.add_column("Unlabelled", justify="right", style="dim")
    table.add_column("Tolerated", justify="right", style="dim")
    if baseline:
        table.add_column("Δ F1", justify="right")

    def _row(label: str, s, base) -> list[str]:
        cells = [
            label, str(s.tp), str(s.fp), str(s.fn),
            _fmt(s.precision), _fmt(s.recall), _fmt(s.f1),
            str(s.needs_review), str(s.unlabelled), str(s.tolerated),
        ]
        if baseline:
            if base is None or base.f1 is None or s.f1 is None:
                cells.append("—")
            else:
                delta = s.f1 - base.f1
                sign = "+" if delta >= 0 else ""
                cells.append(f"[green]{sign}{delta:.2f}[/green]" if delta >= 0 else f"[red]{delta:.2f}[/red]")
        return cells

    for policy in sorted(totals):
        table.add_row(*_row(policy, totals[policy], base_totals.get(policy)))

    overall = type(next(iter(totals.values())))()
    for s in totals.values():
        overall.tp += s.tp
        overall.fp += s.fp
        overall.fn += s.fn
        overall.needs_review += s.needs_review
        overall.unlabelled += s.unlabelled
        overall.tolerated += s.tolerated
    base_overall = None
    if base_totals:
        base_overall = type(next(iter(base_totals.values())))()
        for s in base_totals.values():
            base_overall.tp += s.tp
            base_overall.fp += s.fp
            base_overall.fn += s.fn
    table.add_section()
    table.add_row(*_row("[bold]OVERALL[/bold]", overall, base_overall))

    console.print()
    console.print(table)

    if details:
        for result in results:
            if not (result.false_negatives or result.false_positives or result.unlabelled):
                continue
            console.print(f"\n[bold]{result.repo}[/bold]")
            for policy, path, note in result.false_negatives:
                console.print(f"  [red]MISSED [/red] {policy:<8} {path or '(repo-level)'}  — {note}")
            for policy, path, note in result.false_positives:
                console.print(f"  [red]FALSE+ [/red] {policy:<8} {path or '(repo-level)'}  — {note}")
            for policy, path, _ in result.unlabelled:
                console.print(f"  [dim]UNLABELLED {policy:<8} {path or '(repo-level)'}  — triage into the label file[/dim]")

    console.print(
        f"\n[dim]Tolerated findings are excluded from scoring — each one marks a policy "
        f"that is underspecified. Currently {overall.tolerated}.[/dim]"
    )


if __name__ == "__main__":
    app()
