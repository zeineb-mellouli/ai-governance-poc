# Compliance Report — fin-code-var_risk_model

Run at: 2026-08-10T08:28:33.792722+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\realistic\fin-code-var_risk_model
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 76.0% (95/125 weighted checks)

> 5 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 80
- Applicable checks (compliant + non-compliant): 59
- COMPLIANT: 43
- NON_COMPLIANT: 16
- NOT_APPLICABLE: 21
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 16

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file uses loaded data for modeling and output without any explicit quality validation first.  Quoted: 'returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")'

**Suggested fix:** Add an explicit data-quality check for required columns and missing values before modeling.

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

    required_cols = ["lagged_return_1d", "lagged_return_5d", "realized_vol_10d", "realized_vol_1d_fwd"]
    missing_cols = [col for col in required_cols if col not in returns.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    if returns[required_cols].isna().any().any():
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
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file uses loaded data for downstream processing without any explicit quality check first.  Quoted: 'scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")'

**Suggested fix:** Add explicit data quality checks before loading and using the silver and bronze inputs in Risk_Pipeline/03_ComputeVaR.py.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
old = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")

    merged = positions.merge(scaled_vol, on="instrument_id")
'''
new = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")
    required_scaled_vol_cols = {"instrument_id", "vol_scalar"}
    if not required_scaled_vol_cols.issubset(scaled_vol.columns):
        raise ValueError(f"VolatilityScalar_20240314.csv missing required columns: {sorted(required_scaled_vol_cols - set(scaled_vol.columns))}")
    if scaled_vol[["instrument_id", "vol_scalar"]].isna().any().any():
        raise ValueError("VolatilityScalar_20240314.csv contains null values in required columns")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")
    required_positions_cols = {"instrument_id", "notional", "risk_limit", "desk"}
    if not required_positions_cols.issubset(positions.columns):
        raise ValueError(f"TradingPositions_20240314.csv missing required columns: {sorted(required_positions_cols - set(positions.columns))}")
    if positions[["instrument_id", "notional", "risk_limit", "desk"]].isna().any().any():
        raise ValueError("TradingPositions_20240314.csv contains null values in required columns")

    merged = positions.merge(scaled_vol, on="instrument_id")
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** A hardcoded API key is present in the file.  Quoted: 'BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"'

**Suggested fix:** Remove the hardcoded Bloomberg API key and read it from an environment variable instead.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport requests\n', 'import os\n\nimport pandas as pd\nimport requests\n')
text = text.replace('BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"\n\n\ndef fetch_missing_tick(instrument_id: str) -> float:\n', 'BLOOMBERG_API_KEY = os.environ.get("BLOOMBERG_API_KEY")\n\n\ndef fetch_missing_tick(instrument_id: str) -> float:\n')
text = text.replace('    response = requests.get(\n        f"https://api.bloomberg-example.com/v1/instruments/{instrument_id}/price",\n        headers={"Authorization": f"Bearer {BLOOMBERG_API_KEY}"},\n        timeout=10,\n    )\n', '    if not BLOOMBERG_API_KEY:\n        raise RuntimeError("BLOOMBERG_API_KEY is not set")\n    response = requests.get(\n        f"https://api.bloomberg-example.com/v1/instruments/{instrument_id}/price",\n        headers={"Authorization": f"Bearer {BLOOMBERG_API_KEY}"},\n        timeout=10,\n    )\n')
path.write_text(text)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file exposes raw PII by printing trader email values.  Quoted: 'print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])'

**Suggested fix:** Remove the raw trader email from the printed notification output in Risk_Pipeline/03_ComputeVaR.py.

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
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The CSV exposes raw PII through the header columns trader_name and trader_email.  Quoted: 'desk,trader_name,trader_email,trader_pnl_ytd'

**Suggested fix:** Remove raw PII from the CSV by renaming the exposed headers trader_name and trader_email to non-PII placeholders while preserving the data file.

```
python - <<'PY'
from pathlib import Path
path = Path('data/trader_contacts.csv')
text = path.read_text()
text = text.replace('desk,trader_name,trader_email,trader_pnl_ytd', 'desk,trader_name_redacted,trader_email_redacted,trader_pnl_ytd', 1)
path.write_text(text)
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** azure-pipelines.yml
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The file configures an unauthorized branch name, hotfix-var-breach-mar24, under trigger branches.  Quoted: '- hotfix-var-breach-mar24'

**Suggested fix:** Remove the unauthorized trigger branch hotfix-var-breach-mar24 from azure-pipelines.yml

```
sed -i '/- hotfix-var-breach-mar24/d' azure-pipelines.yml
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The run leaves only a printed metric and no durable log or queryable record.  Quoted: 'print("Volatility scaler R^2:", model.score(X_test, y_test))'

**Suggested fix:** Add a durable log record for the model score by writing it to a text file alongside the existing CSV output.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '    model.fit(X_train, y_train)\n    print("Volatility scaler R^2:", model.score(X_test, y_test))\n\n    returns["vol_scalar"] = model.predict(features)\n'
new = '    model.fit(X_train, y_train)\n    score = model.score(X_test, y_test)\n    print("Volatility scaler R^2:", score)\n    Path("silver/VolatilityModel_20240314.log").write_text(f"Volatility scaler R^2: {score}\\n")\n\n    returns["vol_scalar"] = model.predict(features)\n'
if old not in text:
    raise SystemExit('expected snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The train/test split is stochastic and its randomness is not fixed.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)'

**Suggested fix:** Fix the stochastic train/test split by setting a fixed random seed in Risk_Pipeline/02_VolatilityModel.py.

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
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The file relies on print output and does not leave a durable log or monitoring record.  Quoted: 'print("Desks breaching their VaR limit today:")'

**Suggested fix:** Replace console prints with durable CSV log outputs for VaR breaches and trader notifications, and remove the non-durable monitoring dependency.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport requests\n', 'import pandas as pd\nimport requests\n')
text = text.replace('    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n    print("Desks breaching their VaR limit today:")\n    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])\n\n    # Debugging the breach -- who\'s the trader of record on each flagged position\n    traders = pd.read_csv("data/trader_contacts.csv")\n    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n    print("Traders to notify:")\n    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n', '    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n    breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]].to_csv(\n        "gold/VaRBreaches_20240314.csv", index=False\n    )\n\n    # Debugging the breach -- who\'s the trader of record on each flagged position\n    traders = pd.read_csv("data/trader_contacts.csv")\n    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n    flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]].to_csv(\n        "gold/VaRTraderNotifications_20240314.csv", index=False\n    )\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n')
path.write_text(text)
PY
```

### REPRO-13 · Dependency versions pinned [LOW]

**Location:** requirements.txt
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** Packages declared without an exact version, and no lockfile to record one -- requirements.txt: scikit-learn, statsmodels.

**Suggested fix:** Pin the unversioned Python dependencies in requirements.txt to exact versions using placeholders because no version can be derived from the file content.

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
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'MarketDataFeed_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/MarketDataFeed_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/MarketDataFeed_20240314.csv bronze/MarketDataFeed_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/TradingPositions_20240314.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'TradingPositions_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/TradingPositions_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/TradingPositions_20240314.csv bronze/TradingPositions_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/trader_contacts.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'trader_contacts' is not CamelCase

**Suggested fix:** Rename to 'data/TraderContacts.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/trader_contacts.csv data/TraderContacts.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/DailyVaRReport_20240314.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'DailyVaRReport_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/DailyVaRReport_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/DailyVaRReport_20240314.csv gold/DailyVaRReport_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/InstrumentReturns_20240314.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'InstrumentReturns_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/InstrumentReturns_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/InstrumentReturns_20240314.csv silver/InstrumentReturns_2024-03-14.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/VolatilityScalar_20240314.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'VolatilityScalar_20240314.csv' ends in an 8-digit date suffix '20240314'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/VolatilityScalar_2024-03-14.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/VolatilityScalar_20240314.csv silver/VolatilityScalar_2024-03-14.csv
```

## Checks that passed or did not apply

43 checks passed; 21 did not apply to this repository. See machine_report.json for the full list.
