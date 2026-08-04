# Compliance Report — fin-code-fx_exposure_report

Run at: 2026-08-04T12:19:59.965978+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\holistic\fin-code-fx_exposure_report

## Summary

- Total findings evaluated: 55
- COMPLIANT: 25
- NON_COMPLIANT: 5
- NOT_APPLICABLE: 25

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/02_GenerateExposureReport.py
**Confidence:** 0.93  |  **Risk score:** 2.79
**Evidence:** Data is loaded with `pd.read_csv("staging/FXPositionsProcessed_20240630.csv")` and then used to build the report, but there are no validation checks (no assert/raise/filter or validation library calls) anywhere in the file.

**Suggested fix:** Add a minimal validation check to ensure the loaded FX positions data is not empty before building the report.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/02_GenerateExposureReport.py')
text = path.read_text()
old = '    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")\n\n    report = (\n'
new = '    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")\n    assert not positions.empty, "FX positions data must not be empty"\n\n    report = (\n'
if old not in text:
    raise SystemExit('target text not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestFXPositions.py
**Confidence:** 0.91  |  **Risk score:** 2.73
**Evidence:** Data is loaded with `pd.read_csv("bronze/FXPositions_20240630.csv")` and then used/written out with no validation checks such as asserts, null/duplicate checks, or range checks anywhere in the file.

**Suggested fix:** Add a minimal null/duplicate validation check after loading FX positions before processing them.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestFXPositions.py')
text = path.read_text()
old = '''def main() -> None:
    positions = pd.read_csv("bronze/FXPositions_20240630.csv")

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
'''
new = '''def main() -> None:
    positions = pd.read_csv("bronze/FXPositions_20240630.csv")
    assert not positions.isnull().any().any(), "FX positions contain null values"
    assert not positions.duplicated().any(), "FX positions contain duplicate rows"

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
'''
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** (repository-level)
**Confidence:** 0.99  |  **Risk score:** 1.98
**Evidence:** requirements.txt pins pandas==2.1.4, pyyaml==6.0.1, and azure-identity==1.15.0, so dependency pinning is complete. However, the repository contains processing code that overwrites raw-derived outputs in place: Treasury_Pipeline/01_IngestFXPositions.py reads bronze/FXPositions_20240630.csv and writes a transformed version to staging/FXPositionsProcessed_20240630.csv, and Treasury_Pipeline/02_GenerateExposureReport.py writes the aggregated report to gold/QuarterlyFXExposureReport.csv. More importantly for reproducibility, there is no stochastic step anywhere in the repository, so no seed issue arises; the non-compliance is due to the repository-level requirement that raw source files be directly overwritten by processing code being violated by the pipeline's write pattern as implemented.

**Suggested fix:** Update the pipeline to write processed and report outputs to new files without overwriting any raw-derived source files in place.

```
python - <<'PY'
from pathlib import Path
files = [Path('Treasury_Pipeline/01_IngestFXPositions.py'), Path('Treasury_Pipeline/02_GenerateExposureReport.py')]
repls = {
    'staging/FXPositionsProcessed_20240630.csv': 'staging/FXPositionsProcessed_20240630.csv',
    'gold/QuarterlyFXExposureReport.csv': 'gold/QuarterlyFXExposureReport.csv',
}
for path in files:
    text = path.read_text()
    # No-op placeholder: inspect and manually ensure writes use new output paths or copies, not in-place overwrites.
    path.write_text(text)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/FXPositions_20240630.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'FXPositions_20240630.csv' ends in an 8-digit date suffix '20240630'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename the CSV file to use the required _yyyy-MM-dd suffix format.

```
git mv bronze/FXPositions_20240630.csv bronze/FXPositions_2024-06-30.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** staging/FXPositionsProcessed_20240630.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'FXPositionsProcessed_20240630.csv' ends in an 8-digit date suffix '20240630'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename the CSV columns to snake_case singular nouns by changing the header row only.

```
sed -i '1s/.*/position_id,currency_code,notional_local,as_of_date/' staging/FXPositionsProcessed_20240630.csv
```

## Compliant checks

25 checks passed. See machine_report.json for the full list.
