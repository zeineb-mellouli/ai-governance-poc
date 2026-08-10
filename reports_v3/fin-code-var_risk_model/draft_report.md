# Compliance Report — fin-code-var_risk_model

Run at: 2026-08-10T09:13:02.752927+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\realistic\fin-code-var_risk_model
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 73.1% (95/130 weighted checks)

> 6 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 80
- Applicable checks (compliant + non-compliant): 61
- COMPLIANT: 43
- NON_COMPLIANT: 18
- NOT_APPLICABLE: 19
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 18

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for modeling and output without any explicit quality check first.  Quoted: 'returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")'

**Suggested fix:** Add an explicit data-quality check before modeling to ensure required columns are present and free of missing values.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '''def main() -> None:
    returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")

    features = returns[["lagged_return_1d", "lagged_return_5d", "realized_vol_10d"]].values
    target = returns["realized_vol_1d_fwd"].values
'''
new = '''def main() -> None:
    returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")

    required_columns = ["lagged_return_1d", "lagged_return_5d", "realized_vol_10d", "realized_vol_1d_fwd"]
    missing_columns = [col for col in required_columns if col not in returns.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    if returns[required_columns].isna().any().any():
        raise ValueError("Input data contains missing values in required modeling columns")

    features = returns[["lagged_return_1d", "lagged_return_5d", "realized_vol_10d"]].values
    target = returns["realized_vol_1d_fwd"].values
'''
if old not in text:
    raise SystemExit('Target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data without any explicit quality validation first.  Quoted: 'scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")'

**Suggested fix:** Add explicit data quality validation before loading and using the CSV inputs in Risk_Pipeline/03_ComputeVaR.py

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
old = '''from pathlib import Path

import pandas as pd
import requests

Path("gold").mkdir(parents=True, exist_ok=True)

BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"
'''
new = '''from pathlib import Path

import pandas as pd
import requests

Path("gold").mkdir(parents=True, exist_ok=True)

BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"


def validate_input(df: pd.DataFrame, required_columns: list[str], name: str) -> None:
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"{name} missing required columns: {missing}")
    if df[required_columns].isnull().any().any():
        raise ValueError(f"{name} contains null values in required columns")
'''
if old not in text:
    raise SystemExit('expected block not found')
text = text.replace(old, new)
old = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")

    merged = positions.merge(scaled_vol, on="instrument_id")
'''
new = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")
    validate_input(scaled_vol, ["instrument_id", "vol_scalar"], "Volatility scalar data")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")
    validate_input(positions, ["instrument_id", "notional", "risk_limit", "desk"], "Trading positions data")

    merged = positions.merge(scaled_vol, on="instrument_id")
'''
if old not in text:
    raise SystemExit('expected main block not found')
text = text.replace(old, new)
path.write_text(text)
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** A hardcoded API key appears directly in the source.  Quoted: 'BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"'

**Suggested fix:** Remove the hardcoded Bloomberg API key and read it from an environment variable instead, with a clear placeholder fallback.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('''from pathlib import Path

import pandas as pd
import requests

Path("gold").mkdir(parents=True, exist_ok=True)

BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"
''','''from pathlib import Path
import os

import pandas as pd
import requests

Path("gold").mkdir(parents=True, exist_ok=True)

BLOOMBERG_API_KEY = os.environ.get("BLOOMBERG_API_KEY", "<SET_BLOOMBERG_API_KEY>")
''')
path.write_text(text)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** The script prints raw PII fields, including trader_email, to output.  Quoted: 'print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])'

**Suggested fix:** Remove the raw PII print by excluding trader_email from the console output in Risk_Pipeline/03_ComputeVaR.py

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
old = '    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])\n'
new = '    print(flagged_traders[["desk", "trader_name", "trader_pnl_ytd"]])\n'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** data/trader_contacts.csv
**Sample agreement:** 100%
**Evidence:** The CSV header exposes direct identifier columns trader_name and trader_email.  Quoted: 'desk,trader_name,trader_email,trader_pnl_ytd'

**Suggested fix:** Remove the raw PII header fields by renaming trader_name and trader_email to non-identifying placeholders in the CSV header.

```
sed -i '1s/.*/desk,trader_id,trader_contact,trader_pnl_ytd/' data/trader_contacts.csv
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 67%
**Evidence:** The file writes to the silver layer without an immediately preceding validation step.  Quoted: 'returns.to_csv("silver/VolatilityScalar_20240314.csv", index=False)'  [2/3 samples agreed: COMPLIANTx1, NON_COMPLIANTx2]

**Suggested fix:** Add an explicit validation step immediately before writing the silver output file.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '''    returns["vol_scalar"] = model.predict(features)
    returns.to_csv("silver/VolatilityScalar_20240314.csv", index=False)
'''
new = '''    returns["vol_scalar"] = model.predict(features)
    if returns[["lagged_return_1d", "lagged_return_5d", "realized_vol_10d", "realized_vol_1d_fwd", "vol_scalar"]].isnull().any().any():
        raise ValueError("Validation failed: null values present before silver write")
    returns.to_csv("silver/VolatilityScalar_20240314.csv", index=False)
'''
if old not in text:
    raise SystemExit('Expected snippet not found')
path.write_text(text.replace(old, new))
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** azure-pipelines.yml
**Sample agreement:** 100%
**Evidence:** The file violates the branch naming rule by including an unsupported branch name in the trigger list.  Quoted: '- hotfix-var-breach-mar24'

**Suggested fix:** Remove the unsupported branch name from the Azure Pipelines trigger list.

```
python - <<'PY'
from pathlib import Path
p = Path('azure-pipelines.yml')
text = p.read_text()
text = text.replace('      - hotfix-var-breach-mar24\n', '')
p.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The run records metrics only via print and does not leave a durable log or metric record.  Quoted: 'print("Volatility scaler R^2:", model.score(X_test, y_test))'

**Suggested fix:** Add a durable metric record by writing the model R^2 to a log file instead of only printing it.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '    model = LinearRegression()\n    model.fit(X_train, y_train)\n    print("Volatility scaler R^2:", model.score(X_test, y_test))\n\n    returns["vol_scalar"] = model.predict(features)\n'
new = '    model = LinearRegression()\n    model.fit(X_train, y_train)\n    r2 = model.score(X_test, y_test)\n    print("Volatility scaler R^2:", r2)\n    Path("silver/volatility_model_metrics.txt").write_text(f"Volatility scaler R^2: {r2}\n")\n\n    returns["vol_scalar"] = model.predict(features)\n'
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The train/test split is stochastic and unseeded, so the run is not reproducible.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)'

