"""Repository Agent: deterministic file I/O only, no LLM calls.

Walks a local repository path and produces a normalised RepositorySnapshot
that the Auditor Agent reasons over.
"""

import json
import os
import re
from pathlib import Path

from agents.schemas import FileRecord, FileType, RepositorySnapshot

# Directories holding generated output, vendored dependencies, or tool state.
# Auditing them is money spent on artifacts nobody wrote: a .NET repo's bin/ and
# obj/ alone can outnumber its source files, and every file here would be an LLM
# call. The .NET and JVM entries matter because Azure DevOps shops are commonly
# .NET, and the original list only covered Python and Node.
#
# The tradeoff is real: a repository that genuinely keeps source in build/ or
# bin/ would be under-audited. That is the rarer mistake, and it is visible in
# the report's file count, whereas an inflated bill is not.
SKIP_DIRS = {
    # version control and editor/tool state
    ".git", ".idea", ".vscode", ".vs", ".specify", ".claude",
    # Python
    "venv", ".venv", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", "site-packages", "htmlcov", ".eggs",
    # Node
    "node_modules", ".next", ".nuxt", "coverage",
    # .NET / JVM
    "bin", "obj", "packages", "target", ".gradle",
    # generic build output and infrastructure state
    "dist", "build", ".terraform", "mlruns",
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


CSV_PROFILE_ROWS = 5

# Value shapes are classified locally and reported as labels, never as values.
# PII-4 needs to know that a column holds real email addresses rather than
# placeholders; it does not need -- and must not be sent -- the addresses
# themselves, which would land in the prompt and in machine_report.json.
# Order matters: the first pattern to match wins, so the specific shapes are
# tested before the permissive ones (a date and a plain amount would both
# otherwise be swallowed by phone-like).
#
# The labels describe SHAPE, not meaning: "capitalized-words" is what the
# regex can actually prove. Deciding whether that column holds people's names
# is the auditor's job, and it has the column name to reason with.
_VALUE_SHAPES: list[tuple[str, re.Pattern[str]]] = [
    ("placeholder", re.compile(r"^(?:x{3,}|\*{3,}|<[^>]*>|redacted|n/?a|test|sample|foo|bar)$", re.IGNORECASE)),
    ("email-like", re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")),
    ("date-like", re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T].*)?$")),
    ("numeric", re.compile(r"^-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?$")),
    ("phone-like", re.compile(r"^\+?\d[\d\s().-]{6,}$")),
    ("code-like", re.compile(r"^[A-Z0-9]{2,}[-_][A-Z0-9-]+$")),
    ("capitalized-words", re.compile(r"^[A-Z][a-z]+(?:[ '-][A-Z][a-z]+)+$")),
]


def _classify(value: str) -> str:
    value = value.strip().strip('"')
    if not value:
        return "empty"
    for label, pattern in _VALUE_SHAPES:
        if pattern.match(value):
            return label
    return "text"


def _profile_csv_values(path: Path, columns: list[str]) -> str:
    """Return a redacted per-column value-shape summary sampled from the first rows."""
    if not columns:
        return ""
    shapes: list[set[str]] = [set() for _ in columns]
    try:
        with path.open(encoding="utf-8", errors="replace") as f:
            f.readline()  # header, already captured
            for _ in range(CSV_PROFILE_ROWS):
                line = f.readline()
                if not line:
                    break
                for i, cell in enumerate(line.rstrip("\n\r").split(",")[: len(columns)]):
                    shapes[i].add(_classify(cell))
    except OSError:
        return ""

    if not any(shapes):
        return ""
    described = ", ".join(
        f"{col}=<{'|'.join(sorted(s))}>" for col, s in zip(columns, shapes) if s
    )
    return (
        f"# column value shapes, sampled from the first {CSV_PROFILE_ROWS} rows "
        f"(labels only -- literal values are deliberately withheld): {described}"
    )


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

    # os.walk yields directory entries in filesystem order, which is neither
    # sorted nor stable as files are added and removed. The holistic pass fills a
    # fixed character budget in this order and drops whatever no longer fits, so
    # an unsorted walk decides which files that pass is even allowed to see.
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for filename in sorted(filenames):
            file_path = Path(dirpath) / filename
            rel_path = file_path.relative_to(root).as_posix()
            suffix = file_path.suffix.lower()

            if file_path.parent == root and filename.lower() in ("readme.md", "readme", "readme.txt"):
                has_readme = True

            if suffix == ".ipynb":
                files.append(FileRecord(path=rel_path, file_type=FileType.NOTEBOOK, content=_read_notebook(file_path)))
            elif suffix == ".csv":
                header_line, columns = _read_csv_header(file_path)
                profile = _profile_csv_values(file_path, columns)
                content = f"{header_line}\n{profile}" if profile else header_line
                files.append(FileRecord(path=rel_path, file_type=FileType.CSV, content=content, csv_columns=columns))
            elif suffix in TEXT_EXTENSIONS:
                files.append(FileRecord(path=rel_path, file_type=TEXT_EXTENSIONS[suffix], content=_read_text(file_path)))
            # unrecognised extensions (images, binaries, parquet, etc.) are skipped entirely

    return RepositorySnapshot(
        repo_root_name=root.name,
        repo_path=str(root),
        has_readme=has_readme,
        files=files,
    )
