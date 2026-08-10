# Compliance Report — fin-code-collateral_management

Run at: 2026-08-10T09:02:26.438109+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\adversarial\fin-code-collateral_management
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 85.9% (67/78 weighted checks)

> 2 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 38
- COMPLIANT: 32
- NON_COMPLIANT: 6
- NOT_APPLICABLE: 20
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 6

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Sample agreement:** 100%
**Evidence:** The file loads and uses data without any explicit quality check first, so it violates DQ-1.  Quoted: 'positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")'

**Suggested fix:** Add an explicit data quality validation step before loading and using the collateral positions CSV.

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
    positions_path = Path("silver/CollateralPositions_validated_20240815.csv")
    if not positions_path.exists():
        raise FileNotFoundError(f"Missing validated input file: {positions_path}")

    positions = pd.read_csv(positions_path)
    required_cols = {"required_collateral", "posted_collateral"}
    missing_cols = required_cols - set(positions.columns)
    if missing_cols:
        raise ValueError(f"Data quality check failed; missing columns: {sorted(missing_cols)}")

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
**Sample agreement:** 100%
**Evidence:** The file hardcodes an API key, so it violates SEC-3.  Quoted: 'COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1"'

**Suggested fix:** Remove the hardcoded API key by reading it from an environment variable with a clear placeholder fallback.

```
python - <<'PY'
from pathlib import Path
path = Path('Collateral_Pipeline/02_ComputeMarginCalls.py')
text = path.read_text()
old = 'import pandas as pd\nimport requests\nfrom pathlib import Path\n'
new = 'import os\nfrom pathlib import Path\n\nimport pandas as pd\nimport requests\n'
text = text.replace(old, new)
text = text.replace('COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1"\n', 'COLLATERAL_VALUATION_API_KEY = os.environ.get("COLLATERAL_VALUATION_API_KEY", "<SET_COLLATERAL_VALUATION_API_KEY>")\n')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Sample agreement:** 100%
**Evidence:** The pipeline job performs data I/O with no logging or durable monitoring record, so it violates OPS-2.  Quoted: 'calls.to_csv("gold/MarginCallReport_20240815.csv", index=False)'

**Suggested fix:** Add a durable logging record for the margin call export before writing the CSV.

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

    calls = positions[positions["margin_call_amount"] > 0]
    calls.to_csv("gold/MarginCallReport_20240815.csv", index=False)
'''
new = '''def main() -> None:
    positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")
    positions["margin_call_amount"] = (
        positions["required_collateral"] - positions["posted_collateral"]
    ).clip(lower=0)

    calls = positions[positions["margin_call_amount"] > 0]
    log_path = Path("gold/MarginCallReport_20240815.log")
    log_path.write_text(f"rows_exported={len(calls)}\noutput_file=gold/MarginCallReport_20240815.csv\n")
    calls.to_csv("gold/MarginCallReport_20240815.csv", index=False)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/CollateralPositions_20240815.csv
**Sample agreement:** 100%
**Evidence:** file name 'CollateralPositions_20240815.csv' ends in an 8-digit date suffix '20240815'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/CollateralPositions_2024-08-15.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/CollateralPositions_20240815.csv bronze/CollateralPositions_2024-08-15.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/MarginCallReport_20240815.csv
**Sample agreement:** 100%
**Evidence:** file name 'MarginCallReport_20240815.csv' ends in an 8-digit date suffix '20240815'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/MarginCallReport_2024-08-15.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/MarginCallReport_20240815.csv gold/MarginCallReport_2024-08-15.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/CollateralPositions_validated_20240815.csv
**Sample agreement:** 100%
**Evidence:** file name 'CollateralPositions_validated_20240815.csv' ends in an 8-digit date suffix '20240815'; the required format is _yyyy-MM-dd; file name stem 'CollateralPositions_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/CollateralPositionsValidated_2024-08-15.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/CollateralPositions_validated_20240815.csv silver/CollateralPositionsValidated_2024-08-15.csv
```

## Checks that passed or did not apply

32 checks passed; 20 did not apply to this repository. See machine_report.json for the full list.
