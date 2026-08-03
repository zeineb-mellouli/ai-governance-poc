"""Repository Agent: deterministic file I/O only, no LLM calls.

Walks a local repository path and produces a normalised RepositorySnapshot
that the Auditor Agent reasons over.
"""

import json
import os
from pathlib import Path

from agents.schemas import FileRecord, FileType, RepositorySnapshot

SKIP_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".specify", ".claude",
    "node_modules", ".pytest_cache", ".idea", ".vscode", "mlruns",
}

TEXT_EXTENSIONS: dict[str, FileType] = {
    ".py": FileType.PYTHON,
    ".sql": FileType.SQL,
    ".yml": FileType.YAML,
    ".yaml": FileType.YAML,
    ".md": FileType.MARKDOWN,
    ".txt": FileType.OTHER,
    ".cfg": FileType.OTHER,
    ".toml": FileType.OTHER,
    ".json": FileType.OTHER,
}

MAX_CONTENT_CHARS = 6000
TRUNCATION_NOTICE = "\n... [truncated]"


def _cap(content: str) -> str:
    if len(content) > MAX_CONTENT_CHARS:
        return content[:MAX_CONTENT_CHARS] + TRUNCATION_NOTICE
    return content


def _read_text(path: Path) -> str:
    try:
        return _cap(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return ""


def _read_notebook(path: Path) -> str:
    try:
        notebook = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return ""

    parts = []
    for i, cell in enumerate(notebook.get("cells", [])):
        source = "".join(cell.get("source", []))
        parts.append(f"### Cell {i} ({cell.get('cell_type', 'unknown')})\n{source}")

        output_texts = []
        for output in cell.get("outputs", []):
            if "text" in output:
                output_texts.append("".join(output["text"]))
            data = output.get("data", {})
            if "text/plain" in data:
                output_texts.append("".join(data["text/plain"]))
        if output_texts:
            parts.append("--- saved output ---\n" + "\n".join(output_texts))

    return _cap("\n\n".join(parts))


def _read_csv_header(path: Path) -> tuple[str, list[str]]:
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            header_line = f.readline().rstrip("\n\r")
    except OSError:
        return "", []
    columns = [c.strip() for c in header_line.split(",")] if header_line else []
    return header_line, columns


def scan(repo_path: str) -> RepositorySnapshot:
    """Read every recognised file under repo_path into a normalised snapshot."""
    root = Path(repo_path).resolve()
    files: list[FileRecord] = []
    has_readme = False

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            file_path = Path(dirpath) / filename
            rel_path = file_path.relative_to(root).as_posix()
            suffix = file_path.suffix.lower()

            if file_path.parent == root and filename.lower() in ("readme.md", "readme", "readme.txt"):
                has_readme = True

            if suffix == ".ipynb":
                files.append(FileRecord(path=rel_path, file_type=FileType.NOTEBOOK, content=_read_notebook(file_path)))
            elif suffix == ".csv":
                header_line, columns = _read_csv_header(file_path)
                files.append(FileRecord(path=rel_path, file_type=FileType.CSV, content=header_line, csv_columns=columns))
            elif suffix in TEXT_EXTENSIONS:
                files.append(FileRecord(path=rel_path, file_type=TEXT_EXTENSIONS[suffix], content=_read_text(file_path)))
            # unrecognised extensions (images, binaries, parquet, etc.) are skipped entirely

    return RepositorySnapshot(
        repo_root_name=root.name,
        repo_path=str(root),
        has_readme=has_readme,
        files=files,
    )
