# Compliance Report — FinalProject

Run at: 2026-08-11T12:42:19.840632+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\non_compliant\FinalProject
Self-consistency samples (k): 1
> At k=1 no disagreement is measurable, so every confidence is 1.0 and the remediation confidence gate does not fire.

## Summary

**Weighted pass rate: 42.1%** (32/76 weighted checks) — 6 high, 7 medium, 12 low severity violations

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
**Evidence:** The file loads data and uses it further without any quality check first.  Quoted: "customers = pd.read_csv('data/customers.csv')"

**Suggested fix:** Add a minimal data-quality validation check immediately after loading customers before the data is used.

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
    "required_columns = {'name', 'salary', 'email'}\n",
    "missing = required_columns - set(customers.columns)\n",
    "if missing:\n",
    "    raise ValueError(f'Missing required columns: {sorted(missing)}')\n",
    "print('Customer data:')\n",
    "print(customers)\n",
]
p.write_text(json.dumps(nb, indent=1))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Untitled.ipynb
**Sample agreement:** 100%
**Evidence:** The notebook output can expose raw PII by printing customer data, including email values.  Quoted: 'print(customers)'

**Suggested fix:** Remove raw PII exposure by stopping the notebook from printing full customer records and email values, while keeping non-PII summary output.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('Untitled.ipynb')
nb = json.loads(p.read_text())
nb['cells'][0]['source'] = ["import pandas as pd\n", "\n", "customers = pd.read_csv('data/customers.csv')\n", "print('Customer data loaded')\n"]
nb['cells'][1]['source'] = ["top = customers.nlargest(3, 'salary')[['name', 'salary']]\n", "print('Top earners by salary:')\n", "print(top)\n", "print('\\nAverage salary:', customers['salary'].mean())\n"]
p.write_text(json.dumps(nb, indent=1))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for downstream processing without any quality check first.  Quoted: '# No quality checks before processing (DQ-1 + ARCH-12 violations)'

**Suggested fix:** Add a minimal data-quality validation check before any downstream processing in final_v2_ACTUAL.py.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = '''# No quality checks before processing (DQ-1 + ARCH-12 violations)
avg_price = df["val"].mean()
'''
new = '''# No quality checks before processing (DQ-1 + ARCH-12 violations)
required_cols = {"id", "vol", "val"}
missing = required_cols - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {sorted(missing)}")
if df[["id", "vol", "val"]].isnull().any().any():
    raise ValueError("Data quality check failed: null values found in required columns")

avg_price = df["val"].mean()
'''
if old not in text:
    raise SystemExit('Target snippet not found')
path.write_text(text.replace(old, new, 1))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The script hardcodes credentials directly in source code.  Quoted: 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"'

**Suggested fix:** Remove the hardcoded database password and API key from the script by replacing them with environment-variable lookups and placeholders.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"\napi_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"'
new = 'import os\n\nconnection_string = os.getenv("CONNECTION_STRING", "<SET_CONNECTION_STRING_IN_ENV>")\napi_key = os.getenv("API_KEY", "<SET_API_KEY_IN_ENV>")'
if old not in text:
    raise SystemExit('target secret block not found')
path.write_text(text.replace(old, new))
PY
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The file overwrites a bronze source file in place, violating medallion layer separation.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Move the processed CSV write out of bronze by changing the overwrite target to a non-bronze output path and keep the raw source file untouched.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)', 'df.to_csv("silver/EthanolMarketRate_20240701_processed.csv", index=False)')
s = s.replace('print("Saved back to bronze (overwrote raw source!)")', 'print("Saved processed output to silver layer")')
p.write_text(s)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** data/customers.csv
**Sample agreement:** 100%
**Evidence:** The CSV header exposes direct identifier columns name, email, and phone.  Quoted: 'name,email,phone,salary'

**Suggested fix:** Remove the raw PII header fields from the CSV by replacing the first line with non-PII column names and leaving the data file otherwise unchanged.

