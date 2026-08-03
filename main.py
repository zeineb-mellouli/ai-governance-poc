"""CLI entrypoint for the runtime AGA audit pipeline (Git-only path)."""

import typer
from dotenv import load_dotenv
from rich.console import Console

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


if __name__ == "__main__":
    app()
