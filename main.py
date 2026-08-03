"""CLI entrypoint for the runtime AGA audit pipeline (Git-only path)."""

import sys
from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

load_dotenv()

from agents.orchestrator import run_audit, write_reports  # noqa: E402 - must load .env before importing agents

app = typer.Typer()
console = Console()


@app.command()
def audit(
    repo: str = typer.Option(..., "--repo", help="Path to the local repository to audit"),
    out: str = typer.Option("reports", "--out", help="Base directory for machine_report.json / draft_report.md"),
) -> None:
    """Run Repository -> Auditor -> Remediation against a local repo and write a compliance report."""
    report = run_audit(repo)
    machine_path, draft_path = write_reports(report, out)

    console.print(f"[bold]Audit complete[/bold] for {report.repo_name}")
    console.print(report.summary)
    if report.errors:
        console.print(f"[yellow]{len(report.errors)} error(s) during the run — see {draft_path}[/yellow]")
    console.print(f"Machine report: {machine_path}")
    console.print(f"Draft report:   {draft_path}")


@app.command()
def batch(
    root: str = typer.Option("sample_repos", "--root", help="Root folder containing category subfolders and repos"),
    out: str = typer.Option("reports", "--out", help="Base directory for all reports"),
    category: str = typer.Option("", "--category", help="Only run repos under this category subfolder (e.g. compliant)"),
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

    console.print(f"\n[bold]Batch audit — {len(repo_paths)} repos[/bold]\n")

    results = []
    failed = 0
    for cat, repo_dir in repo_paths:
        console.print(f"  Auditing [cyan]{cat}/{repo_dir.name}[/cyan] ...")
        try:
            report = run_audit(str(repo_dir))
            machine_path, draft_path = write_reports(report, out)
            s = report.summary
            results.append({
                "category": cat,
                "repo": report.repo_name,
                "total": s["total_findings"],
                "compliant": s["by_status"].get("COMPLIANT", 0),
                "non_compliant": s["by_status"].get("NON_COMPLIANT", 0),
                "needs_review": s["by_status"].get("NEEDS_REVIEW", 0),
                "not_applicable": s["by_status"].get("NOT_APPLICABLE", 0),
                "errors": len(report.errors),
            })
        except Exception as exc:  # noqa: BLE001
            console.print(f"    [red]FAILED: {exc}[/red]")
            results.append({"category": cat, "repo": repo_dir.name, "total": "—", "compliant": "—",
                             "non_compliant": "—", "needs_review": "—", "not_applicable": "—", "errors": "CRASH"})
            failed += 1

    # Summary table
    table = Table(title="\nBatch Audit Summary", show_lines=True)
    table.add_column("Category", style="dim")
    table.add_column("Repo")
    table.add_column("Total", justify="right")
    table.add_column("✅ Compliant", justify="right", style="green")
    table.add_column("❌ Non-Compliant", justify="right", style="red")
    table.add_column("👁 Needs Review", justify="right", style="yellow")
    table.add_column("— N/A", justify="right", style="dim")
    table.add_column("Errors", justify="right")

    for r in results:
        err_str = str(r["errors"])
        table.add_row(
            r["category"], r["repo"],
            str(r["total"]), str(r["compliant"]), str(r["non_compliant"]),
            str(r["needs_review"]), str(r["not_applicable"]),
            f"[red]{err_str}[/red]" if r["errors"] else err_str,
        )

    console.print(table)
    console.print(f"\nReports written to: [bold]{Path(out).resolve()}[/bold]")
    if failed:
        console.print(f"[red]{failed} repo(s) crashed during audit.[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