```
sed -i '1s/.*/customer_id,salary/' data/customers.csv
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'FinalProject' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from FinalProject to a compliant name using an allowed prefix and suffix pattern, preserving all contents.

```
mv FinalProject fin-code-finalproject
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Untitled.ipynb
**Sample agreement:** 100%
**Evidence:** The file performs data I/O but leaves no durable log or monitoring record beyond print output.  Quoted: "print('Customer data:')"

**Suggested fix:** Add a durable log record for the data I/O by writing the existing customer and market load messages to a log file in addition to printing them.

```
python - <<'PY'
import json
from pathlib import Path
p = Path('Untitled.ipynb')
nb = json.loads(p.read_text())
nb['cells'][0]['source'] = [
    "import pandas as pd\n",
    "from pathlib import Path\n",
    "\n",
    "log_path = Path('data_io.log')\n",
    "\n",
    "def log(msg):\n",
    "    print(msg)\n",
    "    log_path.open('a', encoding='utf-8').write(msg + '\\n')\n",
    "\n",
    "customers = pd.read_csv('data/customers.csv')\n",
    "log('Customer data:')\n",
    "print(customers)\n"
]
nb['cells'][2]['source'] = [
    "market = pd.read_csv('data/ethanol market rate.csv')\n",
    "log('Market data loaded')\n",
    "print(market.head(2))\n"
]
p.write_text(json.dumps(nb, indent=1))
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The script relies on print output rather than persistent logging or queryable metrics.  Quoted: 'print("Data loaded:")'

**Suggested fix:** Replace the ad hoc print statements with persistent logging so the script emits queryable log records instead of console-only output.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n', 'import logging\nimport pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n\nlogging.basicConfig(filename="final_v2_ACTUAL.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n')
replacements = {
    'print("Data loaded:")\nprint(df)\nprint("Shape:", df.shape)\n': 'logger.info("Data loaded")\nlogger.info("Shape: %s", df.shape)\n',
    'print("\\nCustomer list:")\nprint(customers)\n': 'logger.info("Customer list loaded")\nlogger.info("Customer rows: %s", customers.shape)\n',
    'print("\\nAverage price:", avg_price)\n\n': 'logger.info("Average price: %s", avg_price)\n\n',
    'print("Total volume:", total_vol)\n\n': 'logger.info("Total volume: %s", total_vol)\n\n',
    'print("\\nModel trained")\nprint("Score:", model.score(X_test, y_test))\n': 'logger.info("Model trained")\nlogger.info("Score: %s", model.score(X_test, y_test))\n',
    'print("Saved back to bronze (overwrote raw source!)")\n': 'logger.info("Saved back to bronze (overwrote raw source!)")\n',
    'print("\\nDone! Results saved to data/ (no gold layer, no silver layer).")\n': 'logger.info("Done! Results saved to data/ (no gold layer, no silver layer).")\n',
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text)
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The train/test split runs without any seed set in the file.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!'

**Suggested fix:** Add a fixed random_state to the train/test split to make the stochastic step reproducible.

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
**Evidence:** The script writes back over the same raw bronze file it read.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Change the script to stop overwriting the bronze source file by writing the processed CSV to a separate output path instead.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'
new = 'df.to_csv("data/output final.csv", index=False)'
if old not in text:
    raise SystemExit('target line not found')
# replace only the bronze overwrite line; keep the existing later output write unchanged
text = text.replace(old, new, 1)
path.write_text(text)
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** pipeline.yml
**Sample agreement:** 100%
**Evidence:** The configured trigger branches include disallowed names, violating the branching standard.  Quoted: '- main\n      - my-analysis-branch\n      - hotfix'

**Suggested fix:** Remove the disallowed trigger branches from pipeline.yml so only compliant branch names remain.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline.yml')
text = path.read_text()
text = text.replace("      - my-analysis-branch\n", "")
text = text.replace("      - hotfix\n", "")
path.write_text(text)
PY
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** sql/create_tables.sql
**Sample agreement:** 100%
**Evidence:** The SQL object names violate naming rules by using the forbidden tbl_ prefix and non-PascalCase naming.  Quoted: 'CREATE TABLE tbl_ethanol_market_rate'

**Suggested fix:** Rename the SQL objects to remove forbidden prefixes and use PascalCase names, updating the procedure references accordingly.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/create_tables.sql')
s = p.read_text()
s = s.replace('CREATE TABLE tbl_ethanol_market_rate (', 'CREATE TABLE EthanolMarketRate (')
s = s.replace('CREATE TABLE tbl_customers (', 'CREATE TABLE Customers (')
s = s.replace('CREATE PROCEDURE sp_GetData', 'CREATE PROCEDURE GetData')
s = s.replace('FROM tbl_ethanol_market_rate m', 'FROM EthanolMarketRate m')
s = s.replace('JOIN tbl_customers c', 'JOIN Customers c')
p.write_text(s)
PY
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

**Suggested fix:** Pin each dependency in requirements.txt to an exact version placeholder because no lockfile is present and the current file lists unpinned packages.

```
cat > requirements.txt <<'EOF'
pandas==<PINNED_VERSION>
sqlalchemy==<PINNED_VERSION>
numpy==<PINNED_VERSION>
jupyter==<PINNED_VERSION>
sklearn==<PINNED_VERSION>
EOF
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

