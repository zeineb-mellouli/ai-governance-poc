# Compliance Report — fin-code-var_risk_model

Run at: 2026-08-03T13:29:28.187821+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\realistic\fin-code-var_risk_model

## Summary

- Total findings evaluated: 98
- COMPLIANT: 27
- NON_COMPLIANT: 13
- NOT_APPLICABLE: 58

## Non-compliant findings

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** The code reads from bronze and writes directly to gold, skipping silver for the main flow: `positions = pd.read_csv("bronze/TradingPositions_20240314.csv")` and `merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)`.

**Suggested fix:** Route the VaR pipeline through silver by reading validated positions from silver and writing the final report only after that silver-stage input is used.

```
python - <<'PY'
from pathlib import Path
p = Path('Risk_Pipeline/03_ComputeVaR.py')
s = p.read_text()
s = s.replace('    # bypasses the silver validation gate -- reads raw positions straight from bronze\n    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")\n', '    # use validated silver positions as the main flow input\n    positions = pd.read_csv("silver/TradingPositions_20240314.csv")\n')
p.write_text(s)
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** A hardcoded credential is assigned directly in code: `BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"`.

**Suggested fix:** Remove the hardcoded Bloomberg API key and read it from an environment variable instead.

```
python - <<'PY'
from pathlib import Path
p = Path('Risk_Pipeline/03_ComputeVaR.py')
text = p.read_text()
text = text.replace('import pandas as pd\nimport requests\n', 'import os\n\nimport pandas as pd\nimport requests\n')
text = text.replace('BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"\n\n\ndef fetch_missing_tick(instrument_id: str) -> float:\n', 'BLOOMBERG_API_KEY = os.environ["BLOOMBERG_API_KEY"]\n\n\ndef fetch_missing_tick(instrument_id: str) -> float:\n')
p.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Confidence:** 0.97  |  **Risk score:** 2.91
**Evidence:** Data is loaded and used with no validation checks before use: `returns = pd.read_csv(...)` followed by feature/target selection and model fitting, with no asserts, null checks, duplicate checks, or range/leakage validation.

**Suggested fix:** Add basic data validation before feature selection and model fitting to reject missing, duplicate, or incomplete rows and ensure required columns are present.

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
    missing = [c for c in required_cols if c not in returns.columns]
    assert not missing, f"Missing required columns: {missing}"
    assert not returns[required_cols].isnull().any().any(), "Null values found in required model columns"
    assert not returns.duplicated().any(), "Duplicate rows found in input data"
    assert len(returns) > 0, "No rows available for model training"

    features = returns[["lagged_return_1d", "lagged_return_5d", "realized_vol_10d"]].values
    target = returns["realized_vol_1d_fwd"].values
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 0.97  |  **Risk score:** 2.91
**Evidence:** It prints a dataframe containing identifier-like columns and real-looking values: `print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])`.

**Suggested fix:** Remove the raw trader PII printout by limiting console output to non-identifying breach summary fields only.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/03_ComputeVaR.py')
text = path.read_text()
old = '''    # Debugging the breach -- who's the trader of record on each flagged position
    traders = pd.read_csv("data/trader_contacts.csv")
    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]
    print("Traders to notify:")
    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])
'''
new = '''    # Debugging the breach -- summarize affected desks without exposing trader PII
    print("Affected desks:")
    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 0.91  |  **Risk score:** 2.73
**Evidence:** Data is loaded and used with no validation checks before processing: `scaled_vol = pd.read_csv(...)`, `positions = pd.read_csv(...)`, then `merged = positions.merge(...)` and VaR is computed without asserts/filters/expectations.

**Suggested fix:** Add explicit input validation checks for the volatility scalar and positions data before merging and computing VaR, and fail fast if required columns or null/invalid values are present.

```
python - <<'PY'
from pathlib import Path
p = Path('Risk_Pipeline/03_ComputeVaR.py')
s = p.read_text()
old = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")

    merged = positions.merge(scaled_vol, on="instrument_id")
    merged["var_99_1d"] = merged["notional"] * merged["vol_scalar"] * 2.33
'''
new = '''def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")

    required_scaled_vol = {"instrument_id", "vol_scalar"}
    required_positions = {"instrument_id", "notional", "risk_limit", "desk"}
    if not required_scaled_vol.issubset(scaled_vol.columns):
        raise ValueError(f"scaled_vol missing required columns: {required_scaled_vol - set(scaled_vol.columns)}")
    if not required_positions.issubset(positions.columns):
        raise ValueError(f"positions missing required columns: {required_positions - set(positions.columns)}")
    if scaled_vol[["instrument_id", "vol_scalar"]].isna().any().any():
        raise ValueError("scaled_vol contains null values in required fields")
    if positions[["instrument_id", "notional", "risk_limit", "desk"]].isna().any().any():
        raise ValueError("positions contains null values in required fields")
    if (scaled_vol["vol_scalar"] < 0).any() or (positions["notional"] < 0).any() or (positions["risk_limit"] <= 0).any():
        raise ValueError("invalid numeric values detected in input data")

    merged = positions.merge(scaled_vol, on="instrument_id", validate="many_to_one")
    merged["var_99_1d"] = merged["notional"] * merged["vol_scalar"] * 2.33
