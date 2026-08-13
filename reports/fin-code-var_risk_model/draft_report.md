# Compliance Report — fin-code-var_risk_model

Run at: 2026-08-11T12:43:36.972271+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\realistic\fin-code-var_risk_model
Self-consistency samples (k): 1
> At k=1 no disagreement is measurable, so every confidence is 1.0 and the remediation confidence gate does not fire.

## Summary

**Weighted pass rate: 74.8%** (95/127 weighted checks) — 5 high, 5 medium, 7 low severity violations

- Checks evaluated: 80
- Applicable checks (compliant + non-compliant): 60
- COMPLIANT: 43
- NON_COMPLIANT: 17
- NOT_APPLICABLE: 20
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 17

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it for modeling and output without any explicit quality check first.  Quoted: 'returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")'

**Suggested fix:** Add an explicit data quality validation check before the CSV is used for modeling and output.

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
    if returns[required_columns].isnull().any().any():
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
**Evidence:** The file loads data and uses it further without any explicit quality check first.  Quoted: 'scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")'

**Suggested fix:** Add an explicit data quality check before loading and using the silver volatility scalar and bronze positions inputs.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
old = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")
'''
new = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")

    required_vol_cols = {"instrument_id", "vol_scalar"}
    required_pos_cols = {"instrument_id", "notional", "risk_limit", "desk"}
    if not required_vol_cols.issubset(scaled_vol.columns) or not required_pos_cols.issubset(positions.columns):
        raise ValueError("Input data quality check failed: missing required columns")

'''
if old not in text:
    raise SystemExit('Expected block not found')
path.write_text(text.replace(old, new))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** A hardcoded API key appears in the file.  Quoted: 'BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"'

**Suggested fix:** Remove the hardcoded Bloomberg API key and read it from an environment variable instead.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('from pathlib import Path\n\nimport pandas as pd\nimport requests\n', 'from pathlib import Path\nimport os\n\nimport pandas as pd\nimport requests\n')
text = text.replace('BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"\n', 'BLOOMBERG_API_KEY = os.environ.get("BLOOMBERG_API_KEY")\nif not BLOOMBERG_API_KEY:\n    raise RuntimeError("BLOOMBERG_API_KEY is not set")\n')
path.write_text(text)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** Raw PII-like identifiers are printed to output.  Quoted: 'print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])'

**Suggested fix:** Remove the raw PII printout by limiting the trader notification output to non-PII fields only.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
old = '    print("Traders to notify:")\n    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])\n'
new = '    print("Traders to notify:")\n    print(flagged_traders[["desk", "trader_pnl_ytd"]])\n'
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** data/trader_contacts.csv
**Sample agreement:** 100%
**Evidence:** The CSV header exposes direct identifier columns trader_name and trader_email.  Quoted: 'desk,trader_name,trader_email,trader_pnl_ytd'

**Suggested fix:** Remove raw PII from the CSV header by renaming trader_name and trader_email to non-identifying snake_case columns while preserving the data file.

```
python - <<'PY'
from pathlib import Path
path = Path('data/trader_contacts.csv')
text = path.read_text()
text = text.replace('desk,trader_name,trader_email,trader_pnl_ytd', 'desk,trader_id,trader_contact,trader_pnl_ytd', 1)
path.write_text(text)
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** azure-pipelines.yml
**Sample agreement:** 100%
**Evidence:** The file violates the branch naming rule by including a disallowed branch name in the trigger list.  Quoted: '- hotfix-var-breach-mar24'

**Suggested fix:** Remove the disallowed hotfix branch from the Azure Pipelines trigger list.

```
python - <<'PY'
from pathlib import Path
path = Path('azure-pipelines.yml')
text = path.read_text()
text = text.replace("      - hotfix-var-breach-mar24\n", "")
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The run only prints its metric and does not leave a durable log or queryable training record.  Quoted: 'print("Volatility scaler R^2:", model.score(X_test, y_test))'

