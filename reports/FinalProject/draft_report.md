# Compliance Report — FinalProject

Run at: 2026-08-03T13:28:13.107347+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\non_compliant\FinalProject

## Summary

- Total findings evaluated: 40
- NON_COMPLIANT: 20
- NOT_APPLICABLE: 16
- COMPLIANT: 4

## Non-compliant findings

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Reads from bronze and writes back to the same bronze file: `pd.read_csv("bronze/EthanolMarketRate_20240701.csv")` and later `df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)`. Also skips silver and writes directly to `data/output final.csv`.

**Suggested fix:** Move the processed output out of bronze into a silver staging file and then write the final reporting dataset to a gold/output path, leaving the bronze source immutable.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)\nprint("Saved back to bronze (overwrote raw source!)")\n\n# ARCH-12 violation 2: no silver layer exists anywhere -- bronze jumps straight\n# to a reporting dump with zero validation or aggregation in between\ndf.to_csv("data/output final.csv")\nprint("\\nDone! Results saved to data/ (no gold layer, no silver layer).")\n', 'silver_path = "silver/EthanolMarketRate_20240701_silver.csv"\ndf.to_csv(silver_path, index=False)\nprint(f"Saved processed data to silver: {silver_path}")\n\n# Gold layer / reporting output\ngold_path = "gold/output_final.csv"\ndf.to_csv(gold_path, index=False)\nprint(f"\\nDone! Results saved to gold: {gold_path}")\n')
p.write_text(s)
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Hardcoded credentials appear directly in code: `connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?..."` and `api_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"`.

**Suggested fix:** Remove the hardcoded database credentials and API key from the script and read them from environment variables instead.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"\napi_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"', 'import os\nconnection_string = os.environ["DB_CONNECTION_STRING"]\napi_key = os.environ["API_KEY"]')
p.write_text(s)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** Untitled.ipynb
**Confidence:** 0.98  |  **Risk score:** 2.94
**Evidence:** Data is loaded and used with no validation checks: `pd.read_csv('data/customers.csv')`, `pd.read_csv('data/ethanol market rate.csv')`, then `nlargest(...)` and `mean()` with no assert/raise/filter or validation call anywhere in the notebook.

**Suggested fix:** Add basic data validation checks after loading each CSV so the notebook asserts required columns and non-empty data before using the values.

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
"required_customer_cols = {'name', 'salary', 'email'}\n",
"assert not customers.empty, 'customers.csv is empty'\n",
"assert required_customer_cols.issubset(customers.columns), f'missing columns: {required_customer_cols - set(customers.columns)}'\n",
"assert customers['salary'].notna().all(), 'salary contains missing values'\n",
"print('Customer data:')\n",
"print(customers)\n"
]
nb['cells'][1]['source'] = [
"top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]\n",
"print('Top earners by salary:')\n",
"print(top)\n",
"print('\\nAverage salary:', customers['salary'].mean())\n"
]
nb['cells'][2]['source'] = [
"market = pd.read_csv('data/ethanol market rate.csv')\n",
"assert not market.empty, 'ethanol market rate.csv is empty'\n",
"print('Market data loaded')\n",
"print(market.head(2))\n"
]
p.write_text(json.dumps(nb, indent=1))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.95  |  **Risk score:** 2.85
**Evidence:** Data is loaded and used with no validation checks before processing; the file explicitly says `# No quality checks before processing` and then computes aggregates/model training without asserts, filters, or expectation checks.

**Suggested fix:** Add basic data quality validation before any aggregation or model training, including required-column, null, and numeric checks with row filtering or failure on invalid data.

