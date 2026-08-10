# Compliance Report — fin-code-liquidity_forecast

Run at: 2026-08-10T13:21:34.224367+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\edge_cases\fin-code-liquidity_forecast
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 88.7%** (126/142 weighted checks) — 3 high, 0 medium, 7 low severity violations

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
**Sample agreement:** 100%
**Evidence:** The file loads raw data and writes it to silver without any intervening quality validation.  Quoted: 'balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")'

**Suggested fix:** Add a minimal data-quality validation step before writing bronze data to silver in the ingest pipeline.

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

        if balances.empty or movements.empty:
            raise ValueError("Data quality validation failed: input file(s) are empty")

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
**Evidence:** The file writes bronze-sourced data into silver without an immediate validation step before the middle-layer write.  Quoted: 'balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)'

**Suggested fix:** Add an immediate validation step before writing bronze-sourced balances and movements into silver.

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
            raise ValueError("Validation failed: bronze inputs must not be empty before silver write")

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
**Evidence:** The file loads data and uses it for feature engineering and model training without any explicit quality check first.  Quoted: 'movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")'

**Suggested fix:** Add an explicit data quality validation check immediately after loading the CSV before feature engineering and model training.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/03_ForecastLiquidity.py')
text = path.read_text()
old = '    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")\n\n    X = movements[["amount"]].shift(1).fillna(0).values\n'
new = '    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")\n    if movements.empty or movements[["bank_account_id", "amount"]].isnull().any().any():\n        raise ValueError("Data quality validation failed: empty input or missing required values")\n\n    X = movements[["amount"]].shift(1).fillna(0).values\n'
if old not in text:
    raise SystemExit('Expected snippet not found')
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
**Evidence:** The column Id violates the SQL column naming convention because it is a generic standalone name.  Quoted: 'Id'

**Suggested fix:** Rename the generic SQL column Id to the PascalCase name CounterpartyId in the table definition.

```
sed -i 's/^[[:space:]]*Id[[:space:]]\+INT[[:space:]]\+PRIMARY KEY,/    CounterpartyId    INT           PRIMARY KEY,/' Treasury_SQL/CreateCounterpartyDim.sql
```

## Checks that passed or did not apply

58 checks passed; 22 did not apply to this repository. See machine_report.json for the full list.