**Suggested fix:** Rename the CSV headers to snake_case descriptive names derived from the existing tokens: dt,date; id,id; val,value; vol,volume.

```
sed -i '1s/.*/date,id,value,volume/' bronze/EthanolMarketRate_20240701.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Sample agreement:** 100%
**Evidence:** The CSV header uses cryptic single-token names that violate the naming convention.  Quoted: 'dt,id,val,vol'

**Suggested fix:** Rename the CSV header to snake_case column names while preserving the data file contents.

```
sed -i '1s/.*/date,id,value,volume/' 'data/ethanol market rate.csv'
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/create_tables.sql
**Sample agreement:** 100%
**Evidence:** The SQL column names violate the column naming convention because they are not PascalCase and include cryptic standalone names.  Quoted: 'id       INT          PRIMARY KEY,\n    dt       DATE,\n    val      DECIMAL(10,2),\n    vol      DECIMAL(12,2)'

**Suggested fix:** Rename the SQL table columns to PascalCase and update the procedure references accordingly.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/create_tables.sql')
text = p.read_text()
text = text.replace('    id       INT          PRIMARY KEY,\n    dt       DATE,\n    val      DECIMAL(10,2),\n    vol      DECIMAL(12,2)', '    Id       INT          PRIMARY KEY,\n    Dt       DATE,\n    Val      DECIMAL(10,2),\n    Vol      DECIMAL(12,2)')
text = text.replace('    id       INT          PRIMARY KEY,\n    name     VARCHAR(100),\n    email    VARCHAR(200),\n    phone    VARCHAR(20),\n    salary   DECIMAL(10,2)', '    Id       INT          PRIMARY KEY,\n    Name     VARCHAR(100),\n    Email    VARCHAR(200),\n    Phone    VARCHAR(20),\n    Salary   DECIMAL(10,2)')
text = text.replace('        m.id,\n        m.dt,\n        m.val,\n        m.vol,\n        c.name,\n        c.email,\n        c.salary\n    FROM tbl_ethanol_market_rate m\n    JOIN tbl_customers c ON m.id = c.id;', '        m.Id,\n        m.Dt,\n        m.Val,\n        m.Vol,\n        c.Name,\n        c.Email,\n        c.Salary\n    FROM tbl_ethanol_market_rate m\n    JOIN tbl_customers c ON m.Id = c.Id;')
p.write_text(text)
PY
```

## Checks that passed or did not apply

12 checks passed; 20 did not apply to this repository. See machine_report.json for the full list.
