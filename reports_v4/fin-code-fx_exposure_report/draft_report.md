# Compliance Report — fin-code-fx_exposure_report

Run at: 2026-08-10T13:23:45.346456+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\holistic\fin-code-fx_exposure_report
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 86.9%** (73/84 weighted checks) — 3 high, 0 medium, 2 low severity violations

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 40
- COMPLIANT: 35
- NON_COMPLIANT: 5
- NOT_APPLICABLE: 18
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 5

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Sample agreement:** 100%
**Evidence:** The file loads and writes data without any intervening quality check, so it violates the validation requirement.  Quoted: 'positions = pd.read_csv("bronze/FXPositions_20240630.csv")'

**Suggested fix:** Add a data quality validation check between reading and writing the FX positions data.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestFXPositions.py')
text = path.read_text()
old = '''def main() -> None:
    positions = pd.read_csv("bronze/FXPositions_20240630.csv")

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
    logger.info("Ingested and normalised %d FX position rows", len(processed))
'''
new = '''def main() -> None:
    positions = pd.read_csv("bronze/FXPositions_20240630.csv")

    required_columns = {"currency_code"}
    missing_columns = required_columns - set(positions.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if positions["currency_code"].isna().any() or (positions["currency_code"].astype(str).str.strip() == "").any():
        raise ValueError("currency_code contains missing or blank values")

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
    logger.info("Ingested and normalised %d FX position rows", len(processed))
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Sample agreement:** 100%
**Evidence:** The file writes bronze data into the middle layer without a validation step immediately before the write.  Quoted: 'processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)'

**Suggested fix:** Add an explicit validation step immediately before writing the staging output to satisfy the bronze-to-silver medallion boundary.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestFXPositions.py')
text = path.read_text()
old = '''    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
'''
new = '''    processed["currency_code"] = processed["currency_code"].str.upper()

    # validation step before promoting bronze data into staging/silver
    if processed["currency_code"].isna().any():
        raise ValueError("currency_code validation failed: missing values present")

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
'''
if old not in text:
    raise SystemExit('Expected code block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/02_GenerateExposureReport.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it for aggregation and output without any explicit quality validation first.  Quoted: 'positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")'

**Suggested fix:** Add an explicit data quality validation step before aggregating the loaded positions data.

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
    missing_columns = required_columns - set(positions.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if positions["currency_code"].isna().any() or positions["notional_local"].isna().any():
        raise ValueError("Data quality validation failed: null values found in required columns")

    report = (
        positions.groupby("currency_code")["notional_local"]
        .sum()
        .reset_index()
        .rename(columns={"notional_local": "total_exposure"})
    )
'''
if old not in text:
    raise SystemExit('Expected block not found')
path.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/FXPositions_20240630.csv
**Sample agreement:** 100%
**Evidence:** file name 'FXPositions_20240630.csv' ends in an 8-digit date suffix '20240630'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/FXPositions_2024-06-30.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/FXPositions_20240630.csv bronze/FXPositions_2024-06-30.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** staging/FXPositionsProcessed_20240630.csv
**Sample agreement:** 100%
**Evidence:** file name 'FXPositionsProcessed_20240630.csv' ends in an 8-digit date suffix '20240630'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'staging/FXPositionsProcessed_2024-06-30.csv' to satisfy the NAM-5 naming grammar.

```
git mv staging/FXPositionsProcessed_20240630.csv staging/FXPositionsProcessed_2024-06-30.csv
```

## Checks that passed or did not apply

35 checks passed; 18 did not apply to this repository. See machine_report.json for the full list.
