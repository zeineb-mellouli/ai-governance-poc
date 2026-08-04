# Compliance Report — fin-code-liquidity_forecast

Run at: 2026-08-03T13:26:41.053636+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\edge_cases\fin-code-liquidity_forecast

## Summary

- Total findings evaluated: 105
- COMPLIANT: 44
- NOT_APPLICABLE: 54
- NON_COMPLIANT: 7

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/01_IngestCashPositions.py
**Confidence:** 0.93  |  **Risk score:** 2.79
**Evidence:** Data is loaded and written onward with no validation checks before use: CSVs are read with "pd.read_csv(...)" and immediately saved to silver via "to_csv(...)"; no assert/filter/quality validation appears.

**Suggested fix:** Add a minimal data-quality validation step to reject empty or null-containing inputs before writing to silver.

```
python - <<'PY'
from pathlib import Path
p = Path('Treasury_Pipeline/01_IngestCashPositions.py')
s = p.read_text()
old = '''        balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")
        movements = pd.read_csv("bronze/DailyCashMovements_2024-07-01.csv")

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_2024-07-01.csv", index=False)
'''
new = '''        balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")
        movements = pd.read_csv("bronze/DailyCashMovements_2024-07-01.csv")

        if balances.empty or movements.empty:
            raise ValueError("Input data must not be empty")
        if balances.isnull().any().any() or movements.isnull().any().any():
            raise ValueError("Input data contains null values")

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_2024-07-01.csv", index=False)
'''
p.write_text(s.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Treasury_Pipeline/03_ForecastLiquidity.py
**Confidence:** 0.93  |  **Risk score:** 2.79
**Evidence:** Data is loaded and used with no validation checks before modeling or writing output; after `pd.read_csv(...)` there are no asserts, null/duplicate/range checks, or other validation logic.

**Suggested fix:** Add basic input validation immediately after loading the CSV to reject empty, null, duplicate, or non-numeric amount data before training and output generation.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/03_ForecastLiquidity.py')
text = path.read_text()
old = '    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")\n\n    X = movements[["amount"]].shift(1).fillna(0).values\n'
new = '    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")\n    assert not movements.empty, "movements dataset is empty"\n    required_cols = {"bank_account_id", "amount"}\n    missing = required_cols - set(movements.columns)\n    assert not missing, f"missing required columns: {missing}"\n    assert movements["bank_account_id"].notna().all(), "bank_account_id contains nulls"\n    assert movements["amount"].notna().all(), "amount contains nulls"\n    assert pd.api.types.is_numeric_dtype(movements["amount"]), "amount must be numeric"\n    assert not movements.duplicated().any(), "duplicate rows found"\n\n    X = movements[["amount"]].shift(1).fillna(0).values\n'
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### DM-7 · Star schema / shared output table design [MEDIUM]

**Location:** Treasury_Pipeline/03_ForecastLiquidity.py
**Confidence:** 0.84  |  **Risk score:** 1.68
**Evidence:** The file writes a reusable gold output `gold/LiquidityForecast_20240701.csv`, but there is no documentation of the row grain/primary key or what one row represents.

**Suggested fix:** Add a brief schema/grain comment documenting that the gold file is one row per bank_account_id and that bank_account_id is the primary key.

```
python - <<'PY'
from pathlib import Path
path = Path('Treasury_Pipeline/03_ForecastLiquidity.py')
text = path.read_text()
old = '"""Silver -> Gold: project each bank account\'s balance forward 30 days."""\n'
new = '"""Silver -> Gold: project each bank account\'s balance forward 30 days.\n\nGold output grain: one row per bank_account_id (primary key).\nEach row represents the account\'s average daily net flow and projected 30-day balance.\n"""\n'
if old not in text:
    raise SystemExit('target text not found')
path.write_text(text.replace(old, new, 1))
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** Treasury_SQL/CreateCounterpartyDim.sql
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** Column definition `Id INT PRIMARY KEY` uses the generic standalone name `Id`, which the policy flags as non-compliant.

**Suggested fix:** Rename the generic primary key column from Id to CounterpartyId to comply with the SQL column naming convention.

```
sed -i 's/\bId\s\+INT\s\+PRIMARY KEY/CounterpartyId INT PRIMARY KEY/' Treasury_SQL/CreateCounterpartyDim.sql
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/LiquidityForecast_20240701.csv
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** File path is `gold/LiquidityForecast_20240701.csv`; the date suffix uses `20240701` without hyphens, which violates the required `yyyy-MM-dd` format.

**Suggested fix:** Rename the file so the date suffix uses the required yyyy-MM-dd format.

```
git mv gold/LiquidityForecast_20240701.csv gold/LiquidityForecast_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_20240701.csv
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** File name is `DailyCashMovements_20240701.csv`; the date suffix uses `yyyyMMdd` with no hyphens, which the policy lists as a violation.

**Suggested fix:** Rename the file to use the required hyphenated date format in the filename.

```
mv silver/DailyCashMovements_20240701.csv silver/DailyCashMovements_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/DailyCashMovements_validated_20240701.csv
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** File name is `DailyCashMovements_validated_20240701.csv`; the date suffix uses `20240701` without hyphens, which violates the required `yyyy-MM-dd` format.

**Suggested fix:** Rename the file so the date suffix uses the required yyyy-MM-dd format.

```
mv silver/DailyCashMovements_validated_20240701.csv silver/DailyCashMovements_validated_2024-07-01.csv
```

## Compliant checks

44 checks passed. See machine_report.json for the full list.