'''
if old not in s:
    raise SystemExit('target block not found')
s = s.replace(old, new)
p.write_text(s)
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** azure-pipelines.yml
**Confidence:** 0.98  |  **Risk score:** 1.96
**Evidence:** CI/CD YAML trigger/pr branches include an unsupported branch name: "hotfix-var-breach-mar24". GIT-8 allows only master, develop, or user-story/\d+.

**Suggested fix:** Remove the unsupported hotfix branch from the CI trigger so only allowed branches remain.

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

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 0.98  |  **Risk score:** 1.96
**Evidence:** The file relies on print() for run output and has no logging module usage or error-path logging; e.g. `print("Desks breaching their VaR limit today:")` and `print("Traders to notify:")`.

**Suggested fix:** Replace stdout prints with structured logging and add basic error-path logging around the VaR pipeline steps.

```
python - <<'PY'
from pathlib import Path
p = Path('Risk_Pipeline/03_ComputeVaR.py')
s = p.read_text()
s = s.replace('from pathlib import Path\n\nimport pandas as pd\nimport requests\n', 'from pathlib import Path\nimport logging\n\nimport pandas as pd\nimport requests\n\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n')
s = s.replace('def fetch_missing_tick(instrument_id: str) -> float:\n    response = requests.get(\n        f"https://api.bloomberg-example.com/v1/instruments/{instrument_id}/price",\n        headers={"Authorization": f"Bearer {BLOOMBERG_API_KEY}"},\n        timeout=10,\n    )\n    return response.json().get("price", 0.0)\n', 'def fetch_missing_tick(instrument_id: str) -> float:\n    try:\n        response = requests.get(\n            f"https://api.bloomberg-example.com/v1/instruments/{instrument_id}/price",\n            headers={"Authorization": f"Bearer {BLOOMBERG_API_KEY}"},\n            timeout=10,\n        )\n        response.raise_for_status()\n        return response.json().get("price", 0.0)\n    except Exception:\n        logger.exception("Failed to fetch missing tick for instrument_id=%s", instrument_id)\n        raise\n')
s = s.replace('def main() -> None:\n    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")\n\n    # bypasses the silver validation gate -- reads raw positions straight from bronze\n    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")\n\n    merged = positions.merge(scaled_vol, on="instrument_id")\n    merged["var_99_1d"] = merged["notional"] * merged["vol_scalar"] * 2.33\n\n    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n    print("Desks breaching their VaR limit today:")\n    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])\n\n    # Debugging the breach -- who\'s the trader of record on each flagged position\n    traders = pd.read_csv("data/trader_contacts.csv")\n    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n    print("Traders to notify:")\n    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])\n\n    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n', 'def main() -> None:\n    try:\n        scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")\n\n        # bypasses the silver validation gate -- reads raw positions straight from bronze\n        positions = pd.read_csv("bronze/TradingPositions_20240314.csv")\n\n        merged = positions.merge(scaled_vol, on="instrument_id")\n        merged["var_99_1d"] = merged["notional"] * merged["vol_scalar"] * 2.33\n\n        breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]\n        logger.info("Desks breaching their VaR limit today:\n%s", breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]].to_string(index=False))\n\n        # Debugging the breach -- who\'s the trader of record on each flagged position\n        traders = pd.read_csv("data/trader_contacts.csv")\n        flagged_traders = traders[traders["desk"].isin(breaches["desk"])]\n        logger.info("Traders to notify:\n%s", flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]].to_string(index=False))\n\n        merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)\n    except Exception:\n        logger.exception("VaR computation failed")\n        raise\n')
p.write_text(s)
PY
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** Risk_SQL/CreateVarBreachFact.sql
**Confidence:** 0.98  |  **Risk score:** 1.96
**Evidence:** CREATE TABLE Reporting.VarBreachFact (...) uses schema Reporting (approved) but the table name VarBreachFact exactly matches a column name pattern? No; the clear issue is the object name starts with a forbidden verb-like prefix in the file name only? Actually SQL object name is VarBreachFact, which is PascalCase and ends with Fact. No violation found in the SQL object definition.

**Suggested fix:** No SQL naming violation is present in the table definition, so no change is needed.

```
true
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Confidence:** 0.96  |  **Risk score:** 1.92
**Evidence:** A stochastic split is used with `train_test_split(features, target, test_size=0.2)` but no `random_state` or other seed is set in the file.

**Suggested fix:** Make the train/test split reproducible by setting a fixed random seed.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
text = text.replace('    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)\n', '    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)\n')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Risk_Pipeline/02_VolatilityModel.py
**Confidence:** 0.95  |  **Risk score:** 1.9
**Evidence:** The script relies on `print("Volatility scaler R^2:", model.score(X_test, y_test))` and contains no logging module usage or persistent metric/error logging.

**Suggested fix:** Replace the ad hoc print with persistent logging to a file using the logging module, including the model R^2 metric and basic error reporting.

```
python - <<'PY'
from pathlib import Path
path = Path('Risk_Pipeline/02_VolatilityModel.py')
text = path.read_text()
text = text.replace('from pathlib import Path\n\nimport pandas as pd\n', 'from pathlib import Path\nimport logging\n\nimport pandas as pd\n')
text = text.replace('Path("silver").mkdir(parents=True, exist_ok=True)\n\n\ndef main() -> None:\n', 'Path("silver").mkdir(parents=True, exist_ok=True)\nlogging.basicConfig(filename="silver/volatility_model.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n\n\ndef main() -> None:\n')
text = text.replace('    model = LinearRegression()\n    model.fit(X_train, y_train)\n    print("Volatility scaler R^2:", model.score(X_test, y_test))\n\n    returns["vol_scalar"] = model.predict(features)\n    returns.to_csv("silver/VolatilityScalar_20240314.csv", index=False)\n', '    model = LinearRegression()\n    model.fit(X_train, y_train)\n    r2 = model.score(X_test, y_test)\n    logger.info("Volatility scaler R^2: %s", r2)\n\n    returns["vol_scalar"] = model.predict(features)\n    returns.to_csv("silver/VolatilityScalar_20240314.csv", index=False)\n')
path.write_text(text)
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** README.md
**Confidence:** 0.89  |  **Risk score:** 1.78
**Evidence:** The note says `hotfix-var-breach-mar24` was cut directly from `master`, which is a concrete hotfix branch name outside the allowed master/develop/user-story model.

**Suggested fix:** Remove the noncompliant hotfix branch note from README.md so the documentation no longer records a branch cut directly from master.

```
python - <<'PY'
from pathlib import Path
p = Path('README.md')
text = p.read_text()
old = """## Note\n\n`hotfix-var-breach-mar24` was cut directly from `master` during the March\ngilt-market shock to patch a same-day data gap. Marked for cleanup after the\nincident review.\n"""
p.write_text(text.replace(old, ""))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/VolatilityScalar_20240314.csv
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** CSV header includes plural column names: "lagged_return_1d, lagged_return_5d, realized_vol_10d, realized_vol_1d_fwd" and "instrument_id" is snake_case rather than singular CamelCase.

**Suggested fix:** Rename the CSV columns to use singular CamelCase names instead of plural snake_case headers.

```
python - <<'PY'
from pathlib import Path
p = Path('silver/VolatilityScalar_20240314.csv')
text = p.read_text()
text = text.replace('instrument_id,price_date,price,lagged_return_1d,lagged_return_5d,realized_vol_10d,realized_vol_1d_fwd,vol_scalar', 'InstrumentId,PriceDate,Price,LaggedReturn1D,LaggedReturn5D,RealizedVol10D,RealizedVol1DFwd,VolScalar')
p.write_text(text)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** Risk_Pipeline/03_ComputeVaR.py
**Confidence:** 0.95  |  **Risk score:** 0.95
**Evidence:** The file contains a vague name token `TEMP` in the docstring: `TEMP: hit the Bloomberg feed directly here...`.

**Suggested fix:** Remove the vague TEMP token from the docstring by renaming it to a descriptive note.

```
python - <<'PY'
from pathlib import Path
p = Path('Risk_Pipeline/03_ComputeVaR.py')
text = p.read_text()
text = text.replace('TEMP: hit the Bloomberg feed directly here to backfill the missing 14-Mar\nprice tick during the gilt shock outage -- the usual overnight batch import\nwas down. QA\'d manually, but same-day was required so this went straight to\nprod. Revisit after incident review.','Note: hit the Bloomberg feed directly here to backfill the missing 14-Mar\nprice tick during the gilt shock outage -- the usual overnight batch import\nwas down. QA\'d manually, but same-day was required so this went straight to\nprod. Revisit after incident review.')
p.write_text(text)
PY
```

## Compliant checks

27 checks passed. See machine_report.json for the full list.
