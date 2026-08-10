# Compliance Report — fin-code-collateral_management

Run at: 2026-08-10T08:16:20.343167+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\adversarial\fin-code-collateral_management
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 88.9% (72/81 weighted checks)

> 2 HIGH-severity violation(s) cap the grade at FAIL.

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

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file loads and uses data without any explicit quality check first, so it violates the policy.  Quoted: 'positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")'

**Suggested fix:** Add an explicit data quality validation step before loading and using the collateral positions data.

```
python - <<'PY'
from pathlib import Path
path = Path('Collateral_Pipeline/02_ComputeMarginCalls.py')
text = path.read_text()
old = '''def main() -> None:
    positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")
    positions["margin_call_amount"] = (
        positions["required_collateral"] - positions["posted_collateral"]
    ).clip(lower=0)
'''
new = '''def main() -> None:
    positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")
    required_cols = {"required_collateral", "posted_collateral"}
    missing = required_cols.difference(positions.columns)
    if missing:
        raise ValueError(f"Data quality validation failed: missing columns {sorted(missing)}")
    if positions["required_collateral"].isna().any() or positions["posted_collateral"].isna().any():
        raise ValueError("Data quality validation failed: null values in collateral columns")
    positions["margin_call_amount"] = (
        positions["required_collateral"] - positions["posted_collateral"]
    ).clip(lower=0)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file hardcodes a credential-like API key literal, which violates the policy.  Quoted: 'COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1"'

**Suggested fix:** Remove the hardcoded API key by reading it from an environment variable with a placeholder fallback.

```
python - <<'PY'
from pathlib import Path
path = Path('Collateral_Pipeline/02_ComputeMarginCalls.py')
text = path.read_text()
old = 'COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1"\n'
new = 'import os\n\nCOLLATERAL_VALUATION_API_KEY = os.getenv("COLLATERAL_VALUATION_API_KEY", "<SET_COLLATERAL_VALUATION_API_KEY>")\n'
if old not in text:
    raise SystemExit('target string not found')
text = text.replace('import pandas as pd\nimport requests\nfrom pathlib import Path\n', 'import os\nimport pandas as pd\nimport requests\nfrom pathlib import Path\n')
text = text.replace(old, new)
path.write_text(text)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/CollateralPositions_20240815.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CollateralPositions_20240815.csv' ends in an 8-digit date suffix '20240815'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/CollateralPositions_2024-08-15.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/CollateralPositions_20240815.csv bronze/CollateralPositions_2024-08-15.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/MarginCallReport_20240815.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'MarginCallReport_20240815.csv' ends in an 8-digit date suffix '20240815'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/MarginCallReport_2024-08-15.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/MarginCallReport_20240815.csv gold/MarginCallReport_2024-08-15.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/CollateralPositions_validated_20240815.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CollateralPositions_validated_20240815.csv' ends in an 8-digit date suffix '20240815'; the required format is _yyyy-MM-dd; file name stem 'CollateralPositions_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/CollateralPositionsValidated_2024-08-15.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/CollateralPositions_validated_20240815.csv silver/CollateralPositionsValidated_2024-08-15.csv
```

## Checks that passed or did not apply

34 checks passed; 19 did not apply to this repository. See machine_report.json for the full list.
