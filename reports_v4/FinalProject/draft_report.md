# Compliance Report — FinalProject

Run at: 2026-08-10T13:25:12.834099+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\non_compliant\FinalProject
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 41.3%** (31/75 weighted checks) — 6 high, 7 medium, 12 low severity violations

- Checks evaluated: 57
- Applicable checks (compliant + non-compliant): 37
- COMPLIANT: 12
- NON_COMPLIANT: 25
- NOT_APPLICABLE: 20
- Requiring human action: 2

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 23
- NO_FIX_AVAILABLE: 2

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Untitled.ipynb
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it for aggregation/selection without any quality validation in between.  Quoted: "customers = pd.read_csv('data/customers.csv')\nprint('Customer data:')\nprint(customers)\n\n### Cell 1 (code)\ntop = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]\nprint('Top earners by salary:')\nprint(top)\nprint('\\nAverage salary:', customers['salary'].mean())"

**Suggested fix:** Add a minimal data-quality validation step after loading customers before aggregation/selection, using an assertion on required columns and non-null salary values.

```
import pandas as pd

customers = pd.read_csv('data/customers.csv')
print('Customer data:')
print(customers)

# Data quality validation
required_cols = {'name', 'salary', 'email'}
assert required_cols.issubset(customers.columns), f"Missing required columns: {required_cols - set(customers.columns)}"
assert customers['salary'].notna().all(), 'salary contains null values'

### Cell 1 (code)
top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]
print('Top earners by salary:')
print(top)
print('\nAverage salary:', customers['salary'].mean())

### Cell 2 (code)
market = pd.read_csv('data/ethanol market rate.csv')
print('Market data loaded')
print(market.head(2))
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for processing and training without any prior quality check, violating DQ-1.  Quoted: '# No quality checks before processing (DQ-1 + ARCH-12 violations)'

**Suggested fix:** Add a minimal data-quality validation check before any processing by asserting the loaded dataframe has no missing values in the required columns.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = '''print("Shape:", df.shape)

# Also load customer data for enrichment
'''
new = '''print("Shape:", df.shape)

# DQ-1: validate required data before processing
required_cols = ["id", "vol", "val"]
if df[required_cols].isnull().any().any():
    raise ValueError("Data quality check failed: missing values in required columns")

# Also load customer data for enrichment
'''
if old not in text:
    raise SystemExit('target insertion point not found')
path.write_text(text.replace(old, new, 1))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The script hardcodes credentials in source, violating SEC-3.  Quoted: 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"'

**Suggested fix:** Remove the hardcoded database credentials by replacing them with environment-variable lookups and a placeholder for the API key.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"\napi_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"'
new = 'import os\n\nconnection_string = os.getenv("CONNECTION_STRING", "<SET_CONNECTION_STRING_ENV_VAR>")\napi_key = os.getenv("API_KEY", "<SET_API_KEY_ENV_VAR>")'
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The file overwrites bronze source data in place, violating ARCH-12.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Redirect the processed output to a non-bronze silver/gold file and keep the bronze source read-only.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)\nprint("Saved back to bronze (overwrote raw source!)")\n', 'df.to_csv("silver/EthanolMarketRate_20240701_processed.csv", index=False)\nprint("Saved processed output to silver layer")\n')
p.write_text(s)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** data/customers.csv
**Sample agreement:** 100%
**Evidence:** The CSV header exposes direct identifier columns name, email, and phone.  Quoted: 'name,email,phone,salary'

**Suggested fix:** Rewrite the CSV header to remove raw PII identifier columns by replacing name, email, and phone with non-identifying snake_case labels while preserving the file structure.

```
sed -i '1s/.*/customer_name,contact_email,contact_phone,salary/' data/customers.csv
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Untitled.ipynb
**Sample agreement:** 67%
**Evidence:** Raw PII is exposed by printing customer data that includes identifier fields such as email.  Quoted: 'print(customers)'  [2/3 samples agreed: NEEDS_REVIEWx1, NON_COMPLIANTx2]

**Suggested fix:** Replace raw customer dataframe prints with redacted summaries that omit PII fields like email.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('Untitled.ipynb')
nb = json.loads(p.read_text())
nb['cells'][0]['source'] = [
    "import pandas as pd\n",
    "\n",
    "customers = pd.read_csv('data/customers.csv')\n",
    "print('Customer data:')\n",
    "print(customers.drop(columns=['email'], errors='ignore').head())\n"
]
nb['cells'][1]['source'] = [
    "top = customers.nlargest(3, 'salary')[['name', 'salary']]\n",
    "print('Top earners by salary:')\n",
    "print(top)\n",
    "print('\\nAverage salary:', customers['salary'].mean())\n"
]
p.write_text(json.dumps(nb, indent=1))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'FinalProject' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from FinalProject to a compliant name matching the required prefix pattern; exact compliant name cannot be derived from the evidence, so use a placeholder to be finalized by the owner.

