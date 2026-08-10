# Compliance Report — fin-code-liquidity_forecast

Run at: 2026-08-10T08:19:25.397117+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\edge_cases\fin-code-liquidity_forecast
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 88.7% (126/142 weighted checks)

> 3 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 90
- Applicable checks (compliant + non-compliant): 68
- COMPLIANT: 58
- NON_COMPLIANT: 10
- NOT_APPLICABLE: 22
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 10

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestCashPositions.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file loads data and writes it onward without any explicit data quality validation in between.  Quoted: 'balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")'

**Suggested fix:** Add explicit data quality validation checks between reading and writing the bronze cash position files.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestCashPositions.py')
text = path.read_text()
old = '''def main() -> None:
    logger.info("Starting ingest run")
    try:
        balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")
        movements = pd.read_csv("bronze/DailyCashMovements_2024-07-01.csv")

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_2024-07-01.csv", index=False)
        logger.info("Ingest run complete: %d balance rows, %d movement rows", len(balances), len(movements))
    except Exception:
        logger.exception("Ingest run failed")
        raise
'''
new = '''def main() -> None:
    logger.info("Starting ingest run")
    try:
        balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")
        movements = pd.read_csv("bronze/DailyCashMovements_2024-07-01.csv")

        if balances.empty:
            raise ValueError("BankAccountBalances_20240701.csv failed validation: no rows loaded")
        if movements.empty:
            raise ValueError("DailyCashMovements_2024-07-01.csv failed validation: no rows loaded")
        if balances.isnull().any().any():
            raise ValueError("BankAccountBalances_20240701.csv failed validation: null values present")
        if movements.isnull().any().any():
            raise ValueError("DailyCashMovements_2024-07-01.csv failed validation: null values present")

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_2024-07-01.csv", index=False)
        logger.info("Ingest run complete: %d balance rows, %d movement rows", len(balances), len(movements))
    except Exception:
        logger.exception("Ingest run failed")
        raise
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** Treasury_Pipeline/01_IngestCashPositions.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file writes to silver without a data quality validation step immediately before the write.  Quoted: 'balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)'

**Suggested fix:** Add a data quality validation step immediately before writing the silver outputs in the ingest pipeline.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestCashPositions.py')
text = path.read_text()
old = '''        balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")
        movements = pd.read_csv("bronze/DailyCashMovements_2024-07-01.csv")

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_2024-07-01.csv", index=False)
'''
new = '''        balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")
        movements = pd.read_csv("bronze/DailyCashMovements_2024-07-01.csv")

        if balances.empty or movements.empty:
            raise ValueError("Data quality validation failed: empty balances or movements")

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_2024-07-01.csv", index=False)
'''
if old not in text:
    raise SystemExit('Expected block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/03_ForecastLiquidity.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file uses loaded data for aggregation and model training without any explicit quality check first.  Quoted: 'movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")'

**Suggested fix:** Add an explicit data quality validation check before using the loaded movements data for training and aggregation.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/03_ForecastLiquidity.py')
text = path.read_text()
old = '''    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")

    X = movements[["amount"]].shift(1).fillna(0).values
'''
new = '''    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")
    required_columns = {"bank_account_id", "amount"}
    missing = required_columns - set(movements.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if movements[["bank_account_id", "amount"]].isnull().any().any():
        raise ValueError("Data quality check failed: null values found in required columns")

    X = movements[["amount"]].shift(1).fillna(0).values
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/BankAccountBalances_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'BankAccountBalances_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/BankAccountBalances_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/BankAccountBalances_20240701.csv bronze/BankAccountBalances_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/LiquidityForecast_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'LiquidityForecast_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/LiquidityForecast_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/LiquidityForecast_20240701.csv gold/LiquidityForecast_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/BankAccountBalances_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'BankAccountBalances_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/BankAccountBalances_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/BankAccountBalances_20240701.csv silver/BankAccountBalances_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/BankAccountBalances_validated_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'BankAccountBalances_validated_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd; file name stem 'BankAccountBalances_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/BankAccountBalancesValidated_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/BankAccountBalances_validated_20240701.csv silver/BankAccountBalancesValidated_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'DailyCashMovements_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/DailyCashMovements_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/DailyCashMovements_20240701.csv silver/DailyCashMovements_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_validated_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'DailyCashMovements_validated_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd; file name stem 'DailyCashMovements_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/DailyCashMovementsValidated_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/DailyCashMovements_validated_20240701.csv silver/DailyCashMovementsValidated_2024-07-01.csv
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** Treasury_SQL/CreateCounterpartyDim.sql
**Confidence:** 0.67  |  **Risk score:** 0.667
**Evidence:** The column Id is a generic standalone name and violates the SQL column naming convention.  Quoted: 'Id                INT           PRIMARY KEY'  [2/3 samples agreed: COMPLIANTx1, NON_COMPLIANTx2]

**Suggested fix:** Rename the generic SQL primary key column Id to CounterpartyId to satisfy SQL-11 naming convention.

```
python - <<'PY'
from pathlib import Path
p = Path('Treasury_SQL/CreateCounterpartyDim.sql')
text = p.read_text()
text = text.replace('    Id                INT           PRIMARY KEY,\n', '    CounterpartyId    INT           PRIMARY KEY,\n')
p.write_text(text)
PY
```

## Checks that passed or did not apply

58 checks passed; 22 did not apply to this repository. See machine_report.json for the full list.
