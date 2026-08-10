# Compliance Report — fin-code-fx_exposure_report

Run at: 2026-08-10T09:09:00.247802+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\holistic\fin-code-fx_exposure_report
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 90.5% (76/84 weighted checks)

> 2 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 40
- COMPLIANT: 36
- NON_COMPLIANT: 4
- NOT_APPLICABLE: 18
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 4

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Sample agreement:** 100%
**Evidence:** The file loads and writes FX position data without any explicit data quality check in between.  Quoted: 'positions = pd.read_csv("bronze/FXPositions_20240630.csv")'

**Suggested fix:** Add an explicit data quality validation step between reading and writing the FX positions data.

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

    # explicit data quality validation before downstream processing
    required_columns = {"currency_code"}
    missing_columns = required_columns.difference(positions.columns)
    if missing_columns:
        raise ValueError(f"Missing required FX position columns: {sorted(missing_columns)}")
    if positions["currency_code"].isna().any() or (positions["currency_code"].astype(str).str.strip() == "").any():
        raise ValueError("FX position data quality check failed: currency_code contains missing or blank values")

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
    logger.info("Ingested and normalised %d FX position rows", len(processed))
'''
if old not in text:
    raise SystemExit('Target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/02_GenerateExposureReport.py
**Sample agreement:** 100%
**Evidence:** The file loads and uses data further without any explicit quality check first.  Quoted: 'positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")'

**Suggested fix:** Add an explicit data quality validation check before the CSV is used in the FX exposure report pipeline.

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
    missing_columns = required_columns.difference(positions.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if positions[["currency_code", "notional_local"]].isnull().any().any():
        raise ValueError("Data quality check failed: null values found in required columns")

    report = (
        positions.groupby("currency_code")["notional_local"]
        .sum()
        .reset_index()
        .rename(columns={"notional_local": "total_exposure"})
    )
'''
if old not in text:
    raise SystemExit('Target block not found')
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

36 checks passed; 18 did not apply to this repository. See machine_report.json for the full list.
