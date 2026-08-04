# Compliance Report — fin-code-collateral_management

Run at: 2026-08-03T13:24:42.949141+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\adversarial\fin-code-collateral_management

## Summary

- Total findings evaluated: 73
- COMPLIANT: 29
- NOT_APPLICABLE: 39
- NON_COMPLIANT: 5

## Run errors (partial failures)

- Remediation Agent failed on ARCH-12 (Collateral_Pipeline/02_ComputeMarginCalls.py): Error code: 400 - {'error': {'message': "The response was filtered due to the prompt triggering Azure OpenAI's content management policy. Please modify your prompt and retry. To learn more about our content filtering policies please read our documentation: https://go.microsoft.com/fwlink/?linkid=2198766", 'type': None, 'param': 'prompt', 'code': 'content_filter', 'status': 400, 'innererror': {'code': 'ResponsibleAIPolicyViolation', 'content_filter_result': {'hate': {'filtered': False, 'severity': 'safe'}, 'indirect_attack': {'detected': False, 'filtered': False}, 'jailbreak': {'detected': True, 'filtered': True}, 'self_harm': {'filtered': False, 'severity': 'safe'}, 'sexual': {'filtered': False, 'severity': 'safe'}, 'violence': {'filtered': False, 'severity': 'safe'}}}}}

## Non-compliant findings

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Reads from silver/CollateralPositions_validated_20240815.csv and writes directly to gold/MarginCallReport_20240815.csv; no bronze/silver/gold validation or intermediate quality gate is shown before the gold write.

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Hardcoded credential-like value assigned directly in code: COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1".

**Suggested fix:** Remove the hardcoded API key and read the valuation credential from an environment variable instead.

```
python - <<'PY'
from pathlib import Path
path = Path('Collateral_Pipeline/02_ComputeMarginCalls.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport requests\nfrom pathlib import Path\n', 'import os\n\nimport pandas as pd\nimport requests\nfrom pathlib import Path\n')
text = text.replace('COLLATERAL_VALUATION_API_KEY = "cva-9f21b7d3-prod-6a48e0c1"\n\n\n', 'COLLATERAL_VALUATION_API_KEY = os.environ["COLLATERAL_VALUATION_API_KEY"]\n\n\n')
path.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Confidence:** 0.98  |  **Risk score:** 2.94
**Evidence:** Data is loaded with pd.read_csv("silver/CollateralPositions_validated_20240815.csv") and then used to compute/write output, but there are no asserts, raises, expectation decorators, or other validation checks in the file.

**Suggested fix:** Add a minimal data validation check after loading the CSV to ensure required columns are present and non-null before computing margin calls.

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
    missing = required_cols - set(positions.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if positions[list(required_cols)].isna().any().any():
        raise ValueError("Null values found in required collateral fields")
    positions["margin_call_amount"] = (
        positions["required_collateral"] - positions["posted_collateral"]
    ).clip(lower=0)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Collateral_Pipeline/02_ComputeMarginCalls.py
**Confidence:** 0.90  |  **Risk score:** 1.8
**Evidence:** The module has no logging setup or logger calls and relies on direct execution without start/end or error logging.

**Suggested fix:** Add basic module logging with start/end and error reporting around the main margin-call computation.

```
python - <<'PY'
from pathlib import Path
p = Path('Collateral_Pipeline/02_ComputeMarginCalls.py')
s = p.read_text()
s = s.replace('''import pandas as pd
import requests
from pathlib import Path
''', '''import logging
import pandas as pd
import requests
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)
''')
s = s.replace('''def main() -> None:
    positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")
    positions["margin_call_amount"] = (
        positions["required_collateral"] - positions["posted_collateral"]
    ).clip(lower=0)

    calls = positions[positions["margin_call_amount"] > 0]
    calls.to_csv("gold/MarginCallReport_20240815.csv", index=False)
''', '''def main() -> None:
    logger.info("Starting margin call computation")
    try:
        positions = pd.read_csv("silver/CollateralPositions_validated_20240815.csv")
        positions["margin_call_amount"] = (
            positions["required_collateral"] - positions["posted_collateral"]
        ).clip(lower=0)

        calls = positions[positions["margin_call_amount"] > 0]
        calls.to_csv("gold/MarginCallReport_20240815.csv", index=False)
        logger.info("Completed margin call computation: %d calls written", len(calls))
    except Exception:
        logger.exception("Margin call computation failed")
        raise
''')
p.write_text(s)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/CollateralPositions_20240815.csv
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** CSV filename "CollateralPositions_20240815.csv" uses an underscore date suffix instead of the required CamelCase_yyyy-MM-dd pattern; columns also use snake_case headers like "counterparty_id" and "required_collateral".

**Suggested fix:** Rename the CSV to use the required CamelCase_yyyy-MM-dd naming pattern and update the headers to CamelCase.

```
mv bronze/CollateralPositions_20240815.csv bronze/CollateralPositions_2024-08-15.csv && printf 'CounterpartyId,RequiredCollateral,PostedCollateral\n' > bronze/CollateralPositions_2024-08-15.csv
```

## Compliant checks

29 checks passed. See machine_report.json for the full list.
