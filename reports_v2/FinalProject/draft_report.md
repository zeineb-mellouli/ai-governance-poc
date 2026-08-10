# Compliance Report — FinalProject

Run at: 2026-08-10T08:19:53.517475+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\non_compliant\FinalProject
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 41.0% (32/78 weighted checks)

> 6 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 56
- Applicable checks (compliant + non-compliant): 38
- COMPLIANT: 12
- NON_COMPLIANT: 26
- NOT_APPLICABLE: 18
- Requiring human action: 2

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 24
- NO_FIX_AVAILABLE: 2

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Untitled.ipynb
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file loads data and uses it further without any visible quality check first.  Quoted: "customers = pd.read_csv('data/customers.csv')"

**Suggested fix:** Add a minimal data-quality validation check before the loaded customer data is used.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('Untitled.ipynb')
nb = json.loads(p.read_text())
cell = nb['cells'][0]
cell['source'] = [
    "import pandas as pd\n",
    "\n",
    "customers = pd.read_csv('data/customers.csv')\n",
    "assert customers[['name', 'salary', 'email']].notna().all().all(), 'Customer data quality check failed: missing values found'\n",
    "print('Customer data:')\n",
    "print(customers)\n"
]
p.write_text(json.dumps(nb, indent=1))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Untitled.ipynb
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** Raw PII is exposed in notebook output by printing data that includes email values.  Quoted: 'print(top)'

**Suggested fix:** Remove the raw email field from the notebook output by printing only non-PII columns in the top earners table.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('Untitled.ipynb')
nb = json.loads(p.read_text())
for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        src = ''.join(cell.get('source', []))
        if "nlargest(3, 'salary')[[" in src and "'email'" in src:
            cell['source'] = [
                "top = customers.nlargest(3, 'salary')[['name', 'salary']]\n",
                "print('Top earners by salary:')\n",
                "print(top)\n",
                "print('\\nAverage salary:', customers['salary'].mean())\n",
            ]
            break
p.write_text(json.dumps(nb, indent=1))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file uses loaded data for downstream processing without any explicit quality check first.  Quoted: '# No quality checks before processing (DQ-1 + ARCH-12 violations)'

**Suggested fix:** Add an explicit data quality check before any downstream processing by validating required columns and non-empty input, then fail fast if the check does not pass.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = '''print("Shape:", df.shape)

# Also load customer data for enrichment
'''
new = '''print("Shape:", df.shape)

# Explicit data quality check required by DQ-1
required_cols = {"id", "vol", "val"}
missing_cols = required_cols - set(df.columns)
if df.empty or missing_cols:
    raise ValueError(f"Data quality check failed: empty dataframe or missing columns: {sorted(missing_cols)}")

# Also load customer data for enrichment
'''
if old not in text:
    raise SystemExit('Expected insertion point not found')
path.write_text(text.replace(old, new, 1))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file hardcodes credentials directly in source code.  Quoted: 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"'

**Suggested fix:** Remove the hardcoded database password and API key by replacing them with environment-variable placeholders in final_v2_ACTUAL.py.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"\napi_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"'
new = 'import os\n\nconnection_string = os.getenv("CONNECTION_STRING", "<REPLACE_WITH_CONNECTION_STRING>")\napi_key = os.getenv("API_KEY", "<REPLACE_WITH_API_KEY>")'
if old not in text:
    raise SystemExit('Expected secret block not found')
path.write_text(text.replace(old, new))
PY
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file writes processed data back into the bronze source path, violating medallion layer separation.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Redirect the processed CSV output from the immutable bronze source path to a separate silver-layer file and keep the raw bronze input untouched.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'
new = 'df.to_csv("silver/EthanolMarketRate_20240701.csv", index=False)'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new, 1))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** data/customers.csv
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The CSV header exposes direct identifiers: name, email, and phone.  Quoted: 'name,email,phone,salary'

**Suggested fix:** Rename the exposed PII columns in the CSV header to non-identifying snake_case names while preserving the data file.

```
sed -i '1s/.*/full_name,contact_email,contact_phone,salary/' data/customers.csv
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** Repo root name 'FinalProject' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from FinalProject to a compliant name matching the required pattern, using a placeholder suffix if the intended project slug is not derivable from the evidence.

```
mv FinalProject aud-code-placeholder
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Untitled.ipynb
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The file relies on print output rather than durable logging or monitoring records.  Quoted: "print('Customer data:')"

