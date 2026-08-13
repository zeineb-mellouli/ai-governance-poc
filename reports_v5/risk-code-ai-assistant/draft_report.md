# Compliance Report — risk-code-ai-assistant

Run at: 2026-08-11T12:19:34.029602+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\risk-code-ai-assistant
Self-consistency samples (k): 1
> At k=1 no disagreement is measurable, so every confidence is 1.0 and the remediation confidence gate does not fire.

## Summary

**Weighted pass rate: 71.8%** (163/227 weighted checks) — 8 high, 9 medium, 22 low severity violations

- Checks evaluated: 238
- Applicable checks (compliant + non-compliant): 103
- COMPLIANT: 64
- NON_COMPLIANT: 39
- NOT_APPLICABLE: 135
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 39

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** app/refresh.py
**Sample agreement:** 100%
**Evidence:** The file performs downstream data processing without any explicit quality check in this file before further use.  Quoted: 'results = run_ingestion(config_path)'

**Suggested fix:** Add an explicit data quality validation step immediately after ingestion and before downstream processing in app/refresh.py.

```
python - <<'PY'
from pathlib import Path
path = Path('app/refresh.py')
text = path.read_text()
old = '''def run_refresh(config_path: str = "config.yaml") -> dict[str, int]:
    results = run_ingestion(config_path)
    run_normalization(config_path)
'''
new = '''def run_refresh(config_path: str = "config.yaml") -> dict[str, int]:
    results = run_ingestion(config_path)
    if not results:
        raise ValueError("Data quality validation failed: ingestion returned no results")
    run_normalization(config_path)
'''
if old not in text:
    raise SystemExit('Expected snippet not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** ingestion/loader.py
**Sample agreement:** 100%
**Evidence:** The file loads data/configuration and performs downstream transformations without any explicit quality validation shown in the visible content.  Quoted: 'def load_config(config_path: str = "config.yaml") -> dict:\n    resolved = _ROOT / config_path if not Path(config_path).is_absolute() else Path(config_path)\n    return yaml.safe_load(resolved.read_text())'

**Suggested fix:** Add an explicit data-quality validation step to loader.py before returning loaded config/data, using a minimal non-destructive check on required content.

```
python - <<'PY'
from pathlib import Path
p = Path('ingestion/loader.py')
text = p.read_text()
needle = 'def load_config(config_path: str = "config.yaml") -> dict:\n    resolved = _ROOT / config_path if not Path(config_path).is_absolute() else Path(config_path)\n    return yaml.safe_load(resolved.read_text())\n'
replacement = '''def load_config(config_path: str = "config.yaml") -> dict:
    resolved = _ROOT / config_path if not Path(config_path).is_absolute() else Path(config_path)
    config = yaml.safe_load(resolved.read_text())
    if not isinstance(config, dict) or not config:
        raise ValueError(f"Invalid or empty config: {resolved}")
    return config
'''
if needle not in text:
    raise SystemExit('target snippet not found')
p.write_text(text.replace(needle, replacement, 1))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** ingestion/normalizer.py
**Sample agreement:** 100%
**Evidence:** The file loads table data and writes it back without any explicit quality check in between.  Quoted: 'df = pd.read_sql(f"SELECT * FROM {table_name}", con)  # noqa: S608'

**Suggested fix:** Add an explicit data-quality validation step before writing normalized table data back to SQLite.

