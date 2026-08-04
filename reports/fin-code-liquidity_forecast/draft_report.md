# Compliance Report — fin-code-liquidity_forecast

Run at: 2026-08-04T12:19:07.363600+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\edge_cases\fin-code-liquidity_forecast

## Summary

- Total findings evaluated: 90
- COMPLIANT: 37
- NEEDS_REVIEW: 6
- NOT_APPLICABLE: 42
- NON_COMPLIANT: 5

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestCashPositions.py
**Confidence:** 0.95  |  **Risk score:** 2.85
**Evidence:** Data is loaded and written onward with no validation checks in between; after `pd.read_csv(...)` the code सीधे writes to silver via `balances.to_csv(...)` and `movements.to_csv(...)` without any assert/filter/quality validation.

**Suggested fix:** Add explicit data quality checks after loading the CSVs and before writing them to silver.

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

        assert not balances.empty, "balances must not be empty"
        assert not movements.empty, "movements must not be empty"
        assert balances.notna().all().all(), "balances contains null values"
        assert movements.notna().all().all(), "movements contains null values"
        assert len(balances) == len(balances.drop_duplicates()), "balances contains duplicate rows"
        assert len(movements) == len(movements.drop_duplicates()), "movements contains duplicate rows"

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_2024-07-01.csv", index=False)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/03_ForecastLiquidity.py
**Confidence:** 0.91  |  **Risk score:** 2.73
**Evidence:** Data is loaded from `pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")` and then used for modeling/forecasting, but the file contains no explicit validation checks such as asserts, null/duplicate/range checks, or validation library calls.

**Suggested fix:** Add explicit validation checks after loading the CSV and before modeling to verify required columns, non-null values, and no duplicate rows.

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
    missing_columns = required_columns - set(movements.columns)
    assert not missing_columns, f"Missing required columns: {sorted(missing_columns)}"
    assert movements["amount"].notna().all(), "amount contains null values"
    assert movements["bank_account_id"].notna().all(), "bank_account_id contains null values"
    assert not movements.duplicated().any(), "Duplicate rows found in movements"

    X = movements[["amount"]].shift(1).fillna(0).values
'''
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** Treasury_SQL/CreateCounterpartyDim.sql
**Confidence:** 0.99  |  **Risk score:** 1.98
**Evidence:** CREATE TABLE Reporting.CounterpartyDim (...) uses a data model table name without a forbidden prefix, but the column name `Id` exactly matches the SQL column naming rule's cryptic standalone identifier and the table is a dimension table ending in `Dim`.

**Suggested fix:** Rename the self-matching column `Id` in `Reporting.CounterpartyDim` to a non-conflicting PascalCase name.

```
sed -i 's/^    Id                INT           PRIMARY KEY,/    CounterpartyId    INT           PRIMARY KEY,/' Treasury_SQL/CreateCounterpartyDim.sql
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** Treasury_Pipeline/01_IngestCashPositions.py
**Confidence:** 0.90  |  **Risk score:** 1.8
**Evidence:** The processing code directly overwrites raw source-derived outputs in place by writing CSVs to fixed paths (`silver/BankAccountBalances_20240701.csv`, `silver/DailyCashMovements_20240701.csv`) with no reproducibility controls such as seeds; this file performs data processing but sets no random seed.

**Suggested fix:** Update the ingest script to avoid overwriting raw-derived outputs in place by writing copied outputs to new reproducible filenames or a separate staging path.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/01_IngestCashPositions.py')
text = path.read_text()
text = text.replace('        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)\n        movements.to_csv("silver/DailyCashMovements_20240701.csv", index=False)\n', '        balances.to_csv("silver/BankAccountBalances_20240701_copy.csv", index=False)\n        movements.to_csv("silver/DailyCashMovements_20240701_copy.csv", index=False)\n')
path.write_text(text)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** Treasury_SQL/CreateCounterpartyDim.sql
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** In `CREATE TABLE Reporting.CounterpartyDim`, the column `Id` is a standalone generic name, which the policy flags as NON_COMPLIANT in SQL contexts.

**Suggested fix:** Rename the generic SQL column `Id` to the compliant PascalCase `CounterpartyId` in the CounterpartyDim table definition.

```
sed -i 's/\bId\b                INT           PRIMARY KEY,/CounterpartyId      INT           PRIMARY KEY,/' Treasury_SQL/CreateCounterpartyDim.sql
```

## Needs human review (low-confidence findings)

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/BankAccountBalances_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'BankAccountBalances_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/LiquidityForecast_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'LiquidityForecast_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/BankAccountBalances_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'BankAccountBalances_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/BankAccountBalances_validated_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'BankAccountBalances_validated_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd; file name stem 'BankAccountBalances_validated' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'DailyCashMovements_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_validated_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'DailyCashMovements_validated_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd; file name stem 'DailyCashMovements_validated' is not CamelCase  [no automated fix attached: model reported no violation to fix]

## Compliant checks

37 checks passed. See machine_report.json for the full list.
