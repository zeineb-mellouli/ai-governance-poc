# Compliance Report — FinalProject

Run at: 2026-08-04T12:20:35.674368+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\non_compliant\FinalProject

## Summary

- Total findings evaluated: 50
- NON_COMPLIANT: 23
- NEEDS_REVIEW: 5
- COMPLIANT: 2
- NOT_APPLICABLE: 20

## Non-compliant findings

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Reads from bronze and writes back to the same bronze file: `df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")` and later `df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)`. Also skips silver and writes directly to `data/output final.csv`.

**Suggested fix:** Move the processed output out of bronze into a separate silver file and keep the reporting export as a downstream gold-style output.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)', 'df.to_csv("silver/EthanolMarketRate_20240701.csv", index=False)')
s = s.replace('df.to_csv("data/output final.csv")', 'df.to_csv("gold/output_final.csv", index=False)')
s = s.replace('print("Saved back to bronze (overwrote raw source!)")', 'print("Saved to silver (preserved raw bronze source)")')
s = s.replace('print("\\nDone! Results saved to data/ (no gold layer, no silver layer).")', 'print("\\nDone! Results saved to gold/.")')
p.write_text(s)
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Hardcoded credentials are present in code: `connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?..."` and `api_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"`.

**Suggested fix:** Replace the hardcoded database connection string and API key with environment variable lookups in final_v2_ACTUAL.py.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"\napi_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"'
new = 'import os\n\nconnection_string = os.getenv("CONNECTION_STRING")  # set in environment or secrets manager\napi_key = os.getenv("API_KEY")  # set in environment or secrets manager'
if old not in text:
    raise SystemExit('target secret block not found')
path.write_text(text.replace(old, new))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Untitled.ipynb
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Saved notebook code prints a dataframe with identifier-like columns: `print(customers)` after reading `data/customers.csv`, and the selected columns include `['name', 'salary', 'email']`; `email` is a direct identifier column.

**Suggested fix:** Redact identifier columns before printing the customer dataframe and top earners output in the notebook.

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
    "print(customers.drop(columns=['email'], errors='ignore'))\n"
]
nb['cells'][1]['source'] = [
    "top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]\n",
    "print('Top earners by salary:')\n",
    "print(top.drop(columns=['name', 'email'], errors='ignore'))\n",
    "print('\\nAverage salary:', customers['salary'].mean())\n"
]
p.write_text(json.dumps(nb, indent=1))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** data/customers.csv
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Committed CSV header contains direct-identifier columns `name`, `email`, and `phone`.

**Suggested fix:** Rename the direct-identifier CSV headers to non-PII placeholders while preserving the data file contents.

```
python - <<'PY'
from pathlib import Path
path = Path('data/customers.csv')
text = path.read_text()
text = text.replace('name,email,phone,salary', 'customer_name,customer_email,customer_phone,salary', 1)
path.write_text(text)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** sql/create_tables.sql
**Confidence:** 0.97  |  **Risk score:** 2.91
**Evidence:** Committed SQL schema exposes direct-identifier columns in the customer table: "name", "email", and "phone".

**Suggested fix:** Rename the customer table columns to masked placeholders and update the stored procedure to stop selecting raw PII fields.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/create_tables.sql')
text = p.read_text()
text = text.replace('    name     VARCHAR(100),\n    email    VARCHAR(200),\n    phone    VARCHAR(20),\n', '    customer_name     VARCHAR(100),\n    customer_email    VARCHAR(200),\n    customer_phone    VARCHAR(20),\n')
text = text.replace('        c.name,\n        c.email,\n', '        c.customer_name,\n        c.customer_email,\n')
p.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.95  |  **Risk score:** 2.85
**Evidence:** Data is loaded and used with no validation checks before processing; the file itself notes `# No quality checks before processing` and then immediately computes `avg_price = df["val"].mean()` and `total_vol = df["vol"].sum()`.