```
python - <<'PY'
from pathlib import Path
path = Path('ingestion/normalizer.py')
text = path.read_text()
old = '''def normalize_table(table_name: str, db_path: str, normalizations: list[dict]) -> None:
    """Read a SQLite table, apply all normalization rules, write back."""
    con = sqlite3.connect(db_path)
    try:
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name}", con)  # noqa: S608
        except Exception:
            logger.warning("Table '%s' not found, skipping normalization", table_name)
            return

        for norm in normalizations:
            df = _apply_normalization(df, norm)

        df.to_sql(table_name, con, if_exists="replace", index=False)
        logger.info("Normalized table '%s'", table_name)
    finally:
        con.close()
'''
new = '''def normalize_table(table_name: str, db_path: str, normalizations: list[dict]) -> None:
    """Read a SQLite table, apply all normalization rules, validate, write back."""
    con = sqlite3.connect(db_path)
    try:
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name}", con)  # noqa: S608
        except Exception:
            logger.warning("Table '%s' not found, skipping normalization", table_name)
            return

        for norm in normalizations:
            df = _apply_normalization(df, norm)

        # Explicit quality check: ensure the normalized frame is not empty before persisting.
        if df.empty:
            raise ValueError(f"Data quality validation failed for table '{table_name}': empty result set")

        df.to_sql(table_name, con, if_exists="replace", index=False)
        logger.info("Normalized table '%s'", table_name)
    finally:
        con.close()
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** ingestion/pdf_loader.py
**Sample agreement:** 100%
**Evidence:** The file performs data ingestion and downstream indexing without any visible data quality validation step first.  Quoted: 'def _extract_pages(pdf_path: Path) -> list[dict]:'

**Suggested fix:** Add a lightweight data-quality validation step before page extraction and indexing in ingestion/pdf_loader.py

```
python - <<'PY'
from pathlib import Path
path = Path('ingestion/pdf_loader.py')
text = path.read_text()
needle = '''def _extract_pages(pdf_path: Path) -> list[dict]:
    """Return a list of {page_number, text, tables} dicts for every page in the PDF."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    pages = []
'''
replacement = '''def _validate_pdf_for_ingestion(pdf_path: Path) -> None:
    """Basic data-quality checks before ingestion."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file: {pdf_path}")
    if pdf_path.stat().st_size == 0:
        raise ValueError(f"PDF is empty: {pdf_path}")


def _extract_pages(pdf_path: Path) -> list[dict]:
    """Return a list of {page_number, text, tables} dicts for every page in the PDF."""
    _validate_pdf_for_ingestion(pdf_path)
    try:
        import pdfplumber
    except ImportError:
        raise ImportError("pdfplumber is required: pip install pdfplumber")

    pages = []
'''
if needle not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(needle, replacement))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** scripts/audit_powerbi_export.py
**Sample agreement:** 100%
**Evidence:** The script profiles and compares data but shows no explicit quality check before using it further.  Quoted: 'Analysis covers:\n  1. Schema     — columns in the original not in the export, and vice-versa\n  2. Content    — null breakdowns per category group, value distributions\n  3. Representation gaps — how the original formats fields vs the export'

**Suggested fix:** Add an explicit data-quality validation gate before further analysis in scripts/audit_powerbi_export.py.

```
python - <<'PY'
from pathlib import Path
path = Path('scripts/audit_powerbi_export.py')
text = path.read_text()
needle = """def _detect_group_col(df: pd.DataFrame) -> str | None:
    candidates = [
        \"source\", \"risk_category\", \"category\", \"category_1\",
        \"taxonomy_root\", \"type\", \"organisation\", \"business_unit\",
    ]
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        if df[c].dtype == object and 2 <= df[c].nunique() <= 50:
            return c
    return None

"""
insert = needle + """def _validate_quality(df: pd.DataFrame, label: str) -> None:
    required = [c for c in _EXPORT_METRIC_COLS if c in df.columns]
    if not required:
        raise ValueError(f\"{label}: no expected metric columns found for quality validation\")
    missing = [c for c in required if df[c].isna().all()]
    if missing:
        raise ValueError(f\"{label}: quality validation failed; all values missing in: {', '.join(missing)}\")

"""
if needle not in text:
    raise SystemExit('anchor not found')
text = text.replace(needle, insert, 1)
path.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** scripts/build_all_risks.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any visible quality check first.  Quoted: 'dl = pd.read_sql("SELECT * FROM dl_risks", con)'

**Suggested fix:** Add a lightweight data-quality validation check immediately after loading dl_risks before the data is used further.

```
python - <<'PY'
from pathlib import Path
path = Path('scripts/build_all_risks.py')
text = path.read_text()
old = '    dl = pd.read_sql("SELECT * FROM dl_risks", con)\n    tax = pd.read_sql(\n'
new = '    dl = pd.read_sql("SELECT * FROM dl_risks", con)\n    if dl.empty:\n        raise ValueError("dl_risks failed validation: no rows loaded")\n    tax = pd.read_sql(\n'
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new, 1))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** scripts/export_for_powerbi.py
**Sample agreement:** 100%
**Evidence:** The file loads data and exports it onward without any intervening quality check, so it violates the validation requirement.  Quoted: 'return pd.read_sql("SELECT * FROM all_risks", con)'

**Suggested fix:** Add a lightweight data-quality validation step before exporting the all_risks table to Power BI.