**Suggested fix:** Replace notebook print statements with durable logging calls so output is recorded through the logging system instead of stdout.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('Untitled.ipynb')
nb = json.loads(p.read_text())
for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        src = ''.join(cell.get('source', []))
        src = src.replace("import pandas as pd\n", "import pandas as pd\nimport logging\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n")
        src = src.replace("print('Customer data:')\nprint(customers)\n", "logger.info('Customer data:')\nlogger.info('%s', customers)\n")
        src = src.replace("print('Top earners by salary:')\nprint(top)\nprint('\\nAverage salary:', customers['salary'].mean())\n", "logger.info('Top earners by salary:')\nlogger.info('%s', top)\nlogger.info('Average salary: %s', customers['salary'].mean())\n")
        src = src.replace("print('Market data loaded')\nprint(market.head(2))\n", "logger.info('Market data loaded')\nlogger.info('%s', market.head(2))\n")
        cell['source'] = src.splitlines(keepends=True)
p.write_text(json.dumps(nb, indent=1))
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The file relies on print output rather than durable logging or queryable metric tracking.  Quoted: 'print("Data loaded:")'

**Suggested fix:** Replace print-based status output with durable logging in the Python script to satisfy OPS-2.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n', 'import logging\nimport pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n\nlogging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)\n')
replacements = {
    'print("Data loaded:")': 'logger.info("Data loaded:")',
    'print(df)': 'logger.info("%s", df)',
    'print("Shape:", df.shape)': 'logger.info("Shape: %s", df.shape)',
    'print("\\nCustomer list:")': 'logger.info("Customer list:")',
    'print(customers)': 'logger.info("%s", customers)',
    'print("\\nAverage price:", avg_price)': 'logger.info("Average price: %s", avg_price)',
    'print("Total volume:", total_vol)': 'logger.info("Total volume: %s", total_vol)',
    'print("\\nModel trained")': 'logger.info("Model trained")',
    'print("Score:", model.score(X_test, y_test))': 'logger.info("Score: %s", model.score(X_test, y_test))',
    'print("Saved back to bronze (overwrote raw source!)")': 'logger.info("Saved back to bronze (overwrote raw source!)")',
    'print("\\nDone! Results saved to data/ (no gold layer, no silver layer).")': 'logger.info("Done! Results saved to data/ (no gold layer, no silver layer).")',
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text)
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The stochastic split is not seeded, so the run is not reproducible.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!'

**Suggested fix:** Seed the stochastic train/test split to make the run reproducible.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!'
new = 'X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)  # seeded for reproducibility'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new, 1))
PY
```

### REPRO-14 · Raw source data not modified in place [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The file overwrites the same raw bronze file it read from.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Redirect the processed CSV output to a non-bronze file so the raw source file is not overwritten.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)', 'df.to_csv("data/EthanolMarketRate_20240701_processed.csv", index=False)')
p.write_text(s)
PY
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** sql/create_tables.sql
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The SQL object names violate the naming convention by using forbidden Hungarian prefixes.  Quoted: 'CREATE TABLE tbl_ethanol_market_rate'

**Suggested fix:** Rename the SQL tables and procedure to remove forbidden prefixes and use PascalCase object names.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/create_tables.sql')
text = p.read_text()
text = text.replace('CREATE TABLE tbl_ethanol_market_rate (', 'CREATE TABLE EthanolMarketRate (')
text = text.replace('CREATE TABLE tbl_customers (', 'CREATE TABLE Customers (')
text = text.replace('CREATE PROCEDURE sp_GetData', 'CREATE PROCEDURE GetData')
text = text.replace('FROM tbl_ethanol_market_rate m', 'FROM EthanolMarketRate m')
text = text.replace('JOIN tbl_customers c', 'JOIN Customers c')
p.write_text(text)
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** pipeline.yml configures disallowed trigger branches including my-analysis-branch and hotfix.  Quoted: '- my-analysis-branch'

**Suggested fix:** Remove the disallowed trigger branches from pipeline.yml so the pipeline no longer includes my-analysis-branch or hotfix.

```
python - <<'PY'
from pathlib import Path
p = Path('pipeline.yml')
text = p.read_text()
text = text.replace("- my-analysis-branch\n", "")
text = text.replace("- hotfix\n", "")
p.write_text(text)
PY
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Confidence:** 0.67  |  **Risk score:** 1.334
**Evidence:** final_v2_ACTUAL.py writes a reporting-style output to data/output final.csv, and no repository file documents its grain.  Quoted: 'df.to_csv("data/output final.csv")'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Add repository-level documentation stating the grain of the shared output table written to data/output final.csv.