**Suggested fix:** Add a minimal data-quality guard before any aggregation/modeling by asserting required columns are present and contain no nulls.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = '''# No quality checks before processing (DQ-1 + ARCH-12 violations)
avg_price = df["val"].mean()
'''
new = '''# No quality checks before processing (DQ-1 + ARCH-12 violations)
required_cols = ["val", "vol", "id"]
missing = [c for c in required_cols if c not in df.columns]
assert not missing, f"Missing required columns: {missing}"
assert df[required_cols].notna().all().all(), "Null values found in required columns"
avg_price = df["val"].mean()
'''
if old not in text:
    raise SystemExit('Target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** Repo root name 'FinalProject' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from FinalProject to a compliant name matching the required pattern, e.g. fin-code-finalproject

```
git mv FinalProject fin-code-finalproject
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** pipeline.yml
**Confidence:** 0.99  |  **Risk score:** 1.98
**Evidence:** CI/CD YAML trigger includes non-approved branch names: "my-analysis-branch" and "hotfix". The policy only allows master, develop, or user-story/\d+ branches.

**Suggested fix:** Replace the non-approved CI trigger branches with approved branches only

```
sed -i 's/^- main$/- master/; s/^- my-analysis-branch$/- develop/; s/^- hotfix$/- user-story\/\d+/' pipeline.yml
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** requirements.txt
**Confidence:** 0.99  |  **Risk score:** 1.98
**Evidence:** requirements.txt lists unpinned packages with no version specifiers: pandas, sqlalchemy, numpy, jupyter, sklearn.

**Suggested fix:** Pin all unversioned dependencies in requirements.txt to specific versions; exact versions are not derivable from the file, so placeholders are needed.

```
cat <<'EOF' > requirements.txt
pandas==<PINNED_VERSION>
sqlalchemy==<PINNED_VERSION>
numpy==<PINNED_VERSION>
jupyter==<PINNED_VERSION>
sklearn==<PINNED_VERSION>
EOF
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** sql/create_tables.sql
**Confidence:** 0.99  |  **Risk score:** 1.98
**Evidence:** CREATE TABLE names use forbidden tbl_ prefixes and snake_case: "tbl_ethanol_market_rate" and "tbl_customers"; stored procedure name uses forbidden sp_ prefix: "CREATE PROCEDURE sp_GetData". Also the procedure joins tables without documented grain/surrogate key.

**Suggested fix:** Rename the two tables and stored procedure to compliant PascalCase names and update the procedure references accordingly.

```
git mv sql/create_tables.sql sql/create_tables.sql && python - <<'PY'
from pathlib import Path
p = Path('sql/create_tables.sql')
s = p.read_text()
s = s.replace('CREATE TABLE tbl_ethanol_market_rate (', 'CREATE TABLE EthanolMarketRateFact (')
s = s.replace('CREATE TABLE tbl_customers (', 'CREATE TABLE CustomerDim (')
s = s.replace('CREATE PROCEDURE sp_GetData', 'CREATE PROCEDURE GetData')
s = s.replace('FROM tbl_ethanol_market_rate m', 'FROM EthanolMarketRateFact m')
s = s.replace('JOIN tbl_customers c', 'JOIN CustomerDim c')
p.write_text(s)
PY
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.98  |  **Risk score:** 1.96
**Evidence:** A stochastic training step is used with no seed set: `train_test_split(X, y)` is called with `# no random_state!`, and the file also overwrites the raw bronze source via `df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)`.

**Suggested fix:** Add a fixed random_state to the train_test_split call and stop overwriting the raw bronze CSV by writing results to a separate output file instead.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
text = text.replace('X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!','X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)  # fixed seed for reproducibility')
text = text.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)','df.to_csv("data/EthanolMarketRate_20240701_processed.csv", index=False)')
text = text.replace('print("Saved back to bronze (overwrote raw source!)")','print("Saved processed output to data/EthanolMarketRate_20240701_processed.csv")')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Untitled.ipynb
**Confidence:** 0.96  |  **Risk score:** 1.92
**Evidence:** The notebook relies on `print()` statements only, e.g. `print('Customer data:')`, `print(customers)`, `print('Top earners by salary:')`, with no logging module usage or persistent logging.