```
python - <<'PY'
from pathlib import Path
path = Path('scripts/export_for_powerbi.py')
text = path.read_text()
old = '''def build_all_risks(con: sqlite3.Connection) -> pd.DataFrame:
    """
    Primary sheet — unified DeLaval + Tetra Pak risks.
    All score, label, and intensity sort columns are produced by build_all_risks.py.
    """
    return pd.read_sql("SELECT * FROM all_risks", con)
'''
new = '''def build_all_risks(con: sqlite3.Connection) -> pd.DataFrame:
    """
    Primary sheet — unified DeLaval + Tetra Pak risks.
    All score, label, and intensity sort columns are produced by build_all_risks.py.
    """
    df = pd.read_sql("SELECT * FROM all_risks", con)
    if df.empty:
        raise ValueError("all_risks is empty; run ingest.py/build_all_risks.py before exporting")
    return df
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** scripts/index_docs.py
**Sample agreement:** 100%
**Evidence:** The script loads and processes data without any visible quality check before indexing it.  Quoted: 'n = build_pdf_index()'

**Suggested fix:** Add a visible data-quality validation step before indexing PDFs in scripts/index_docs.py.

```
python - <<'PY'
from pathlib import Path
path = Path('scripts/index_docs.py')
text = path.read_text()
old = '''    print(f"Found {pdf_count} PDF file(s) in {pdf_dir}")
    print("Building index...")

    n = build_pdf_index()
'''
new = '''    print(f"Found {pdf_count} PDF file(s) in {pdf_dir}")
    print("Validating PDF inputs...")
    for pdf in pdf_dir.glob("*.pdf"):
        if pdf.stat().st_size == 0:
            print(f"Invalid PDF input (empty file): {pdf}")
            sys.exit(1)
    print("Building index...")

    n = build_pdf_index()
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'risk-code-ai-assistant' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from risk-code-ai-assistant to a compliant name using an allowed prefix and suffix pattern.

```
mv risk-code-ai-assistant fin-code-ai-assistant
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** data/test.py
**Sample agreement:** 100%
**Evidence:** The script performs work with only print-based output and no durable logging or metrics, violating the monitoring requirement.  Quoted: 'print("AZURE KEY FOUND:", bool(os.getenv("AZURE_OPENAI_API_KEY")))'

**Suggested fix:** Replace print-based status output with durable Python logging in data/test.py.

```
python - <<'PY'
from pathlib import Path
path = Path('data/test.py')
text = path.read_text()
text = text.replace('import os\nfrom openai import AzureOpenAI\nfrom dotenv import load_dotenv\nload_dotenv()  # Load environment variables from .env file\nprint("AZURE KEY FOUND:", bool(os.getenv("AZURE_OPENAI_API_KEY")))\n', 'import os\nimport logging\nfrom openai import AzureOpenAI\nfrom dotenv import load_dotenv\n\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n\nload_dotenv()  # Load environment variables from .env file\nlogger.info("AZURE KEY FOUND: %s", bool(os.getenv("AZURE_OPENAI_API_KEY")))\n')
text = text.replace('print("✅ Embeddings connected")\nprint("Vector length:", len(embedding))\nprint("First 3 values:", embedding[:3])\n', 'logger.info("Embeddings connected")\nlogger.info("Vector length: %s", len(embedding))\nlogger.info("First 3 values: %s", embedding[:3])\n')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** ingestion/schema_profiler.py
**Sample agreement:** 100%
**Evidence:** The file performs data I/O but contains no logging or durable monitoring record, so it violates the logging/monitoring policy.  Quoted: 'return "No database found. Run ingestion first."'

**Suggested fix:** Add a durable monitoring record by logging the missing-database condition before returning the existing message.

```
python - <<'PY'
from pathlib import Path
path = Path('ingestion/schema_profiler.py')
text = path.read_text()
old = 'import re\nimport sqlite3\nfrom datetime import datetime\n'
new = 'import logging\nimport re\nimport sqlite3\nfrom datetime import datetime\n'
if old not in text:
    raise SystemExit('import block not found')
text = text.replace(old, new, 1)
old = '    if not Path(db_path).exists():\n        return "No database found. Run ingestion first."\n'
new = '    if not Path(db_path).exists():\n        logging.warning("No database found. Run ingestion first.")\n        return "No database found. Run ingestion first."\n'
if old not in text:
    raise SystemExit('missing-db block not found')
text = text.replace(old, new, 1)
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** scripts/audit_excel.py
**Sample agreement:** 100%
**Evidence:** The script relies on print statements and does not use persistent logging or exception logging, so it fails the monitoring requirement.  Quoted: 'print("Profiling Excel sheets...")'

**Suggested fix:** Replace print-based status and exception output in scripts/audit_excel.py with persistent logging to a file plus exception logging.

```
python - <<'PY'
from pathlib import Path
path = Path('scripts/audit_excel.py')
text = path.read_text()
text = text.replace('import sys\nfrom datetime import datetime\nfrom pathlib import Path\n\nimport pandas as pd\nimport yaml\n', 'import logging\nimport sys\nfrom datetime import datetime\nfrom pathlib import Path\n\nimport pandas as pd\nimport yaml\n')
text = text.replace('from agent.llm import get_llm\n\n_ROOT = Path(__file__).parent.parent\n', 'from agent.llm import get_llm\n\n_ROOT = Path(__file__).parent.parent\n_LOG_PATH = _ROOT / "logs" / "audit_excel.log"\n_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)\nlogging.basicConfig(\n    filename=_LOG_PATH,\n    level=logging.INFO,\n    format="%(asctime)s %(levelname)s %(message)s",\n)\nlogger = logging.getLogger(__name__)\n')
text = text.replace('    print("Profiling Excel sheets...")\n', '    logger.info("Profiling Excel sheets...")\n')
text = text.replace('            print(f"  SKIP (not found): {entry[\'filename\']}")\n', '            logger.warning("SKIP (not found): %s", entry["filename"])\n')
text = text.replace('        print(f"  {table}  ({sheet})")\n', '        logger.info("Profiling %s (%s)", table, sheet)\n')
text = text.replace('        except Exception as exc:\n            print(f"    ERROR: {exc}")\n', '        except Exception:\n            logger.exception("ERROR profiling %s (%s)", table, sheet)\n')
text = text.replace('        print("No sheets could be read. Check that data/raw/ contains the Excel files.")\n', '        logger.error("No sheets could be read. Check that data/raw/ contains the Excel files.")\n')
text = text.replace('    print(f"\\n{len(profiles)} sheets profiled. Calling GPT-4o...")\n', '    logger.info("%s sheets profiled. Calling GPT-4o...", len(profiles))\n')
text = text.replace('    print(f"\\nReport written to {out_path.name}")\n    print("-" * 60)\n    print(report)\n', '    logger.info("Report written to %s", out_path.name)\n    logger.info("%s", "-" * 60)\n    logger.info("%s", report)\n')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** scripts/audit_powerbi_export.py
**Sample agreement:** 100%
**Evidence:** The script performs file I/O but the visible content shows no logging or exception logging.  Quoted: 'Run: python scripts/audit_powerbi_export.py\nOutput: POWERBI_EXPORT_AUDIT.md at the project root'

**Suggested fix:** Add minimal logging and exception logging to the audit script so file I/O and failures are recorded.

```
python - <<'PY'
from pathlib import Path
p = Path('scripts/audit_powerbi_export.py')
s = p.read_text()
if 'import logging\n' not in s:
    s = s.replace('import sys\n', 'import sys\nimport logging\n')
if 'logger = logging.getLogger(__name__)\n' not in s:
    s = s.replace('_ROOT = Path(__file__).resolve().parent.parent\n\n# ── Configure before running ──────────────────────────────────────────────────\n', '_ROOT = Path(__file__).resolve().parent.parent\n\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n\n# ── Configure before running ──────────────────────────────────────────────────\n')
s = s.replace('def main():\n', 'def main():\n    logger.info("Starting Power BI export audit")\n')
# Add a generic exception log if a top-level try/except exists; otherwise wrap main invocation.
old = 'if __name__ == "__main__":\n    main()\n'
new = 'if __name__ == "__main__":\n    try:\n        main()\n    except Exception:\n        logger.exception("Power BI export audit failed")\n        raise\n'
if old in s:
    s = s.replace(old, new)
else:
    s += '\n' + new
p.write_text(s)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** scripts/export_for_powerbi.py
**Sample agreement:** 100%
**Evidence:** The script relies on print output rather than logging or another durable record, so it violates the monitoring requirement.  Quoted: 'print(f"\\nExported to {out_path}")'

**Suggested fix:** Replace the export status print with a durable logging call and keep the user-facing Power BI guidance as-is.

```
python - <<'PY'
from pathlib import Path
path = Path('scripts/export_for_powerbi.py')
text = path.read_text()
text = text.replace('import sqlite3\nimport sys\n', 'import logging\nimport sqlite3\nimport sys\n')
text = text.replace('sys.path.insert(0, str(Path(__file__).parent.parent))\n\ndef build_all_risks', 'sys.path.insert(0, str(Path(__file__).parent.parent))\n\nlogging.basicConfig(level=logging.INFO, format="%(message)s")\nlogger = logging.getLogger(__name__)\n\ndef build_all_risks')
text = text.replace('    print(f"\\nExported to {out_path}")\n', '    logger.info("Exported to %s", out_path)\n')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** scripts/index_docs.py
**Sample agreement:** 100%
**Evidence:** The script relies on print statements for failure handling instead of logging the error path.  Quoted: 'print(f"PDF directory not found: {pdf_dir}")'

**Suggested fix:** Replace failure-path print statements in scripts/index_docs.py with logging calls so errors are reported through the logger.

```
python - <<'PY'
from pathlib import Path
path = Path('scripts/index_docs.py')
text = path.read_text()
text = text.replace('        print(f"PDF directory not found: {pdf_dir}")\n        print("Create data/docs/ and drop PDF files there, then re-run.")\n', '        logging.error(f"PDF directory not found: {pdf_dir}")\n        logging.error("Create data/docs/ and drop PDF files there, then re-run.")\n')
text = text.replace('        print(f"No PDF files found in {pdf_dir}")\n        print("Drop PDF files into data/docs/ and re-run.")\n', '        logging.error(f"No PDF files found in {pdf_dir}")\n        logging.error("Drop PDF files into data/docs/ and re-run.")\n')
text = text.replace('        print("\\nNo chunks were indexed. Check logs above for errors.")\n', '        logging.error("No chunks were indexed. Check logs above for errors.")\n')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** scripts/notebooks/audit_metrics.ipynb
**Sample agreement:** 100%
**Evidence:** The notebook relies on print statements and does not use persistent logging, which violates the monitoring requirement.  Quoted: 'print(f"  Could not read {table}: {exc}")'

**Suggested fix:** Replace notebook print-based status/error output with persistent logging via the standard logging module.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('scripts/notebooks/audit_metrics.ipynb')
nb = json.loads(p.read_text())
# Cell 1
src = nb['cells'][1]['source']
if isinstance(src, list):
    src = ''.join(src)
src = src.replace('import sqlite3\nimport sys\nfrom pathlib import Path\n\nimport pandas as pd\nimport yaml\n', 'import logging\nimport sqlite3\nimport sys\nfrom pathlib import Path\n\nimport pandas as pd\nimport yaml\n')
src = src.replace('con = sqlite3.connect(DB_PATH)\nprint(f"Connected to {DB_PATH}")\n', 'logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n\ncon = sqlite3.connect(DB_PATH)\nlogger.info("Connected to %s", DB_PATH)\n')
nb['cells'][1]['source'] = src
# Cell 2
src = nb['cells'][2]['source']
if isinstance(src, list):
    src = ''.join(src)
src = src.replace('        print(f"  Could not read {table}: {exc}")\n', '        logger.exception("Could not read %s", table)\n')
src = src.replace('    print(f"\\n{\'=\'*65}")\n    print(f"TABLE: {table}  ({len(metric_cols)} metric columns)")\n    print(\'=\'*65)\n', '    logger.info("%s", "="*65)\n    logger.info("TABLE: %s  (%d metric columns)", table, len(metric_cols))\n    logger.info("%s", "="*65)\n')
src = src.replace('        print("\\n  OK — both forms present:")\n        for g in ok:\n            print(f"    {g[\'column\']} ({g[\'type\']})  ↔  {g[\'counterpart\']}")\n', '        logger.info("OK — both forms present:")\n        for g in ok:\n            logger.info("    %s (%s)  ↔  %s", g["column"], g["type"], g["counterpart"])\n')
src = src.replace('        print(f"\\n  MISSING counterpart:")\n        for g in gaps:\n            print(f"\\n    Column  : {g[\'column\']}")\n            print(f"    Type    : {g[\'type\']}  (missing {g[\'counterpart_type\']} version)")\n            print(f"    Nulls   : {g[\'null_pct\']}%")\n            print(f"    Values  : {g[\'samples\']}")\n', '        logger.warning("MISSING counterpart:")\n        for g in gaps:\n            logger.warning("    Column  : %s", g["column"])\n            logger.warning("    Type    : %s  (missing %s version)", g["type"], g["counterpart_type"])\n            logger.warning("    Nulls   : %s%%", g["null_pct"])\n            logger.warning("    Values  : %s", g["samples"])\n')
src = src.replace('        print("\\n  All metric columns have both forms.")\n', '        logger.info("All metric columns have both forms.")\n')
nb['cells'][2]['source'] = src
# Cell 3
src = nb['cells'][3]['source']
if isinstance(src, list):
    src = ''.join(src)
src = src.replace('print(f"\\n{\'=\'*65}")\nprint(f"SUMMARY: {total_missing} metric columns missing a counterpart form")\nif total_missing:\n    print("  → For each MISSING entry, add a normalization rule in config.yaml")\n    print("    following the existing gross_impact / gross_likelihood pattern.")\nelse:\n    print("  → All key risk metrics have both numeric and label forms.")\n', 'logger.info("%s", "="*65)\nlogger.info("SUMMARY: %d metric columns missing a counterpart form", total_missing)\nif total_missing:\n    logger.info("For each MISSING entry, add a normalization rule in config.yaml")\n    logger.info("following the existing gross_impact / gross_likelihood pattern.")\nelse:\n    logger.info("All key risk metrics have both numeric and label forms.")\n')
nb['cells'][3]['source'] = src
# Cell 6
src = nb['cells'][6]['source']
if isinstance(src, list):
    src = ''.join(src)
src = src.replace('con.close()\nprint("Done.")\n', 'con.close()\nlogger.info("Done.")\n')
nb['cells'][6]['source'] = src
p.write_text(json.dumps(nb, indent=1))
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** scripts/notebooks/eda_exploration.ipynb
**Sample agreement:** 100%
**Evidence:** The notebook performs data I/O but relies on print output rather than durable logging or queryable metrics.  Quoted: 'print(f"{\'Table\':<45} {\'Rows\':>8}")'

**Suggested fix:** Replace notebook print-based table summaries with durable logging calls so data I/O is recorded via the logging system instead of stdout prints.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('scripts/notebooks/eda_exploration.ipynb')
nb = json.loads(p.read_text())
cell = nb['cells'][1]
cell['source'] = [
"import logging\n",
"import sqlite3\n",
"import sys\n",
"from pathlib import Path\n",
"\n",
"import pandas as pd\n",
"import yaml\n",
"\n",
"logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')\n",
"logger = logging.getLogger(__name__)\n",
"\n",
"# Walk up from cwd until config.yaml is found — works regardless of where Jupyter is launched\n",
"ROOT = Path.cwd()\n",
"while not (ROOT / 'config.yaml').exists() and ROOT.parent != ROOT:\n",
"    ROOT = ROOT.parent\n",
"assert (ROOT / 'config.yaml').exists(), f'Could not locate project root from {Path.cwd()}'\n",
"\n",
"if str(ROOT) not in sys.path:\n",
"    sys.path.insert(0, str(ROOT))\n",
"\n",
"cfg = yaml.safe_load((ROOT / 'config.yaml').read_text())\n",
"DB_PATH = ROOT / cfg['data']['db_path']\n",
"RAW_DIR = ROOT / cfg['data']['raw_dir']\n",
"\n",
"assert DB_PATH.exists(), f'Database not found at {DB_PATH} — run ingest.py first'\n",
"\n",
"con = sqlite3.connect(DB_PATH)\n",
"logger.info('Project root : %s', ROOT)\n",
"logger.info('Connected to : %s', DB_PATH)\n",
]
for idx in [3,4]:
    src = nb['cells'][idx]['source']
    nb['cells'][idx]['source'] = [line.replace('print(', 'logger.info(') for line in src]
    nb['cells'][idx]['source'] = [line.replace("print(f\"{\'Table\':<45} {\'Rows\':>8}\")", "logger.info('%-45s %8s', 'Table', 'Rows')") if line.strip()=="print(f\"{'Table':<45} {'Rows':>8}\")" else line for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print('-' * 55)", "logger.info('%s', '-' * 55)") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(f\"{t:<45} {n:>8,}\")", "logger.info('%-45s %8s', t, format(n, ','))") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(f\"\\n{'='*60}\")", "logger.info('%s', '\\n' + '='*60)") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(f\"TABLE: {table}  ({len(df):,} rows × {len(df.columns)} cols)\")", "logger.info('TABLE: %s  (%s rows × %s cols)', table, format(len(df), ','), len(df.columns))") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print('='*60)", "logger.info('%s', '='*60)") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(describe_col(df, col))", "logger.info('%s', describe_col(df, col))") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(f\"  [ERROR reading {table}: {e}]\")", "logger.error('  [ERROR reading %s: %s]', table, e)") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(f\"  [skip — column missing]\")", "logger.info('  [skip — column missing]')") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(f\"  {label}\")", "logger.info('  %s', label)") for line in nb['cells'][idx]['source']]
    nb['cells'][idx]['source'] = [line.replace("print(f\"    left={len(left_vals)}  right={len(right_vals)}  matched={len(matched)} ({pct:.0f}%)\")", "logger.info('    left=%s  right=%s  matched=%s (%s%%)', len(left_vals), len(right_vals), len(matched), f'{pct:.0f}')") for line in nb['cells'][idx]['source']]
p.write_text(json.dumps(nb, indent=1))
PY
```

### REPRO-13 · Dependency versions pinned [LOW]

**Location:** requirements.txt
**Sample agreement:** 100%
**Evidence:** Packages declared without an exact version, and no lockfile to record one -- requirements.txt: PyYAML, chromadb, ddgs, llama-index-retrievers-bm25, llama-index-vector-stores-chroma, openpyxl, pandas, pdfplumber, pytest, python-dotenv, rank_bm25, shiny, sqlalchemy.

**Suggested fix:** Pin all unversioned dependencies in requirements.txt to exact versions using the versions already present where available, and leave placeholders for packages whose exact versions cannot be derived from the file content.

```
python - <<'PY'
from pathlib import Path
p = Path('requirements.txt')
text = p.read_text()
replacements = {
    'python-dotenv>=1.0': 'python-dotenv==1.0.0',
    'pandas>=2.0': 'pandas==2.0.0',
    'openpyxl>=3.1': 'openpyxl==3.1.0',
    'PyYAML>=6.0': 'PyYAML==6.0.0',
    'sqlalchemy>=2.0': 'sqlalchemy==2.0.0',
    'pytest>=7.0': 'pytest==7.0.0',
    'pdfplumber>=0.10': 'pdfplumber==0.10.0',
    'chromadb>=0.4': 'chromadb==0.4.0',
    'llama-index-vector-stores-chroma>=0.1': 'llama-index-vector-stores-chroma==0.1.0',
    'llama-index-retrievers-bm25>=0.1': 'llama-index-retrievers-bm25==0.1.0',
    'rank_bm25>=0.2': 'rank_bm25==0.2.0',
    'shiny>=1.0': 'shiny==1.0.0',
    'ddgs>=6.0': 'ddgs==6.0.0',
}
for old, new in replacements.items():
    text = text.replace(old, new)
p.write_text(text)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** config.yaml
**Sample agreement:** 100%
**Evidence:** file name stem 'config' is not CamelCase

**Suggested fix:** Rename to 'Config.yaml' to satisfy the NAM-5 naming grammar.

```
git mv config.yaml Config.yaml
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** agent/agent.py
**Sample agreement:** 100%
**Evidence:** file name stem 'agent' is not CamelCase

**Suggested fix:** Rename to 'agent/Agent.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'agent' must be updated to 'Agent' in the same change.

```
git mv agent/agent.py agent/Agent.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** agent/llm.py
**Sample agreement:** 100%
**Evidence:** file name stem 'llm' is not CamelCase

**Suggested fix:** Rename to 'agent/Llm.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'llm' must be updated to 'Llm' in the same change.

```
git mv agent/llm.py agent/Llm.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** agent/rag.py
**Sample agreement:** 100%
**Evidence:** file name stem 'rag' is not CamelCase

**Suggested fix:** Rename to 'agent/Rag.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'rag' must be updated to 'Rag' in the same change.

```
git mv agent/rag.py agent/Rag.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** agent/schema.py
**Sample agreement:** 100%
**Evidence:** file name stem 'schema' is not CamelCase

**Suggested fix:** Rename to 'agent/Schema.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'schema' must be updated to 'Schema' in the same change.

```
git mv agent/schema.py agent/Schema.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** agent/tools.py
**Sample agreement:** 100%
**Evidence:** file name stem 'tools' is not CamelCase

**Suggested fix:** Rename to 'agent/Tools.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'tools' must be updated to 'Tools' in the same change.

```
git mv agent/tools.py agent/Tools.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** app/refresh.py
**Sample agreement:** 100%
**Evidence:** file name stem 'refresh' is not CamelCase

**Suggested fix:** Rename to 'app/Refresh.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'refresh' must be updated to 'Refresh' in the same change.

```
git mv app/refresh.py app/Refresh.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** app/shiny_app.py
**Sample agreement:** 100%
**Evidence:** file name stem 'shiny_app' is not CamelCase

**Suggested fix:** Rename to 'app/ShinyApp.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'shiny_app' must be updated to 'ShinyApp' in the same change.

```
git mv app/shiny_app.py app/ShinyApp.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/test.py
**Sample agreement:** 100%
**Evidence:** file name stem 'test' is not CamelCase

**Suggested fix:** Rename to 'data/Test.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'test' must be updated to 'Test' in the same change.

```
git mv data/test.py data/Test.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** ingestion/loader.py
**Sample agreement:** 100%
**Evidence:** file name stem 'loader' is not CamelCase

**Suggested fix:** Rename to 'ingestion/Loader.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'loader' must be updated to 'Loader' in the same change.

```
git mv ingestion/loader.py ingestion/Loader.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** ingestion/normalizer.py
**Sample agreement:** 100%
**Evidence:** file name stem 'normalizer' is not CamelCase

**Suggested fix:** Rename to 'ingestion/Normalizer.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'normalizer' must be updated to 'Normalizer' in the same change.

```
git mv ingestion/normalizer.py ingestion/Normalizer.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** ingestion/pdf_loader.py
**Sample agreement:** 100%
**Evidence:** file name stem 'pdf_loader' is not CamelCase

**Suggested fix:** Rename to 'ingestion/PdfLoader.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'pdf_loader' must be updated to 'PdfLoader' in the same change.

```
git mv ingestion/pdf_loader.py ingestion/PdfLoader.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** ingestion/schema_profiler.py
**Sample agreement:** 100%
**Evidence:** file name stem 'schema_profiler' is not CamelCase

**Suggested fix:** Rename to 'ingestion/SchemaProfiler.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'schema_profiler' must be updated to 'SchemaProfiler' in the same change.

```
git mv ingestion/schema_profiler.py ingestion/SchemaProfiler.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/audit_excel.py
**Sample agreement:** 100%
**Evidence:** file name stem 'audit_excel' is not CamelCase

**Suggested fix:** Rename to 'scripts/AuditExcel.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'audit_excel' must be updated to 'AuditExcel' in the same change.

```
git mv scripts/audit_excel.py scripts/AuditExcel.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/audit_powerbi_export.py
**Sample agreement:** 100%
**Evidence:** file name stem 'audit_powerbi_export' is not CamelCase

**Suggested fix:** Rename to 'scripts/AuditPowerbiExport.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'audit_powerbi_export' must be updated to 'AuditPowerbiExport' in the same change.

```
git mv scripts/audit_powerbi_export.py scripts/AuditPowerbiExport.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/build_all_risks.py
**Sample agreement:** 100%
**Evidence:** file name stem 'build_all_risks' is not CamelCase

**Suggested fix:** Rename to 'scripts/BuildAllRisks.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'build_all_risks' must be updated to 'BuildAllRisks' in the same change.

```
git mv scripts/build_all_risks.py scripts/BuildAllRisks.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/export_for_powerbi.py
**Sample agreement:** 100%
**Evidence:** file name stem 'export_for_powerbi' is not CamelCase

**Suggested fix:** Rename to 'scripts/ExportForPowerbi.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'export_for_powerbi' must be updated to 'ExportForPowerbi' in the same change.

```
git mv scripts/export_for_powerbi.py scripts/ExportForPowerbi.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/index_docs.py
**Sample agreement:** 100%
**Evidence:** file name stem 'index_docs' is not CamelCase

**Suggested fix:** Rename to 'scripts/IndexDocs.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'index_docs' must be updated to 'IndexDocs' in the same change.

```
git mv scripts/index_docs.py scripts/IndexDocs.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/ingest.py
**Sample agreement:** 100%
**Evidence:** file name stem 'ingest' is not CamelCase

**Suggested fix:** Rename to 'scripts/Ingest.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'ingest' must be updated to 'Ingest' in the same change.

```
git mv scripts/ingest.py scripts/Ingest.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/notebooks/audit_metrics.ipynb
**Sample agreement:** 100%
**Evidence:** file name stem 'audit_metrics' is not CamelCase

**Suggested fix:** Rename to 'scripts/notebooks/AuditMetrics.ipynb' to satisfy the NAM-5 naming grammar.

```
git mv scripts/notebooks/audit_metrics.ipynb scripts/notebooks/AuditMetrics.ipynb
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** scripts/notebooks/eda_exploration.ipynb
**Sample agreement:** 100%
**Evidence:** file name stem 'eda_exploration' is not CamelCase

**Suggested fix:** Rename to 'scripts/notebooks/EdaExploration.ipynb' to satisfy the NAM-5 naming grammar.

```
git mv scripts/notebooks/eda_exploration.ipynb scripts/notebooks/EdaExploration.ipynb
```

## Checks that passed or did not apply

64 checks passed; 135 did not apply to this repository. See machine_report.json for the full list.
