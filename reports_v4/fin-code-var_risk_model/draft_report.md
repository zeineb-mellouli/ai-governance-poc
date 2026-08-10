# Compliance Report — fin-code-var_risk_model

Run at: 2026-08-10T13:27:50.725835+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\realistic\fin-code-var_risk_model
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 75.4%** (92/122 weighted checks) — 5 high, 4 medium, 7 low severity violations

- Checks evaluated: 80
- Applicable checks (compliant + non-compliant): 58
- COMPLIANT: 42
- NON_COMPLIANT: 16
- NOT_APPLICABLE: 22
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 16

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
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
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any explicit quality validation in between.  Quoted: 'scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")'

**Suggested fix:** Add explicit data quality validation checks before using the loaded CSV inputs in Risk_Pipeline/03_ComputeVaR.py.

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
    if scaled_vol.empty or scaled_vol[["instrument_id", "vol_scalar"]].isnull().any().any():
        raise ValueError("VolatilityScalar_20240314.csv failed data quality validation")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")
    required_cols = ["instrument_id", "desk", "notional", "risk_limit"]
    if positions.empty or positions[required_cols].isnull().any().any():
        raise ValueError("TradingPositions_20240314.csv failed data quality validation")

    merged = positions.merge(scaled_vol, on="instrument_id")
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
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
**Sample agreement:** 100%
**Evidence:** Raw PII is exposed by printing trader email information.  Quoted: 'print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])'

**Suggested fix:** Remove the raw trader email from the debug print so the script no longer outputs PII.

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
**Evidence:** The CSV header exposes a direct identifier column, trader_email, which violates the no raw PII rule.  Quoted: 'desk,trader_name,trader_email,trader_pnl_ytd'

**Suggested fix:** Rename the exposed PII header trader_email to a non-PII placeholder in the CSV header line only.

```
sed -i '1s/trader_email/trader_contact/' data/trader_contacts.csv
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** azure-pipelines.yml
**Sample agreement:** 100%
**Evidence:** The trigger branch list includes an invalid branch name, so the branch standard is violated.  Quoted: '- hotfix-var-breach-mar24'

**Suggested fix:** Remove the invalid trigger branch entry from azure-pipelines.yml so only valid branches remain.

```
python - <<'PY'
from pathlib import Path
path = Path('azure-pipelines.yml')
text = path.read_text()
text = text.replace('      - hotfix-var-breach-mar24\n', '')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The run records its metric only with print and does not leave a durable log or metric record.  Quoted: 'print("Volatility scaler R^2:", model.score(X_test, y_test))'

**Suggested fix:** Add a durable metric record by writing the model R^2 to a log file instead of only printing it.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '    model = LinearRegression()\n    model.fit(X_train, y_train)\n    print("Volatility scaler R^2:", model.score(X_test, y_test))\n\n    returns["vol_scalar"] = model.predict(features)\n'
new = '    model = LinearRegression()\n    model.fit(X_train, y_train)\n    r2 = model.score(X_test, y_test)\n    print("Volatility scaler R^2:", r2)\n    Path("silver/volatility_model_metrics.txt").write_text(f"Volatility scaler R^2: {r2}\\n")\n\n    returns["vol_scalar"] = model.predict(features)\n'
if old not in text:
    raise SystemExit('Expected code block not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The stochastic split is not seeded anywhere in the file, so the run is not reproducible.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)'

**Suggested fix:** Add a fixed random seed to the stochastic train/test split in Risk_Pipeline/02_VolatilityModel.py for reproducible runs.

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
**Evidence:** The job relies on print statements and does not leave a durable log record.  Quoted: 'print("Desks breaching their VaR limit today:")'

**Suggested fix:** Replace console prints with durable file logging to a text log in gold while preserving the VaR CSV output.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('''from pathlib import Path\n\nimport pandas as pd\nimport requests\n''', '''from pathlib import Path\n\nimport pandas as pd\nimport requests\n\nLOG_PATH = Path("gold/DailyVaRReport_20240314.log")\n''')
text = text.replace('''    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n    print("Desks breaching their VaR limit today:")\n    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])\n\n    # Debugging the breach -- who's the trader of record on each flagged position\n    traders = pd.read_csv("data/trader_contacts.csv")\n    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n    print("Traders to notify:")\n    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n''', '''    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n    log_lines = ["Desks breaching their VaR limit today:"]\n    log_lines.append(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]].to_string(index=False))\n\n    # Debugging the breach -- who's the trader of record on each flagged position\n    traders = pd.read_csv("data/trader_contacts.csv")\n    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n    log_lines.append("Traders to notify:")\n    log_lines.append(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]].to_string(index=False))\n    LOG_PATH.write_text("\n".join(log_lines) + "\n")\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n''')
path.write_text(text)
PY
```

### REPRO-13 · Dependency versions pinned [LOW]

**Location:** requirements.txt
**Sample agreement:** 100%
**Evidence:** Packages declared without an exact version, and no lockfile to record one -- requirements.txt: scikit-learn, statsmodels.

**Suggested fix:** Pin the unversioned Python dependencies in requirements.txt to exact versions using placeholders because no version is derivable from the file content.

```
python - <<'PY'
from pathlib import Path
path = Path('requirements.txt')
text = path.read_text()
text = text.replace('scikit-learn\n', 'scikit-learn==<PINNED_VERSION>\n')
text = text.replace('statsmodels\n', 'statsmodels==<PINNED_VERSION>\n')
path.write_text(text)
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

42 checks passed; 22 did not apply to this repository. See machine_report.json for the full list.