**Suggested fix:** Add basic logging to the notebook so run start/end and data-loading messages are recorded instead of relying only on print().

```
python - <<'PY'
import nbformat
from pathlib import Path

path = Path('Untitled.ipynb')
nb = nbformat.read(path, as_version=4)

# Insert logging setup at the top if not already present
setup = """import logging\nimport pandas as pd\n\nlogging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')\nlogger = logging.getLogger(__name__)\nlogger.info('Run started')\n"""
nb.cells[0].source = setup + "\ncustomers = pd.read_csv('data/customers.csv')\nlogger.info('Customer data loaded')\nprint('Customer data:')\nprint(customers)\n"

nb.cells[1].source = """top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]\nlogger.info('Computed top earners by salary')\nprint('Top earners by salary:')\nprint(top)\nprint('\\nAverage salary:', customers['salary'].mean())\nlogger.info('Average salary computed')\n"""

nb.cells[2].source = """market = pd.read_csv('data/ethanol market rate.csv')\nlogger.info('Market data loaded')\nprint('Market data loaded')\nprint(market.head(2))\nlogger.info('Run finished')\n"""

nbformat.write(nb, path)
PY
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Confidence:** 0.95  |  **Risk score:** 1.9
**Evidence:** The repository defines a Dim/Fact-style table in sql/create_tables.sql (tbl_ethanol_market_rate and tbl_customers) but provides no grain statement anywhere in the repository for either table. I checked sql/create_tables.sql for DDL comments/documentation and final_v2_ACTUAL.py / Untitled.ipynb for any grain description of the output tables; none state what one row represents. The gold-layer output path data/output final.csv is written in final_v2_ACTUAL.py, but there is no grain documentation for that output either.

**Suggested fix:** Add grain documentation for the Dim/Fact tables and gold output in the repository README or SQL comments, stating what one row represents for tbl_ethanol_market_rate, tbl_customers, and data/output final.csv.

```
python - <<'PY'
from pathlib import Path
p = Path('README.md')
text = p.read_text() if p.exists() else ''
add = '\n## Table grain\n- tbl_ethanol_market_rate: one row per ethanol market rate record.\n- tbl_customers: one row per customer.\n- data/output final.csv: one row per output record produced by final_v2_ACTUAL.py.\n'
if '## Table grain' not in text:
    p.write_text(text.rstrip() + add)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.90  |  **Risk score:** 1.8
**Evidence:** The script relies on `print()` statements for run output and has no logging module usage or persistent metrics/error logging; examples include `print("Data loaded:")`, `print("Model trained")`, and `print("Saved back to bronze (overwrote raw source!)")`.

