# Compliance Report — fin-code-fx_exposure_report

Run at: 2026-08-13T12:14:29.487402+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\holistic\fin-code-fx_exposure_report
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 86.4%** (70/81 weighted checks) — 3 high, 0 medium, 2 low severity violations

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 39
- COMPLIANT: 34
- NON_COMPLIANT: 5
- NOT_APPLICABLE: 19
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 5

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Sample agreement:** 100%
**Evidence:** The file loads and writes data without any intervening quality check, so it violates the validation requirement.  Quoted: 'processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)'

**Suggested fix:** Add a minimal data quality validation check before writing the processed FX positions CSV.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestFXPositions.py')
text = path.read_text()
old = '''    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
'''
new = '''    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    # basic data quality validation: require currency codes and no missing values
    if processed["currency_code"].isna().any() or processed.isna().any().any():
        raise ValueError("Data quality validation failed for FX positions")

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
'''
if old not in text:
    raise SystemExit('Expected block not found')
path.write_text(text.replace(old, new))
PY
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Sample agreement:** 100%
**Evidence:** The file writes bronze-sourced data into the middle layer without a validation step immediately before the write.  Quoted: 'processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)'

**Suggested fix:** Add an explicit validation step immediately before writing bronze-sourced FX positions to the staging layer.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestFXPositions.py')
text = path.read_text()
old = '''    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
'''
new = '''    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    # validate the transformed data before promoting it to staging
    if processed["currency_code"].isna().any() or (processed["currency_code"].str.len() != 3).any():
        raise ValueError("Invalid FX position currency_code values after normalization")

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
**Evidence:** The file loads data and uses it in an aggregation without any quality check first.  Quoted: 'positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")'

**Suggested fix:** Add a basic data quality validation check immediately after loading the positions CSV before aggregation.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/02_GenerateExposureReport.py')
text = path.read_text()
old = '    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")\n\n    report = (\n'
new = '    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")\n    required_columns = {"currency_code", "notional_local"}\n    missing_columns = required_columns - set(positions.columns)\n    if missing_columns:\n        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")\n    if positions[["currency_code", "notional_local"]].isnull().any().any():\n        raise ValueError("Data quality check failed: null values found in required columns")\n\n    report = (\n'
if old not in text:
    raise SystemExit('Expected pattern not found')
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

34 checks passed; 19 did not apply to this repository. See machine_report.json for the full list.
