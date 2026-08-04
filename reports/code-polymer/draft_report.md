# Compliance Report — code-polymer

Run at: 2026-08-04T12:23:26.905271+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\code-polymer

## Summary

- Total findings evaluated: 345
- NON_COMPLIANT: 5
- COMPLIANT: 103
- NEEDS_REVIEW: 4
- NOT_APPLICABLE: 233

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** pipeline/transforms.py
**Confidence:** 0.91  |  **Risk score:** 2.73
**Evidence:** The file loads data and uses it with no validation checks anywhere in the file; `add_loaded_at` only does `out = df.copy()` and `out["loaded_at"] = pd.Timestamp.now(tz="UTC")`.

**Suggested fix:** Add an explicit validation check in pipeline/transforms.py before adding loaded_at to ensure the input DataFrame is non-empty and contains no nulls or duplicate rows.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/transforms.py')
text = path.read_text()
old = '''def add_loaded_at(df: pd.DataFrame) -> pd.DataFrame:
    """Append a ``loaded_at`` UTC timestamp column for the gold layer.

    Does not mutate the input DataFrame.

    Args:
        df: Silver-layer DataFrame (validated by SilverSchema).

    Returns:
        New DataFrame with an additional ``loaded_at`` column of dtype
        ``datetime64[ns]``.
    """
    out = df.copy()
    out["loaded_at"] = pd.Timestamp.now(tz="UTC")
    return out
'''
new = '''def add_loaded_at(df: pd.DataFrame) -> pd.DataFrame:
    """Append a ``loaded_at`` UTC timestamp column for the gold layer.

    Does not mutate the input DataFrame.

    Args:
        df: Silver-layer DataFrame (validated by SilverSchema).

    Returns:
        New DataFrame with an additional ``loaded_at`` column of dtype
        ``datetime64[ns]``.
    """
    if df.empty:
        raise ValueError("input DataFrame must not be empty")
    if df.isnull().any().any():
        raise ValueError("input DataFrame must not contain null values")
    if df.duplicated().any():
        raise ValueError("input DataFrame must not contain duplicate rows")

    out = df.copy()
    out["loaded_at"] = pd.Timestamp.now(tz="UTC")
    return out
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** pipeline/03_LoadToWarehouse.py
**Confidence:** 0.88  |  **Risk score:** 2.64
**Evidence:** Data is loaded and used (`df = pd.read_parquet(...)`, then merged and written) but no explicit validation checks are shown before use; there are no asserts, null/duplicate checks, range checks, or validation decorators in the visible file content.

**Suggested fix:** Add an explicit null/duplicate validation check immediately after loading the parquet data and before any merge/write operations

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/03_LoadToWarehouse.py')
text = path.read_text()
old = """    df = pd.read_parquet(gold_path, engine=\"pyarrow\")\n    log.info(\"Gold loaded: %d rows\", len(df))\n\n    engine = _build_engine(env)\n"""
new = """    df = pd.read_parquet(gold_path, engine=\"pyarrow\")\n    log.info(\"Gold loaded: %d rows\", len(df))\n\n    required_cols = [\"material_code\", \"pricing_date\", \"price_value\"]\n    missing_cols = [c for c in required_cols if c not in df.columns]\n    if missing_cols:\n        raise ValueError(f\"Missing required columns: {missing_cols}\")\n    if df[required_cols].isnull().any().any():\n        raise ValueError(\"Validation failed: null values found in required columns\")\n    if df.duplicated(subset=[\"material_code\", \"pricing_date\"]).any():\n        raise ValueError(\"Validation failed: duplicate material_code/pricing_date rows found\")\n\n    engine = _build_engine(env)\n"""
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** Repo root name 'code-polymer' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from code-polymer to a compliant name matching the required pattern, e.g. aud-code-polymer

```
git mv code-polymer aud-code-polymer
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** specs/001-polymer-pricing-etl/contracts/sql-ddl.sql
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** SQL column definitions use snake_case names in CREATE TABLE statements, e.g. material_code, material_description, created_date, pricing_date, price_value, unit_of_measure, currency_code, source_file_name, ingestion_timestamp, loaded_at.

**Suggested fix:** Rename the SQL DDL columns in both CREATE TABLE statements from snake_case to PascalCase while preserving the existing data and constraints.

```
python - <<'PY'
from pathlib import Path
p = Path('specs/001-polymer-pricing-etl/contracts/sql-ddl.sql')
s = p.read_text()
repls = {
    'material_code': 'MaterialCode',
    'material_description': 'MaterialDescription',
    'created_date': 'CreatedDate',
    'pricing_date': 'PricingDate',
    'price_value': 'PriceValue',
    'unit_of_measure': 'UnitOfMeasure',
    'currency_code': 'CurrencyCode',
    'source_file_name': 'SourceFileName',
    'ingestion_timestamp': 'IngestionTimestamp',
    'loaded_at': 'LoadedAt',
}
for old, new in repls.items():
    s = s.replace(old, new)
p.write_text(s)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/CreatePolymerPricingFact.sql
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** SQL column definitions include snake_case names in CREATE TABLE, e.g. pricing_date, price_value, unit_of_measure, currency_code, source_file_name, ingestion_timestamp, loaded_at.

**Suggested fix:** Rename the non-PascalCase SQL columns pricing_date, price_value, unit_of_measure, currency_code, source_file_name, ingestion_timestamp, and loaded_at to PascalCase throughout the table definition and documented MERGE snippet.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreatePolymerPricingFact.sql')
text = p.read_text()
repls = {
    'pricing_date': 'PricingDate',
    'price_value': 'PriceValue',
    'unit_of_measure': 'UnitOfMeasure',
    'currency_code': 'CurrencyCode',
    'source_file_name': 'SourceFileName',
    'ingestion_timestamp': 'IngestionTimestamp',
    'loaded_at': 'LoadedAt',
}
for old, new in repls.items():
    text = text.replace(old, new)
p.write_text(text)
PY
```

## Needs human review (low-confidence findings)

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline/transforms.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'transforms' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline/schemas/pricing_schema.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'pricing_schema' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline/utils/logging_config.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'logging_config' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** specs/001-polymer-pricing-etl/contracts/sql-ddl.sql
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'sql-ddl' is not CamelCase  [no automated fix attached: model reported no violation to fix]

## Compliant checks

103 checks passed. See machine_report.json for the full list.