```
printf '%s
' '# Shared output table grain' '' 'The reporting output written to `data/output final.csv` is at the row grain produced by `final_v2_ACTUAL.py`.' > OUTPUT_TABLE_GRAIN.md
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** No README.md found at the repository root.

**Suggested fix:** Create the required root README.md. The scaffold below is structurally compliant but its content must be written by the author.

```
cat > README.md <<'EOF'
# FinalProject

## Purpose

TODO: what this project is for.

## Structure

TODO: what lives in each top-level folder.
EOF
```

### REPRO-13 · Dependency versions pinned [LOW]

**Location:** requirements.txt
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** Packages declared without an exact version, and no lockfile to record one -- requirements.txt: jupyter, numpy, pandas, sklearn, sqlalchemy.

**Suggested fix:** Pin each dependency in requirements.txt to an exact version placeholder because no lockfile is present and the current file uses unpinned package names.

```
python - <<'PY'
from pathlib import Path
p = Path('requirements.txt')
lines = p.read_text().splitlines()
repl = {
    'pandas': 'pandas==<PINNED_VERSION>',
    'sqlalchemy': 'sqlalchemy==<PINNED_VERSION>',
    'numpy': 'numpy==<PINNED_VERSION>',
    'jupyter': 'jupyter==<PINNED_VERSION>',
    'sklearn': 'sklearn==<PINNED_VERSION>',
}
p.write_text('\n'.join(repl.get(line.strip(), line) for line in lines) + '\n')
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** Untitled.ipynb
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** path segment 'Untitled.ipynb' contains the vague name token 'untitled'

**No automated fix**: the compliant name depends on what this file actually contains; an author must choose it

### NAM-5 · File and folder naming convention [LOW]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** path segment 'final_v2_ACTUAL.py' contains the vague name token 'final'; path segment 'final_v2_ACTUAL.py' contains the vague name token 'v2'; path segment 'final_v2_ACTUAL.py' contains the vague name token 'actual'; file name stem 'final_v2_ACTUAL' is not CamelCase

**No automated fix**: the compliant name depends on what this file actually contains; an author must choose it

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline.yml
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'pipeline' is not CamelCase

**Suggested fix:** Rename to 'Pipeline.yml' to satisfy the NAM-5 naming grammar.

```
git mv pipeline.yml Pipeline.yml
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/EthanolMarketRate_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'EthanolMarketRate_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/EthanolMarketRate_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/EthanolMarketRate_20240701.csv bronze/EthanolMarketRate_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/customers.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'customers' is not CamelCase

**Suggested fix:** Rename to 'data/Customers.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/customers.csv data/Customers.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'ethanol market rate.csv' contains a space; file name stem 'ethanol market rate' is not CamelCase

**Suggested fix:** Rename to 'data/EthanolMarketRate.csv' to satisfy the NAM-5 naming grammar.

```
git mv 'data/ethanol market rate.csv' data/EthanolMarketRate.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** sql/create_tables.sql
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'create_tables' is not CamelCase

**Suggested fix:** Rename to 'sql/CreateTables.sql' to satisfy the NAM-5 naming grammar.

```
git mv sql/create_tables.sql sql/CreateTables.sql
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/EthanolMarketRate_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** The CSV uses cryptic single-token headers that violate the naming convention.  Quoted: 'dt,id,val,vol'

**Suggested fix:** Rename the CSV headers to snake_case descriptive names while preserving the data rows

```
sed -i '1s/.*/date,id,value,volume/' bronze/EthanolMarketRate_20240701.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** The CSV header uses cryptic single-token column names that violate the naming convention.  Quoted: 'dt,id,val,vol'

**Suggested fix:** Rename the CSV header to snake_case descriptive column names while preserving the data rows.

```
sed -i '1s/.*/date,identifier,value,volume/' 'data/ethanol market rate.csv'
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/create_tables.sql
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** The table columns violate the column naming convention with generic, non-PascalCase names.  Quoted: 'id       INT          PRIMARY KEY,'

**Suggested fix:** Rename SQL table columns to PascalCase in the CREATE TABLE statements and update the procedure SELECT references accordingly.

```
sed -i -e 's/\bid\b/Id/g' -e 's/\bdt\b/Dt/g' -e 's/\bval\b/Val/g' -e 's/\bvol\b/Vol/g' -e 's/\bname\b/Name/g' -e 's/\bemail\b/Email/g' -e 's/\bphone\b/Phone/g' -e 's/\bsalary\b/Salary/g' sql/create_tables.sql
```

## Checks that passed or did not apply

12 checks passed; 18 did not apply to this repository. See machine_report.json for the full list.
