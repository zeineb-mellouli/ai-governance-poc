# Compliance Report — fin-code-var_risk_model

Run at: 2026-08-13T12:18:56.854081+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\realistic\fin-code-var_risk_model
Self-consistency samples (k): 3

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
**Evidence:** The file uses loaded data for modeling and output without any explicit quality check first.  Quoted: 'returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")'

**Suggested fix:** Add an explicit data-quality check for required columns before modeling in Risk_Pipeline/02_VolatilityModel.py

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '''def main() -> None:
    returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")

    features = returns[["lagged_return_1d", "lagged_return_5d", "realized_vol_10d"]].values
'''
new = '''def main() -> None:
    returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")

    required_columns = ["lagged_return_1d", "lagged_return_5d", "realized_vol_10d", "realized_vol_1d_fwd"]
    missing_columns = [col for col in required_columns if col not in returns.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    features = returns[["lagged_return_1d", "lagged_return_5d", "realized_vol_10d"]].values
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any explicit quality check first.  Quoted: 'scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")'

**Suggested fix:** Add an explicit data-quality validation step before using the loaded CSV inputs in Risk_Pipeline/03_ComputeVaR.py.

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
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")

    required_scaled_vol = {"instrument_id", "vol_scalar"}
    required_positions = {"instrument_id", "notional", "risk_limit", "desk"}
    if not required_scaled_vol.issubset(scaled_vol.columns):
        raise ValueError(f"VolatilityScalar_20240314.csv missing required columns: {sorted(required_scaled_vol - set(scaled_vol.columns))}")
    if not required_positions.issubset(positions.columns):
        raise ValueError(f"TradingPositions_20240314.csv missing required columns: {sorted(required_positions - set(positions.columns))}")
    if scaled_vol["instrument_id"].isna().any() or positions["instrument_id"].isna().any():
        raise ValueError("instrument_id contains missing values")
    if scaled_vol[["instrument_id", "vol_scalar"]].isna().any().any() or positions[["instrument_id", "notional", "risk_limit", "desk"]].isna().any().any():
        raise ValueError("Input data contains missing required values")

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
**Evidence:** A hardcoded API key appears in the file.  Quoted: 'BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"'

**Suggested fix:** Remove the hardcoded Bloomberg API key and read it from an environment variable instead.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('from pathlib import Path\n\nimport pandas as pd\nimport requests\n\nPath("gold").mkdir(parents=True, exist_ok=True)\n\nBLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"\n', 'from pathlib import Path\nimport os\n\nimport pandas as pd\nimport requests\n\nPath("gold").mkdir(parents=True, exist_ok=True)\n\nBLOOMBERG_API_KEY = os.environ.get("BLOOMBERG_API_KEY")\nif not BLOOMBERG_API_KEY:\n    raise RuntimeError("BLOOMBERG_API_KEY environment variable is required")\n')
path.write_text(text)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** Raw PII is exposed in printed output via the trader_email field.  Quoted: 'print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])'

**Suggested fix:** Remove raw PII from the printed trader notification output by excluding trader_email from the displayed columns.

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

**Suggested fix:** Remove raw PII from the CSV header by renaming the identifier columns to non-identifying snake_case names while preserving the data file.

```
sed -i '1s/^desk,trader_name,trader_email,trader_pnl_ytd$/desk,trader_id,trader_contact,trader_pnl_ytd/' data/trader_contacts.csv
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** azure-pipelines.yml
**Sample agreement:** 100%
**Evidence:** The file violates the branch naming rule by including an unsupported branch name in the trigger list.  Quoted: '- hotfix-var-breach-mar24'

**Suggested fix:** Remove the unsupported branch name from the Azure Pipelines trigger list.

```
sed -i '/^- hotfix-var-breach-mar24$/d' azure-pipelines.yml
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** The training run only prints a metric and does not leave a durable log or metric record.  Quoted: 'print("Volatility scaler R^2:", model.score(X_test, y_test))'

**Suggested fix:** Add a durable metric log alongside the existing print output for the volatility model training run.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
old = '    model = LinearRegression()\n    model.fit(X_train, y_train)\n    print("Volatility scaler R^2:", model.score(X_test, y_test))\n\n    returns["vol_scalar"] = model.predict(features)\n'
new = '    model = LinearRegression()\n    model.fit(X_train, y_train)\n    r2 = model.score(X_test, y_test)\n    print("Volatility scaler R^2:", r2)\n    Path("silver/VolatilityModel_metrics.txt").write_text(f"Volatility scaler R^2: {r2}\n")\n\n    returns["vol_scalar"] = model.predict(features)\n'
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Sample agreement:** 100%
**Evidence:** A stochastic split is used without any seed being set in the file.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)'

**Suggested fix:** Add a fixed random seed to the stochastic train/test split in Risk_Pipeline/02_VolatilityModel.py.

```
sed -i 's/train_test_split(features, target, test_size=0.2)/train_test_split(features, target, test_size=0.2, random_state=42)/' Risk_Pipeline/02_VolatilityModel.py
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Sample agreement:** 100%
**Evidence:** The job relies on print output only and does not leave a durable log or monitoring record.  Quoted: 'print("Desks breaching their VaR limit today:")'

**Suggested fix:** Add durable file-based logging for the VaR breach and trader notification outputs instead of relying on print-only console output.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
text = text.replace('from pathlib import Path\n\nimport pandas as pd\nimport requests\n', 'from pathlib import Path\n\nimport pandas as pd\nimport requests\n\nLOG_PATH = Path("gold/DailyVaRReport_20240314.log")\n')
text = text.replace('def main() -> None:\n', 'def main() -> None:\n    log_lines = []\n')
text = text.replace('    print("Desks breaching their VaR limit today:")\n    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])\n', '    log_lines.append("Desks breaching their VaR limit today:")\n    log_lines.append(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]].to_string(index=False))\n')
text = text.replace('    print("Traders to notify:")\n    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n', '    log_lines.append("Traders to notify:")\n    log_lines.append(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]].to_string(index=False))\n\n    LOG_PATH.write_text("\\n".join(log_lines) + "\\n")\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n')
path.write_text(text)
PY
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** gold/DailyVaRReport_20240314.csv and Risk_SQL/CreateVarBreachFact.sql lack any explicit one-row-per grain statement for the governed output.  Quoted: 'gold/DailyVaRReport_20240314.csv'

**Suggested fix:** Add an explicit one-row-per-grain statement to the governed output documentation for the shared DailyVaRReport output.

```
python - <<'PY'
from pathlib import Path
p = Path('Risk_SQL/CreateVarBreachFact.sql')
text = p.read_text()
marker = '-- Grain: one row per breach event'
if marker not in text:
    text = marker + '\n' + text
    p.write_text(text)
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