```
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

# ARCH-12 violation 1: reads from bronze (good), but will write output
# back into the same bronze folder (overwrites immutable source layer)
df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")
print("Data loaded:")
print(df)
print("Shape:", df.shape)

# Also load customer data for enrichment
customers = pd.read_csv("data/customers.csv")
print("\nCustomer list:")
print(customers)

# Connect to database - password hardcoded directly in script
connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"
api_key = "prod-key-placeholder"

# Data quality checks before processing
required_cols = ["id", "vol", "val"]
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"Missing required columns: {missing_cols}")

df = df.dropna(subset=required_cols).copy()
df = df[pd.to_numeric(df["id"], errors="coerce").notna()]
df = df[pd.to_numeric(df["vol"], errors="coerce").notna()]
df = df[pd.to_numeric(df["val"], errors="coerce").notna()]
df[["id", "vol", "val"]] = df[["id", "vol", "val"]].apply(pd.to_numeric)
if df.empty:
    raise ValueError("No valid rows remain after data quality checks")

avg_price = df["val"].mean()
print("\nAverage price:", avg_price)

total_vol = df["vol"].sum()
print("Total volume:", total_vol)

# Train a model - no random_state set anywhere (REPRO-6 violation)
X = df[["id", "vol"]].values
y = df["val"].values

X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)
print("\nModel trained")
print("Score:", model.score(X_test, y_test))

df["predicted_val"] = model.predict(X)

# ARCH-12 violation 1: writing processed output BACK to bronze (must be immutable)
df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)
print("Saved back to bronze (overwrote raw source!)")

# ARCH-12 violation 2: no silver layer exists anywhere -- bronze jumps straight
# to a reporting dump with zero validation or aggregation in between
df.to_csv("data/output final.csv", index=False)
print("\nDone! Results saved to data/ (no gold layer, no silver layer).")
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Untitled.ipynb
**Confidence:** 0.95  |  **Risk score:** 2.85
**Evidence:** Notebook prints a dataframe containing identifier-like columns: `print(top)` after selecting `['name', 'salary', 'email']`, which would expose raw values in saved output or execution results.

**Suggested fix:** Remove raw PII from notebook outputs by masking or dropping identifier columns before printing the top earners dataframe.

```
top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']].copy()
top['name'] = '[REDACTED]'
top['email'] = '[REDACTED]'
print('Top earners by salary:')
print(top)
print('\nAverage salary:', customers['salary'].mean())
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.86  |  **Risk score:** 2.58
**Evidence:** Prints full dataframes to output, including `print(df)` and `print(customers)`, which can expose raw identifier-like values from the loaded data.

**Suggested fix:** Remove raw dataframe/customer prints and replace them with non-PII summaries only.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('print(df)\n', 'print(df.head())\n')
s = s.replace('print(customers)\n', 'print(customers.head())\n')
p.write_text(s)
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** Repo root name 'FinalProject' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root to follow the required naming convention.

