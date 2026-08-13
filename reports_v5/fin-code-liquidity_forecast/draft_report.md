# Compliance Report — fin-code-liquidity_forecast

Run at: 2026-08-11T12:40:51.517858+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\edge_cases\fin-code-liquidity_forecast
Self-consistency samples (k): 1
> At k=1 no disagreement is measurable, so every confidence is 1.0 and the remediation confidence gate does not fire.

## Summary

**Weighted pass rate: 88.5%** (123/139 weighted checks) — 3 high, 0 medium, 7 low severity violations

- Checks evaluated: 90
- Applicable checks (compliant + non-compliant): 67
- COMPLIANT: 57
- NON_COMPLIANT: 10
- NOT_APPLICABLE: 23
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 10

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestCashPositions.py
**Sample agreement:** 100%
**Evidence:** The file loads data and writes it onward without any explicit quality validation in between.  Quoted: 'balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")'

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
        if balances.isnull().all(axis=1).any():
            raise ValueError("BankAccountBalances_20240701.csv failed validation: blank row detected")
        if movements.isnull().all(axis=1).any():
            raise ValueError("DailyCashMovements_2024-07-01.csv failed validation: blank row detected")

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
**Sample agreement:** 100%
**Evidence:** The file writes bronze-sourced data into the silver layer without a validation step immediately before the write.  Quoted: 'balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)'

**Suggested fix:** Add an explicit validation step immediately before writing bronze data into the silver layer.

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
            raise ValueError("Validation failed: bronze input contains no rows")

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
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any explicit quality check first.  Quoted: 'movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")'

**Suggested fix:** Add an explicit data quality validation step before the CSV is used in Treasury_Pipeline/03_ForecastLiquidity.py.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/03_ForecastLiquidity.py')
text = path.read_text()
old = 'def main() -> None:\n    np.random.seed(RANDOM_STATE)\n    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")\n\n    X = movements[["amount"]].shift(1).fillna(0).values\n'
new = 'def main() -> None:\n    np.random.seed(RANDOM_STATE)\n    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")\n\n    required_columns = {"bank_account_id", "amount"}\n    missing_columns = required_columns.difference(movements.columns)\n    if missing_columns:\n        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")\n    if movements[["bank_account_id", "amount"]].isnull().any().any():\n        raise ValueError("Data quality check failed: null values found in required columns")\n\n    X = movements[["amount"]].shift(1).fillna(0).values\n'
if old not in text:
    raise SystemExit('Target block not found')
path.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/BankAccountBalances_20240701.csv
**Sample agreement:** 100%
**Evidence:** file name 'BankAccountBalances_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/BankAccountBalances_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/BankAccountBalances_20240701.csv bronze/BankAccountBalances_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/LiquidityForecast_20240701.csv
**Sample agreement:** 100%
**Evidence:** file name 'LiquidityForecast_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/LiquidityForecast_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/LiquidityForecast_20240701.csv gold/LiquidityForecast_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/BankAccountBalances_20240701.csv
**Sample agreement:** 100%
**Evidence:** file name 'BankAccountBalances_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/BankAccountBalances_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/BankAccountBalances_20240701.csv silver/BankAccountBalances_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/BankAccountBalances_validated_20240701.csv
**Sample agreement:** 100%
**Evidence:** file name 'BankAccountBalances_validated_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd; file name stem 'BankAccountBalances_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/BankAccountBalancesValidated_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/BankAccountBalances_validated_20240701.csv silver/BankAccountBalancesValidated_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_20240701.csv
**Sample agreement:** 100%
**Evidence:** file name 'DailyCashMovements_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'silver/DailyCashMovements_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/DailyCashMovements_20240701.csv silver/DailyCashMovements_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_validated_20240701.csv
**Sample agreement:** 100%
**Evidence:** file name 'DailyCashMovements_validated_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd; file name stem 'DailyCashMovements_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/DailyCashMovementsValidated_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/DailyCashMovements_validated_20240701.csv silver/DailyCashMovementsValidated_2024-07-01.csv
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** Treasury_SQL/CreateCounterpartyDim.sql
**Sample agreement:** 100%
**Evidence:** The table includes a standalone generic column name, Id, which violates the column naming convention.  Quoted: 'Id                INT           PRIMARY KEY'

**Suggested fix:** Rename the SQL primary key column from Id to a PascalCase name consistent with the table, using CounterpartyId.

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

57 checks passed; 23 did not apply to this repository. See machine_report.json for the full list.