```
mv FinalProject <compliant-repo-name>
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The script relies on print output only and does not leave a durable log or metric record, violating OPS-2.  Quoted: 'print("Data loaded:")'

**Suggested fix:** Replace print-only status messages with durable logging to a file while preserving existing behavior.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n', 'import logging\nimport pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n\nlogging.basicConfig(filename="final_v2_ACTUAL.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\n')
repls = {
    'print("Data loaded:")': 'logging.info("Data loaded:")',
    'print(df)': 'logging.info("%s", df.to_string())',
    'print("Shape:", df.shape)': 'logging.info("Shape: %s", df.shape)',
    'print("\\nCustomer list:")': 'logging.info("Customer list:")',
    'print(customers)': 'logging.info("%s", customers.to_string())',
    'print("\\nAverage price:", avg_price)': 'logging.info("Average price: %s", avg_price)',
    'print("Total volume:", total_vol)': 'logging.info("Total volume: %s", total_vol)',
    'print("\\nModel trained")': 'logging.info("Model trained")',
    'print("Score:", model.score(X_test, y_test))': 'logging.info("Score: %s", model.score(X_test, y_test))',
    'print("Saved back to bronze (overwrote raw source!)")': 'logging.info("Saved back to bronze (overwrote raw source!)")',
    'print("\\nDone! Results saved to data/ (no gold layer, no silver layer).")': 'logging.info("Done! Results saved to data/ (no gold layer, no silver layer).")',
}
for old, new in repls.items():
    text = text.replace(old, new)
path.write_text(text)
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The train/test split runs without any seed set in the file, violating REPRO-6.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!'

**Suggested fix:** Add a fixed random_state to the train/test split in final_v2_ACTUAL.py to make the stochastic step reproducible.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!'
new = 'X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)  # fixed seed for reproducibility'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-14 · Raw source data not modified in place [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The script writes back over the raw file it read, violating REPRO-14.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Redirect the processed CSV output to a non-bronze file so the raw source remains unchanged.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'
new = 'df.to_csv("data/EthanolMarketRate_20240701_processed.csv", index=False)'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new, 1))
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** pipeline.yml
**Sample agreement:** 100%
**Evidence:** The branch trigger includes an unauthorized branch name, violating the allowed branch naming standard.  Quoted: '- hotfix'

**Suggested fix:** Remove the unauthorized hotfix branch from the pipeline trigger list.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline.yml')
text = path.read_text()
text = text.replace('      - hotfix\n', '')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Untitled.ipynb
**Sample agreement:** 67%
**Evidence:** The notebook performs data work with print() only and no logging that outlives the session.  Quoted: "print('Customer data:')\nprint(customers)"  [2/3 samples agreed: NEEDS_REVIEWx1, NON_COMPLIANTx2]

**Suggested fix:** Replace session-only print statements with persistent logging to a file in the notebook cells.

```
import pandas as pd
import logging

logging.basicConfig(filename='notebook.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

customers = pd.read_csv('data/customers.csv')
logging.info('Customer data:')
logging.info('\n%s', customers)

# Cell 1

top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]
logging.info('Top earners by salary:')
logging.info('\n%s', top)
logging.info('Average salary: %s', customers['salary'].mean())

# Cell 2

market = pd.read_csv('data/ethanol market rate.csv')
logging.info('Market data loaded')
logging.info('\n%s', market.head(2))
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** sql/create_tables.sql
**Sample agreement:** 67%
**Evidence:** The SQL object naming convention is violated by the tbl_ prefix in a table name.  Quoted: 'CREATE TABLE tbl_ethanol_market_rate'  [2/3 samples agreed: NEEDS_REVIEWx1, NON_COMPLIANTx2]

**Suggested fix:** Rename the two tables to remove the forbidden tbl_ prefix while leaving the procedure body unchanged for now.