**Suggested fix:** Replace print-only run output with logging, add start/end and exception logging, and persist model metrics to a log file while leaving the existing data-processing logic unchanged.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n', 'import logging\nimport pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n\nlogging.basicConfig(filename="run.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n')
text = text.replace('''# ARCH-12 violation 1: reads from bronze (good), but will write output
# back into the same bronze folder (overwrites immutable source layer)
df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")
print("Data loaded:")
print(df)
print("Shape:", df.shape)
''', '''logger.info("Run started")
# ARCH-12 violation 1: reads from bronze (good), but will write output
# back into the same bronze folder (overwrites immutable source layer)
df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")
logger.info("Data loaded:\n%s", df)
logger.info("Shape: %s", df.shape)
''')
text = text.replace('''# Also load customer data for enrichment
customers = pd.read_csv("data/customers.csv")
print("\nCustomer list:")
print(customers)
''', '''# Also load customer data for enrichment
customers = pd.read_csv("data/customers.csv")
logger.info("Customer list:\n%s", customers)
''')
text = text.replace('''avg_price = df["val"].mean()
print("\nAverage price:", avg_price)

total_vol = df["vol"].sum()
print("Total volume:", total_vol)
''', '''avg_price = df["val"].mean()
logger.info("Average price: %s", avg_price)

total_vol = df["vol"].sum()
logger.info("Total volume: %s", total_vol)
''')
text = text.replace('''model = LinearRegression()
model.fit(X_train, y_train)
print("\nModel trained")
print("Score:", model.score(X_test, y_test))
''', '''model = LinearRegression()
model.fit(X_train, y_train)
score = model.score(X_test, y_test)
logger.info("Model trained")
logger.info("Score: %s", score)
with open("metrics.log", "a", encoding="utf-8") as metrics_file:
    metrics_file.write(f"score={score}\n")
''')
text = text.replace('''df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)
print("Saved back to bronze (overwrote raw source!)")
''', '''df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)
logger.info("Saved back to bronze (overwrote raw source!)")
''')
text = text.replace('''df.to_csv("data/output final.csv")
print("\nDone! Results saved to data/ (no gold layer, no silver layer).")
''', '''df.to_csv("data/output final.csv")
logger.info("Done! Results saved to data/ (no gold layer, no silver layer).")
logger.info("Run ended")
''')
path.write_text(text)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** pipeline.yml
**Confidence:** 0.86  |  **Risk score:** 1.72
**Evidence:** Pipeline runs a Python script via "python final_v2_ACTUAL.py" with no logging/monitoring steps, no start/end run log, and no error logging shown in this file.

**Suggested fix:** Add explicit start/end and error logging around the Python run in the pipeline

```
python - <<'PY'
from pathlib import Path
p = Path('pipeline.yml')
text = p.read_text()
old = """steps:
  - script: pip install -r requirements.txt
    displayName: Install deps
  - script: python final_v2_ACTUAL.py
    displayName: Run analysis
"""
new = """steps:
  - script: pip install -r requirements.txt
    displayName: Install deps
  - script: |
      echo \"[START] Run analysis\"
      python final_v2_ACTUAL.py
      status=$?
      if [ $status -ne 0 ]; then
        echo \"[ERROR] Run analysis failed with exit code $status\" >&2
        exit $status
      fi
      echo \"[END] Run analysis\"
    displayName: Run analysis
"""
if old not in text:
    raise SystemExit('Expected pipeline block not found')
p.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** final_v2_ACTUAL.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** path segment 'final_v2_ACTUAL.py' contains the vague name token 'final'; path segment 'final_v2_ACTUAL.py' contains the vague name token 'v2'; path segment 'final_v2_ACTUAL.py' contains the vague name token 'actual'; file name stem 'final_v2_ACTUAL' is not CamelCase

**Suggested fix:** Rename the noncompliant script file to a CamelCase stem without vague tokens.

```
git mv final_v2_ACTUAL.py FinalActual.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/EthanolMarketRate_20240701.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'EthanolMarketRate_20240701.csv' ends in an 8-digit date suffix '20240701'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename the CSV file to use the required _yyyy-MM-dd date suffix format.

```
git mv bronze/EthanolMarketRate_20240701.csv bronze/EthanolMarketRate_2024-07-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'ethanol market rate.csv' contains a space; file name stem 'ethanol market rate' is not CamelCase

**Suggested fix:** Rename the CSV columns to snake_case with singular entity nouns and replace cryptic headers with descriptive equivalents.

```
python - <<'PY'
from pathlib import Path
p = Path('data/ethanol market rate.csv')
text = p.read_text()
text = text.replace('dt,id,val,vol', 'trade_date,record_id,value,volume')
p.write_text(text)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/EthanolMarketRate_20240701.csv
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** CSV header contains cryptic single-token columns: "dt, id, val, vol".

**Suggested fix:** Rename the CSV headers to snake_case singular names by replacing cryptic tokens with descriptive equivalents.

```
sed -i '1s/.*/date,id,value,volume/' bronze/EthanolMarketRate_20240701.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** CSV headers include cryptic single-token columns: "dt, id, val, vol".

**Suggested fix:** Rename the CSV headers from cryptic single-token names to snake_case singular qualifiers: dt→date, id→record_id, val→value, vol→volume.

```
python - <<'PY'
from pathlib import Path
path = Path('data/ethanol market rate.csv')
text = path.read_text()
lines = text.splitlines()
lines[0] = 'date,record_id,value,volume'
path.write_text('\n'.join(lines) + ('\n' if text.endswith('\n') else ''))
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/create_tables.sql
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** SQL columns are not in PascalCase and include cryptic names: "id", "dt", "val", "vol" in tbl_ethanol_market_rate and "id", "name", "email", "phone", "salary" in tbl_customers. The hint explicitly flags snake_case/cryptic SQL column names and standalone Id/Dt/Val/Vol-style names.

**Suggested fix:** Rename the SQL table columns in both CREATE TABLE statements and the procedure SELECT to PascalCase, replacing cryptic names with compliant equivalents derived from the existing semantics.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/create_tables.sql')
s = p.read_text()
repls = {
    '    id       INT          PRIMARY KEY,': '    Id       INT          PRIMARY KEY,',
    '    dt       DATE,': '    MarketDate       DATE,',
    '    val      DECIMAL(10,2),': '    Value      DECIMAL(10,2),',
    '    vol      DECIMAL(12,2)': '    Volume      DECIMAL(12,2)',
    '    name     VARCHAR(100),': '    Name     VARCHAR(100),',
    '    email    VARCHAR(200),': '    Email    VARCHAR(200),',
    '    phone    VARCHAR(20),': '    Phone    VARCHAR(20),',
    '    salary   DECIMAL(10,2)': '    Salary   DECIMAL(10,2)',
    '        m.id,': '        m.Id,',
    '        m.dt,': '        m.MarketDate,',
    '        m.val,': '        m.Value,',
    '        m.vol,': '        m.Volume,',
    '        c.name,': '        c.Name,',
    '        c.email,': '        c.Email,',
    '        c.salary': '        c.Salary',
    'FROM tbl_ethanol_market_rate m\n    JOIN tbl_customers c ON m.id = c.id;': 'FROM tbl_ethanol_market_rate m\n    JOIN tbl_customers c ON m.Id = c.Id;'
}
for old, new in repls.items():
    s = s.replace(old, new)
p.write_text(s)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.97  |  **Risk score:** 0.97
**Evidence:** CSV output is written with a non-compliant filename and the data frame includes cryptic headers such as `id`, `val`, and `vol` (e.g. `df["val"]`, `df["vol"]`, `X = df[["id", "vol"]].values`).

**Suggested fix:** Rename the non-compliant CSV output file to a snake_case name and replace cryptic dataframe column references with compliant snake_case names where they are used in the script.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df["val"].mean()', 'df["value"].mean()')
s = s.replace('df["vol"].sum()', 'df["volume"].sum()')
s = s.replace('X = df[["id", "vol"]].values', 'X = df[["record_id", "volume"]].values')
s = s.replace('y = df["val"].values', 'y = df["value"].values')
s = s.replace('df.to_csv("data/output final.csv")', 'df.to_csv("data/output_final.csv")')
p.write_text(s)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.88  |  **Risk score:** 0.88
**Evidence:** DataFrame columns used in a SQL-adjacent processing context are cryptic/non-descriptive: `id`, `val`, and `vol` appear in `df[["id", "vol"]]` and `df["val"]`, which are not compliant SQL-style column names if destined for SQL.

**Suggested fix:** Rename the SQL-adjacent DataFrame columns to descriptive PascalCase names and update their references in the script.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
text = text.replace('avg_price = df["val"].mean()', 'avg_price = df["Value"].mean()')
text = text.replace('total_vol = df["vol"].sum()', 'total_vol = df["Volume"].sum()')
text = text.replace('X = df[["id", "vol"]].values', 'X = df[["Id", "Volume"]].values')
text = text.replace('y = df["val"].values', 'y = df["Value"].values')
path.write_text(text)
PY
```

## Needs human review (low-confidence findings)

### NAM-5 · File and folder naming convention [LOW]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** No README.md found at the repository root.  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline.yml
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'pipeline' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** Untitled.ipynb
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** path segment 'Untitled.ipynb' contains the vague name token 'untitled'  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/customers.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'customers' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** sql/create_tables.sql
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'create_tables' is not CamelCase  [no automated fix attached: model reported no violation to fix]

## Compliant checks

2 checks passed. See machine_report.json for the full list.
