"""Repository Agent: deterministic file I/O only, no LLM calls.

Walks a local repository path and produces a normalised RepositorySnapshot
that the Auditor Agent reasons over.
"""

import json
import os
import re
from pathlib import Path

from agents.schemas import FileRecord, FileType, RepositorySnapshot

# Generated output, vendored dependencies, and tool state; artifacts nobody
# wrote, each costing an LLM call. 
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

# Spec-driven-development scaffolding, policies govern the pipeline
# that runs in production, not the documents specifying it.
SKIP_PATH_PREFIXES = (
    "specs/",
    ".specify/",
    ".github/agents/",
    ".github/prompts/",
    ".github/instructions/",
    ".github/chatmodes/",
)

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

    # Every sorted() here is load-bearing: os.walk yields entries in filesystem
    # order, which is neither sorted nor stable. The holistic pass fills a fixed
    # character budget in this order and drops what no longer fits, so an
    # unsorted walk would decide which files that pass is allowed to see.
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = Path(dirpath).relative_to(root).as_posix()
        prefix = "" if rel_dir == "." else f"{rel_dir}/"
        # Pruned in place, so an excluded tree is never descended into at all.
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in SKIP_DIRS
            and not any(f"{prefix}{d}/".startswith(skip) for skip in SKIP_PATH_PREFIXES)
        )
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
                files.append(FileRecord(path=rel_path, file_type=FileType.CSV, content=content))
            elif suffix in TEXT_EXTENSIONS:
                files.append(FileRecord(path=rel_path, file_type=TEXT_EXTENSIONS[suffix], content=_read_text(file_path)))
            # unrecognised extensions (images, binaries, parquet, etc.) are skipped entirely

    return RepositorySnapshot(
        repo_root_name=root.name,
        repo_path=str(root),
        has_readme=has_readme,
        files=files,
    )