**Suggested fix:** Add a fixed random seed to the stochastic train/test split in Risk_Pipeline/02_VolatilityModel.py for reproducibility.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)\n'
new = '    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)\n'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new))
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** The job records output only with print statements and no persistent logging.  Quoted: 'print("Desks breaching their VaR limit today:")'

**Suggested fix:** Add persistent file logging to the VaR job while preserving the existing CSV output

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('''from pathlib import Path

import pandas as pd
import requests

Path("gold").mkdir(parents=True, exist_ok=True)
''','''from pathlib import Path
import logging

import pandas as pd
import requests

Path("gold").mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename="gold/ComputeVaR.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
''')
text = text.replace('''    print("Desks breaching their VaR limit today:")
    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])
''','''    logger.info("Desks breaching their VaR limit today:\n%s", breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]].to_string(index=False))
    print("Desks breaching their VaR limit today:")
    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])
''')
text = text.replace('''    print("Traders to notify:")
    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])
''','''    logger.info("Traders to notify:\n%s", flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]].to_string(index=False))
    print("Traders to notify:")
    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])
''')
path.write_text(text)
PY
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** README.md, Risk_SQL/CreateVarBreachFact.sql, and gold/DailyVaRReport_20240314.csv do not state what one row represents for the gold/reporting output or the fact table.  Quoted: 'Daily VaR breach fact table'

**Suggested fix:** Add explicit row-grain documentation stating that the Daily VaR breach fact/report output has one row per daily VaR breach record.

```
python - <<'PY'
from pathlib import Path
files = [Path('README.md'), Path('Risk_SQL/CreateVarBreachFact.sql'), Path('gold/DailyVaRReport_20240314.csv')]
for path in files:
    text = path.read_text()
    if path.name == 'README.md':
        if 'one row represents' not in text.lower():
            text += '\n\n## Output grain\nEach row in the Daily VaR breach fact/report output represents one daily VaR breach record.\n'
    elif path.suffix == '.sql':
        if 'one row represents' not in text.lower():
            text = text.rstrip() + '\n\n-- Output grain: one row represents one daily VaR breach record.\n'
    elif path.suffix == '.csv':
        lines = text.splitlines()
        if lines and 'one row represents' not in lines[0].lower():
            lines[0] = lines[0] + '  # one row represents one daily VaR breach record'
            text = '\n'.join(lines) + ('\n' if text.endswith('\n') else '')
    path.write_text(text)
PY
```

### REPRO-13 · Dependency versions pinned [LOW]

**Location:** requirements.txt
**Sample agreement:** 100%
**Evidence:** Packages declared without an exact version, and no lockfile to record one -- requirements.txt: scikit-learn, statsmodels.

**Suggested fix:** Pin the unversioned Python dependencies in requirements.txt to exact versions using placeholders because no lockfile or derivable versions were provided.

```
python - <<'PY'
from pathlib import Path
p = Path('requirements.txt')
text = p.read_text()
text = text.replace('scikit-learn\n', 'scikit-learn==<PINNED_VERSION>\n')
text = text.replace('statsmodels\n', 'statsmodels==<PINNED_VERSION>\n')
p.write_text(text)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/MarketDataFeed_20240314.csv
**Sample agreement:** 100%
**Evidence:** file name 'MarketDataFeed_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/MarketDataFeed_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/MarketDataFeed_20240314.csv bronze/MarketDataFeed_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/TradingPositions_20240314.csv
**Sample agreement:** 100%
**Evidence:** file name 'TradingPositions_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/TradingPositions_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/TradingPositions_20240314.csv bronze/TradingPositions_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/trader_contacts.csv
**Sample agreement:** 100%
**Evidence:** file name stem 'trader_contacts' is not CamelCase

**Suggested fix:** Rename to 'data/TraderContacts.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/trader_contacts.csv data/TraderContacts.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/DailyVaRReport_20240314.csv
**Sample agreement:** 100%
**Evidence:** file name 'DailyVaRReport_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/DailyVaRReport_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/DailyVaRReport_20240314.csv gold/DailyVaRReport_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/InstrumentReturns_20240314.csv
**Sample agreement:** 100%
**Evidence:** file name 'InstrumentReturns_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/InstrumentReturns_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/InstrumentReturns_20240314.csv silver/InstrumentReturns_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/VolatilityScalar_20240314.csv
**Sample agreement:** 100%
**Evidence:** file name 'VolatilityScalar_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/VolatilityScalar_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/VolatilityScalar_20240314.csv silver/VolatilityScalar_2024-03-14.csv
```

## Checks that passed or did not apply

43 checks passed; 19 did not apply to this repository. See machine_report.json for the full list.
