# Compliance Report — fin-code-fx_exposure_report

Run at: 2026-08-11T12:41:44.451522+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\holistic\fin-code-fx_exposure_report
Self-consistency samples (k): 1
> At k=1 no disagreement is measurable, so every confidence is 1.0 and the remediation confidence gate does not fire.

## Summary

**Weighted pass rate: 87.4%** (76/87 weighted checks) — 3 high, 0 medium, 2 low severity violations

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 41
- COMPLIANT: 36
- NON_COMPLIANT: 5
- NOT_APPLICABLE: 17
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 5

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Sample agreement:** 100%
**Evidence:** The file writes processed data to staging without any explicit quality check beforehand.  Quoted: 'processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)'

**Suggested fix:** Add an explicit data quality validation check before writing the processed FX positions to staging.

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

    # basic data quality validation before staging output
    if processed.empty:
        raise ValueError("FX positions validation failed: no rows to process")
    if processed["currency_code"].isna().any() or (processed["currency_code"].str.strip() == "").any():
        raise ValueError("FX positions validation failed: missing currency_code values")

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
**Evidence:** The file enters the middle layer from bronze without an immediate validation step.  Quoted: 'processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)'

**Suggested fix:** Add an immediate validation step before writing the bronze-derived FX positions into staging.

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
new = '''    # validate bronze data before promoting it to staging
    required_columns = {"currency_code"}
    missing = required_columns - set(positions.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
'''
if old not in text:
    raise SystemExit('Expected block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/02_GenerateExposureReport.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any explicit quality check first.  Quoted: 'positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")'

**Suggested fix:** Add an explicit data quality validation check immediately after loading the positions CSV before any downstream use.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/02_GenerateExposureReport.py')
text = path.read_text()
old = 'def main() -> None:\n    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")\n\n    report = (\n'
new = 'def main() -> None:\n    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")\n    if positions.empty:\n        raise ValueError("FX positions data quality check failed: input file contains no rows")\n\n    report = (\n'
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

36 checks passed; 17 did not apply to this repository. See machine_report.json for the full list.