```
sed -i 's/CREATE TABLE tbl_ethanol_market_rate/CREATE TABLE ethanol_market_rate/; s/CREATE TABLE tbl_customers/CREATE TABLE customers/; s/FROM tbl_ethanol_market_rate/FROM ethanol_market_rate/; s/JOIN tbl_customers/JOIN customers/' sql/create_tables.sql
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** (repository-level)
**Sample agreement:** 100%
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
**Sample agreement:** 100%
**Evidence:** Packages declared without an exact version, and no lockfile to record one -- requirements.txt: jupyter, numpy, pandas, sklearn, sqlalchemy.

**Suggested fix:** Pin each dependency in requirements.txt to an exact version placeholder because no lockfile is present and the current file uses unpinned package names.

```
python - <<'PY'
from pathlib import Path
p = Path('requirements.txt')
lines = p.read_text().splitlines()
fixed = []
for line in lines:
    pkg = line.strip()
    if not pkg:
        fixed.append(line)
    elif '==' in pkg:
        fixed.append(pkg)
    else:
        fixed.append(f"{pkg}==<PINNED_VERSION>")
p.write_text('\n'.join(fixed) + ('\n' if fixed else ''))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** Untitled.ipynb
**Sample agreement:** 100%
**Evidence:** path segment 'Untitled.ipynb' contains the vague name token 'untitled'

**No automated fix**: the compliant name depends on what this file actually contains; an author must choose it

### NAM-5 · File and folder naming convention [LOW]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** path segment 'final_v2_ACTUAL.py' contains the vague name token 'final'; path segment 'final_v2_ACTUAL.py' contains the vague name token 'v2'; path segment 'final_v2_ACTUAL.py' contains the vague name token 'actual'; file name stem 'final_v2_ACTUAL' is not CamelCase

**No automated fix**: the compliant name depends on what this file actually contains; an author must choose it

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline.yml
**Sample agreement:** 100%
**Evidence:** file name stem 'pipeline' is not CamelCase

**Suggested fix:** Rename to 'Pipeline.yml' to satisfy the NAM-5 naming grammar.

```
git mv pipeline.yml Pipeline.yml
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/EthanolMarketRate_20240701.csv
**Sample agreement:** 100%
**Evidence:** file name 'EthanolMarketRate_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/EthanolMarketRate_2024-07-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/EthanolMarketRate_20240701.csv bronze/EthanolMarketRate_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/customers.csv
**Sample agreement:** 100%
**Evidence:** file name stem 'customers' is not CamelCase

**Suggested fix:** Rename to 'data/Customers.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/customers.csv data/Customers.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Sample agreement:** 100%
**Evidence:** file name 'ethanol market rate.csv' contains a space; file name stem 'ethanol market rate' is not CamelCase

**Suggested fix:** Rename to 'data/EthanolMarketRate.csv' to satisfy the NAM-5 naming grammar.

```
git mv 'data/ethanol market rate.csv' data/EthanolMarketRate.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** sql/create_tables.sql
**Sample agreement:** 100%
**Evidence:** file name stem 'create_tables' is not CamelCase

**Suggested fix:** Rename to 'sql/CreateTables.sql' to satisfy the NAM-5 naming grammar.

```
git mv sql/create_tables.sql sql/CreateTables.sql
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/EthanolMarketRate_20240701.csv
**Sample agreement:** 100%
**Evidence:** The CSV header uses cryptic single-token column names that violate the naming convention.  Quoted: 'dt,id,val,vol'

**Suggested fix:** Rename the CSV header to descriptive snake_case column names while preserving the data rows.

```
sed -i '1s/.*/date,identifier,value,volume/' bronze/EthanolMarketRate_20240701.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Sample agreement:** 100%
**Evidence:** The CSV headers violate the naming convention because they are cryptic single-token headers.  Quoted: 'dt,id,val,vol'

**Suggested fix:** Rename the CSV headers to descriptive snake_case names while preserving the data rows.

```
sed -i '1s/.*/date,identifier,value,volume/' 'data/ethanol market rate.csv'
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/create_tables.sql
**Sample agreement:** 67%
**Evidence:** The SQL column naming convention is violated by a non-PascalCase, cryptic column name.  Quoted: 'id       INT          PRIMARY KEY,'  [2/3 samples agreed: NEEDS_REVIEWx1, NON_COMPLIANTx2]

**Suggested fix:** Rename the SQL table columns to PascalCase and update the procedure references accordingly.

```
sed -i 's/\bid\b/Id/g; s/\bdt\b/Dt/g; s/\bval\b/Val/g; s/\bvol\b/Vol/g; s/\bname\b/Name/g; s/\bemail\b/Email/g; s/\bphone\b/Phone/g; s/\bsalary\b/Salary/g' sql/create_tables.sql
```

## Checks that passed or did not apply

12 checks passed; 20 did not apply to this repository. See machine_report.json for the full list.
