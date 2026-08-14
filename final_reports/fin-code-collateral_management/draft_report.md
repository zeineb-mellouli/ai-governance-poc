# Compliance Report — fin-code-collateral_management

Run at: 2026-08-13T12:06:52.206959+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\adversarial\fin-code-collateral_management
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 86.4%** (70/81 weighted checks) — 2 high, 1 medium, 3 low severity violations

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 39
- COMPLIANT: 33
- NON_COMPLIANT: 6
- NOT_APPLICABLE: 19
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 6

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any explicit quality check first.  Quoted: 'positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")'

**Suggested fix:** Add an explicit data quality validation step before using the loaded positions data.

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
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if positions[["required_collateral", "posted_collateral"]].isnull().any().any():
        raise ValueError("Input collateral positions contain null values in required fields")
    positions["margin_call_amount"] = (
        positions["required_collateral"] - positions["posted_collateral"]
    ).clip(lower=0)
'''
if old not in text:
    raise SystemExit('Target block not found')
path.write_text(text.replace(old, new))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Sample agreement:** 100%
**Evidence:** A hardcoded API key is present in the file.  Quoted: 'COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1"'

**Suggested fix:** Remove the hardcoded API key by replacing it with an environment-variable lookup and a clear placeholder fallback.

```
python - <<'PY'
from pathlib import Path
path = Path('Collateral_Pipeline/02_ComputeMarginCalls.py')
text = path.read_text()
old = 'import pandas as pd\nimport requests\nfrom pathlib import Path\n'
new = 'import os\nfrom pathlib import Path\n\nimport pandas as pd\nimport requests\n'
text = text.replace(old, new)
text = text.replace('COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1"\n', 'COLLATERAL_VALUATION_API_KEY = os.getenv("COLLATERAL_VALUATION_API_KEY", "<SET_COLLATERAL_VALUATION_API_KEY>")\n')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Sample agreement:** 100%
**Evidence:** The pipeline job performs file I/O with no logging or monitoring mechanism present.  Quoted: 'import pandas as pd'

**Suggested fix:** Add minimal logging to the pipeline job so file I/O and processing steps are recorded.

```
python - <<'PY'
from pathlib import Path
path = Path('Collateral_Pipeline/02_ComputeMarginCalls.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport requests\nfrom pathlib import Path\n', 'import logging\nimport pandas as pd\nimport requests\nfrom pathlib import Path\n\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n')
text = text.replace('def fetch_valuation(counterparty_id: str) -> float:\n', 'def fetch_valuation(counterparty_id: str) -> float:\n    logger.info("Fetching valuation for counterparty_id=%s", counterparty_id)\n')
text = text.replace('def main() -> None:\n    positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")\n', 'def main() -> None:\n    logger.info("Reading collateral positions input file")\n    positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")\n')
text = text.replace('    calls = positions[positions["margin_call_amount"] > 0]\n    calls.to_csv("gold/MarginCallReport_20240815.csv", index=False)\n', '    calls = positions[positions["margin_call_amount"] > 0]\n    logger.info("Writing margin call report with %d rows", len(calls))\n    calls.to_csv("gold/MarginCallReport_20240815.csv", index=False)\n')
path.write_text(text)
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

33 checks passed; 19 did not apply to this repository. See machine_report.json for the full list.