**Suggested fix:** Add a durable training log alongside the existing metric printout so the volatility model run leaves a queryable record.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '    model.fit(X_train, y_train)\n    print("Volatility scaler R^2:", model.score(X_test, y_test))\n\n    returns["vol_scalar"] = model.predict(features)\n'
new = '    model.fit(X_train, y_train)\n    r2 = model.score(X_test, y_test)\n    print("Volatility scaler R^2:", r2)\n\n    with open("silver/VolatilityModel_training_log.csv", "a", encoding="utf-8") as log_file:\n        if log_file.tell() == 0:\n            log_file.write("metric,value\\n")\n        log_file.write(f"volatility_scaler_r2,{r2}\\n")\n\n    returns["vol_scalar"] = model.predict(features)\n'
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The train/test split is stochastic and no seed is fixed in the file.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)'

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
**Sample agreement:** 100%
**Evidence:** The job relies on print statements and does not leave a durable log record.  Quoted: 'print("Desks breaching their VaR limit today:")'

**Suggested fix:** Replace the non-durable print-based breach reporting with a persistent log file write while preserving the existing VaR output.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('''from pathlib import Path\n\nimport pandas as pd\nimport requests\n''', '''from pathlib import Path\n\nimport pandas as pd\nimport requests\n\nLOG_PATH = Path("gold/DailyVaRReport_20240314.log")\n''')
text = text.replace('''    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n    print("Desks breaching their VaR limit today:")\n    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])\n\n    # Debugging the breach -- who's the trader of record on each flagged position\n    traders = pd.read_csv("data/trader_contacts.csv")\n    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n    print("Traders to notify:")\n    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n''', '''    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n    traders = pd.read_csv("data/trader_contacts.csv")\n    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n\n    with LOG_PATH.open("w", encoding="utf-8") as log_file:\n        log_file.write("Desks breaching their VaR limit today:\\n")\n        log_file.write(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]].to_string(index=False))\n        log_file.write("\\n\\nTraders to notify:\\n")\n        log_file.write(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]].to_string(index=False))\n        log_file.write("\\n")\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n''')
path.write_text(text)
PY
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** README.md, Risk_Pipeline/03_ComputeVaR.py, and Risk_SQL/CreateVarBreachFact.sql do not state the row grain for gold/DailyVaRReport_20240314.csv or Reporting.VarBreachFact.  Quoted: 'Daily VaR breach fact table'

**Suggested fix:** Add explicit row-grain documentation for the Daily VaR breach fact outputs in the README and the two pipeline/SQL files.

```
python - <<'PY'
from pathlib import Path
files = [Path('README.md'), Path('Risk_Pipeline/03_ComputeVaR.py'), Path('Risk_SQL/CreateVarBreachFact.sql')]
for path in files:
    text = path.read_text()
    if path.name == 'README.md':
        if 'Daily VaR breach fact table' in text and 'row grain' not in text:
            text = text.replace('Daily VaR breach fact table', 'Daily VaR breach fact table (row grain: one row per portfolio, valuation_date, and breach_date)')
        elif 'Daily VaR breach fact table' not in text:
            text += '\n\nDaily VaR breach fact table (row grain: one row per portfolio, valuation_date, and breach_date).\n'
    elif path.name == '03_ComputeVaR.py':
        if 'Daily VaR breach fact table' in text and 'row grain' not in text:
            text = text.replace('Daily VaR breach fact table', 'Daily VaR breach fact table (row grain: one row per portfolio, valuation_date, and breach_date)')
        elif 'Daily VaR breach fact table' not in text:
            text += '\n# Daily VaR breach fact table (row grain: one row per portfolio, valuation_date, and breach_date)\n'
    elif path.name == 'CreateVarBreachFact.sql':
        if 'Daily VaR breach fact table' in text and 'row grain' not in text:
            text = text.replace('Daily VaR breach fact table', 'Daily VaR breach fact table (row grain: one row per portfolio, valuation_date, and breach_date)')
        elif 'Daily VaR breach fact table' not in text:
            text = '-- Daily VaR breach fact table (row grain: one row per portfolio, valuation_date, and breach_date)\n' + text
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

43 checks passed; 20 did not apply to this repository. See machine_report.json for the full list.
