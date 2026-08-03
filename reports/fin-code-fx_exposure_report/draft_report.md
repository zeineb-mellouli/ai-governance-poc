# Compliance Report — fin-code-fx_exposure_report

Run at: 2026-08-03T13:27:36.123254+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\holistic\fin-code-fx_exposure_report

## Summary

- Total findings evaluated: 67
- COMPLIANT: 24
- NOT_APPLICABLE: 37
- NON_COMPLIANT: 6

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Confidence:** 0.93  |  **Risk score:** 2.79
**Evidence:** Data is loaded and written onward with no validation checks such as asserts, null/duplicate checks, or range checks anywhere in the file.

**Suggested fix:** Add basic data quality validation to the FX ingest step by asserting required columns, rejecting nulls/duplicates, and checking currency codes before writing the staged file.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestFXPositions.py')
text = path.read_text()
text = text.replace('''def main() -> None:
    positions = pd.read_csv("bronze/FXPositions_20240630.csv")

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
    logger.info("Ingested and normalised %d FX position rows", len(processed))
''','''def main() -> None:
    positions = pd.read_csv("bronze/FXPositions_20240630.csv")

    required_columns = {"currency_code"}
    missing = required_columns - set(positions.columns)
    assert not missing, f"Missing required columns: {sorted(missing)}"
    assert not positions["currency_code"].isna().any(), "Null currency_code values found"
    assert not positions.duplicated().any(), "Duplicate FX position rows found"

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()
    assert processed["currency_code"].str.fullmatch(r"[A-Z]{3}").all(), "Invalid currency_code values found"

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
    logger.info("Ingested and normalised %d FX position rows", len(processed))
''')
path.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/02_GenerateExposureReport.py
**Confidence:** 0.91  |  **Risk score:** 2.73
**Evidence:** The file loads data with `pd.read_csv(...)` and then uses it to build the report, but contains no validation checks such as asserts, filters, or explicit quality rules before use.

**Suggested fix:** Add a minimal data-quality validation step after loading the CSV to ensure required columns are present and key fields are non-null before building the report.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/02_GenerateExposureReport.py')
text = path.read_text()
old = '''def main() -> None:
    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")

    report = (
        positions.groupby("currency_code")["notional_local"]
        .sum()
        .reset_index()
        .rename(columns={"notional_local": "total_exposure"})
    )
'''
new = '''def main() -> None:
    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")
    required_columns = {"currency_code", "notional_local"}
    missing = required_columns - set(positions.columns)
    assert not missing, f"Missing required columns: {sorted(missing)}"
    positions = positions.dropna(subset=["currency_code", "notional_local"])

    report = (
        positions.groupby("currency_code")["notional_local"]
        .sum()
        .reset_index()
        .rename(columns={"notional_local": "total_exposure"})
    )
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DM-7 · Star schema / shared output table design [MEDIUM]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Confidence:** 0.88  |  **Risk score:** 1.76
**Evidence:** The file writes a reusable processed output (`staging/FXPositionsProcessed_20240630.csv`) but provides no documented grain/primary key or description of what one row represents beyond a brief module docstring.

**Suggested fix:** Add an explicit documented grain/primary key for the reusable FX positions output so each row’s meaning is clear.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestFXPositions.py')
text = path.read_text()
text = text.replace('''"""Ingest raw FX position data from the custodian feed and prepare it for reporting."""''', '''"""Ingest raw FX position data from the custodian feed and prepare it for reporting.\n\nProcessed output grain: one row per custodian FX position record (unique by the source position identifier, if present, otherwise the full source row).\n"""''')
path.write_text(text)
PY
```

### DM-7 · Star schema / shared output table design [MEDIUM]

**Location:** Treasury_Pipeline/02_GenerateExposureReport.py
**Confidence:** 0.84  |  **Risk score:** 1.68
**Evidence:** The script writes a reusable output `gold/QuarterlyFXExposureReport.csv`, but there is no documented grain/primary key or explanation of what one row represents beyond the brief module docstring.

**Suggested fix:** Document the output grain/primary key in the module docstring so the reusable CSV clearly states that each row represents one currency_code and the file is keyed by currency_code.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/02_GenerateExposureReport.py')
text = path.read_text()
old = '"""Build the quarterly FX exposure report for the Treasury board pack."""\n'
new = '"""Build the quarterly FX exposure report for the Treasury board pack.\n\nOutput grain: one row per currency_code (primary key: currency_code) with the\naggregated total_exposure for that currency.\n"""\n'
if old not in text:
    raise SystemExit('expected docstring not found')
path.write_text(text.replace(old, new, 1))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** Treasury_Pipeline/02_GenerateExposureReport.py
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** File name is `02_GenerateExposureReport.py`, which starts with a digit; the policy flags names starting with a digit as a violation.

**Suggested fix:** Rename the script so it no longer starts with a digit, keeping the same contents and updating any references if needed.

```
git mv Treasury_Pipeline/02_GenerateExposureReport.py Treasury_Pipeline/GenerateExposureReport.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/QuarterlyFXExposureReport.csv
**Confidence:** 0.97  |  **Risk score:** 0.97
**Evidence:** CSV header uses plural column name "total_exposure"? No, the clear violation is the file name pattern: "QuarterlyFXExposureReport.csv" is not CamelCase with an optional yyyy-MM-dd suffix because it lacks the required date suffix format for dataset/pipeline files.

**Suggested fix:** Rename the dataset file to include the required yyyy-MM-dd suffix while preserving the existing content.

```
mv gold/QuarterlyFXExposureReport.csv gold/QuarterlyFXExposureReport_2026-08-03.csv
```

## Compliant checks

24 checks passed. See machine_report.json for the full list.