```
git branch -m FinalProject fin-code-finalproject
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** pipeline.yml
**Confidence:** 0.99  |  **Risk score:** 1.98
**Evidence:** CI/CD YAML trigger includes non-approved branch names: "my-analysis-branch" and "hotfix"; policy allows only master, develop, or user-story/\d+.

**Suggested fix:** Restrict the pipeline trigger to approved branches only by replacing the non-compliant branch names with allowed patterns.

```
cat > pipeline.yml <<'YAML'
trigger:
  branches:
    include:
      - master
      - develop
      - user-story/*

pool:
  vmImage: ubuntu-latest

steps:
  - script: pip install -r requirements.txt
    displayName: Install deps
  - script: python final_v2_ACTUAL.py
    displayName: Run analysis
YAML
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** sql/create_tables.sql
**Confidence:** 0.99  |  **Risk score:** 1.98
**Evidence:** CREATE TABLE tbl_ethanol_market_rate, CREATE TABLE tbl_customers, and CREATE PROCEDURE sp_GetData use forbidden prefixes tbl_ and sp_; table names are also snake_case rather than PascalCase.

**Suggested fix:** Rename the tables and procedure to remove forbidden prefixes and use PascalCase object names.

```
CREATE TABLE EthanolMarketRate (
    id       INT          PRIMARY KEY,
    dt       DATE,
    val      DECIMAL(10,2),
    vol      DECIMAL(12,2)
);

CREATE TABLE Customers (
    id       INT          PRIMARY KEY,
    name     VARCHAR(100),
    email    VARCHAR(200),
    phone    VARCHAR(20),
    salary   DECIMAL(10,2)
);

CREATE PROCEDURE GetData
AS
BEGIN
    SELECT
        m.id,
        m.dt,
        m.val,
        m.vol,
        c.name,
        c.email,
        c.salary
    FROM EthanolMarketRate m
    JOIN Customers c ON m.id = c.id;
END;
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.98  |  **Risk score:** 1.96
**Evidence:** Uses stochastic training split with no seed: `train_test_split(X, y)  # no random_state!`; also overwrites the raw source file with `df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)`.

**Suggested fix:** Make the train/test split deterministic by setting a fixed random_state and stop overwriting the bronze source file by writing the processed output to a separate silver/gold path instead.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!', 'X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)')
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)\nprint("Saved back to bronze (overwrote raw source!)")', 'df.to_csv("silver/EthanolMarketRate_20240701_processed.csv", index=False)\nprint("Saved processed output to silver layer")')
p.write_text(s)
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Confidence:** 0.93  |  **Risk score:** 1.86
**Evidence:** Relies on `print()` statements for run progress and results, e.g. `print("Data loaded:")`, `print("Model trained")`, `print("Done! Results saved...")`, with no logging module or persistent metrics.

**Suggested fix:** Replace ad hoc print-based progress output with the logging module so run status and results are emitted through persistent logs.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = 'import logging\n' + s
s = s.replace('import pandas as pd\n', 'import pandas as pd\n')
s = s.replace('from sklearn.model_selection import train_test_split\n\n', 'from sklearn.model_selection import train_test_split\n\nlogging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\nlogger = logging.getLogger(__name__)\n\n')
repls = {
'print("Data loaded:")':'logger.info("Data loaded:")',
'print(df)':'logger.info("%s", df)',
'print("Shape:", df.shape)':'logger.info("Shape: %s", df.shape)',
'print("\\nCustomer list:")':'logger.info("Customer list:")',
'print(customers)':'logger.info("%s", customers)',
'print("\\nAverage price:", avg_price)':'logger.info("Average price: %s", avg_price)',
'print("Total volume:", total_vol)':'logger.info("Total volume: %s", total_vol)',
'print("\\nModel trained")':'logger.info("Model trained")',
'print("Score:", model.score(X_test, y_test))':'logger.info("Score: %s", model.score(X_test, y_test))',
'print("Saved back to bronze (overwrote raw source!)")':'logger.info("Saved back to bronze (overwrote raw source!)")',
'print("\\nDone! Results saved to data/ (no gold layer, no silver layer).")':'logger.info("Done! Results saved to data/ (no gold layer, no silver layer).")',
}
for a,b in repls.items():
    s = s.replace(a,b)
p.write_text(s)
PY
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** requirements.txt
**Confidence:** 0.91  |  **Risk score:** 1.82
**Evidence:** requirements.txt lists unpinned dependencies with no versions, e.g. 'pandas', 'sqlalchemy', 'numpy', 'jupyter', 'sklearn'.

**Suggested fix:** Pin all Python dependencies in requirements.txt to specific versions to make installs reproducible.

```
cat > requirements.txt <<'EOF'
pandas==2.2.2
sqlalchemy==2.0.32
numpy==2.0.1
jupyter==1.1.1
scikit-learn==1.5.1
EOF
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Untitled.ipynb
**Confidence:** 0.91  |  **Risk score:** 1.82
**Evidence:** The notebook relies on `print()` statements only (`print('Customer data:')`, `print(top)`, `print('Market data loaded')`) and contains no logging module usage or persistent run/error logging.

**Suggested fix:** Replace ad hoc print statements with persistent logging so notebook output is recorded via the logging module.

```
python - <<'PY'
import nbformat
from pathlib import Path

path = Path('Untitled.ipynb')
nb = nbformat.read(path, as_version=4)

nb.cells[0].source = """import pandas as pd
import logging

logging.basicConfig(filename='notebook.log', level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

customers = pd.read_csv('data/customers.csv')
logging.info('Customer data loaded')
logging.info('\n%s', customers.to_string(index=False))"""

nb.cells[1].source = """top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]
logging.info('Top earners by salary:\n%s', top.to_string(index=False))
logging.info('Average salary: %s', customers['salary'].mean())"""

nb.cells[2].source = """market = pd.read_csv('data/ethanol market rate.csv')
logging.info('Market data loaded')
logging.info('\n%s', market.head(2).to_string(index=False))"""

nbformat.write(nb, path)
PY
```

### DM-7 · Star schema / shared output table design [MEDIUM]

**Location:** sql/create_tables.sql
**Confidence:** 0.86  |  **Risk score:** 1.72
**Evidence:** The procedure joins two tables with no documented grain or primary key description: SELECT ... FROM tbl_ethanol_market_rate m JOIN tbl_customers c ON m.id = c.id;

**Suggested fix:** Document the shared grain by making the join key explicit and adding primary key comments for both tables/procedure output.

```
-- market rate table: grain = one row per market_rate.id
CREATE TABLE tbl_ethanol_market_rate (
    id       INT          PRIMARY KEY,
    dt       DATE,
    val      DECIMAL(10,2),
    vol      DECIMAL(12,2)
);

-- customer table: grain = one row per customer.id
CREATE TABLE tbl_customers (
    id       INT          PRIMARY KEY,
    name     VARCHAR(100),
    email    VARCHAR(200),
    phone    VARCHAR(20),
    salary   DECIMAL(10,2)
);

-- stored procedure output grain: one row per shared id
CREATE PROCEDURE sp_GetData
AS
BEGIN
    SELECT
        m.id,
        m.dt,
        m.val,
        m.vol,
        c.name,
        c.email,
        c.salary
    FROM tbl_ethanol_market_rate m
    INNER JOIN tbl_customers c
        ON m.id = c.id;
END;
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** (repository-level)
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** No README.md found at the repository root.

**Suggested fix:** Add a repository-root README.md to satisfy the naming convention requirement.

```
printf '# Project Title\n\nRepository overview.\n' > README.md
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/create_tables.sql
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** Column names include generic/cryptic and non-PascalCase identifiers such as id, dt, val, vol, name, email, phone, and salary.

**Suggested fix:** Rename the tables and columns in `sql/create_tables.sql` to use clear PascalCase identifiers instead of generic/cryptic names, and update the procedure to reference the new names.

```
CREATE TABLE EthanolMarketRate (
    MarketRateId INT PRIMARY KEY,
    RateDate     DATE,
    RateValue    DECIMAL(10,2),
    Volume       DECIMAL(12,2)
);

CREATE TABLE Customers (
    CustomerId INT PRIMARY KEY,
    FullName    VARCHAR(100),
    EmailAddress VARCHAR(200),
    PhoneNumber VARCHAR(20),
    AnnualSalary DECIMAL(10,2)
);

CREATE PROCEDURE GetData
AS
BEGIN
    SELECT
        m.MarketRateId,
        m.RateDate,
        m.RateValue,
        m.Volume,
        c.FullName,
        c.EmailAddress,
        c.AnnualSalary
    FROM EthanolMarketRate m
    JOIN Customers c ON m.MarketRateId = c.CustomerId;
END;
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline.yml
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** File path is "pipeline.yml"; pipeline file names must be CamelCase, and "pipeline" is also a vague name pattern not allowed.

**Suggested fix:** Rename the pipeline file to a CamelCase, non-vague name to satisfy the naming convention.

```
git mv pipeline.yml AnalysisPipeline.yml
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** File name 'ethanol market rate.csv' contains spaces and is not CamelCase.

**Suggested fix:** Rename the CSV file to CamelCase without spaces to comply with the naming convention.

```
mv "data/ethanol market rate.csv" data/EthanolMarketRate.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** Untitled.ipynb
**Confidence:** 0.97  |  **Risk score:** 0.97
**Evidence:** File path is `Untitled.ipynb`, which matches the vague name rule (`Untitled` is explicitly listed as NON_COMPLIANT). Also the CSV path `data/ethanol market rate.csv` contains spaces.

**Suggested fix:** Rename the notebook to a descriptive filename and update the CSV reference to a no-spaces path.

```
mv Untitled.ipynb customer_salary_analysis.ipynb && mv 'data/ethanol market rate.csv' data/ethanol_market_rate.csv && python - <<'PY'
from pathlib import Path
p = Path('customer_salary_analysis.ipynb')
text = p.read_text()
text = text.replace("data/ethanol market rate.csv", "data/ethanol_market_rate.csv")
p.write_text(text)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Confidence:** 0.97  |  **Risk score:** 0.97
**Evidence:** CSV headers include generic/cryptic names 'dt', 'id', 'val', and 'vol', which violate the column naming guidance.

**Suggested fix:** Rename the CSV headers to descriptive column names instead of generic abbreviations.

```
printf 'date,market_id,value,volume\n' > data/ethanol\ market\ rate.csv
```

## Compliant checks

4 checks passed. See machine_report.json for the full list.
