# Compliance Report — FinalProject

Run at: 2026-08-10T09:10:19.069632+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\non_compliant\FinalProject
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 39.7% (29/73 weighted checks)

> 6 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 57
- Applicable checks (compliant + non-compliant): 36
- COMPLIANT: 11
- NON_COMPLIANT: 25
- NOT_APPLICABLE: 21
- Requiring human action: 2

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 23
- NO_FIX_AVAILABLE: 2

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** Untitled.ipynb
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any intervening quality check.  Quoted: "customers = pd.read_csv('data/customers.csv')"

**Suggested fix:** Add a minimal data-quality validation check after loading customers before the data is used.

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
    "if customers[['name', 'salary', 'email']].isnull().any().any():\n",
    "    raise ValueError('customers data contains null values in required columns')\n",
    "print('Customer data:')\n",
    "print(customers)\n",
]
p.write_text(json.dumps(nb, indent=1))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** Untitled.ipynb
**Sample agreement:** 100%
**Evidence:** The notebook exposes raw PII by printing customer data that includes identifier fields such as email.  Quoted: 'print(customers)'

**Suggested fix:** Remove raw PII exposure by masking the email field before printing customer data and top earners.

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
    "print(customers.drop(columns=['email']))\n"
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

### DQ-1 · Data quality validation present [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for downstream processing without any prior quality check.  Quoted: 'df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")'

**Suggested fix:** Add a minimal data-quality validation check immediately after loading the CSV before any downstream processing.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")\nprint("Data loaded:")\nprint(df)\nprint("Shape:", df.shape)\n'
new = 'df = pd.read_csv("bronze/EthanolMarketRate_20240701.csv")\nif df.empty or df.isnull().any().any():\n    raise ValueError("Data quality check failed: empty dataset or missing values detected")\nprint("Data loaded:")\nprint(df)\nprint("Shape:", df.shape)\n'
if old not in text:
    raise SystemExit('Expected snippet not found')
path.write_text(text.replace(old, new, 1))
PY
```

### SEC-3 · No hardcoded secrets or credentials [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The script hardcodes credentials directly in source code.  Quoted: 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"'

**Suggested fix:** Remove the hardcoded database password and API key by replacing them with environment-variable lookups in final_v2_ACTUAL.py.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'connection_string = "mssql+pyodbc://admin:Tetra@dmin123!@prod-db.database.windows.net/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"\napi_key = "sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5"'
new = 'import os\n\nconnection_string = os.environ.get("DB_CONNECTION_STRING", "<SET_DB_CONNECTION_STRING>")\napi_key = os.environ.get("API_KEY", "<SET_API_KEY>")'
if old not in text:
    raise SystemExit('Expected secret block not found')
path.write_text(text.replace(old, new))
PY
```

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold) [HIGH]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The file violates medallion architecture by writing back to bronze and skipping the middle layer.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Move the processed output out of bronze and add an intermediate silver-layer write before the final report export.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)\nprint("Saved back to bronze (overwrote raw source!)")\n\n# ARCH-12 violation 2: no silver layer exists anywhere -- bronze jumps straight\n# to a reporting dump with zero validation or aggregation in between\ndf.to_csv("data/output final.csv")\nprint("\\nDone! Results saved to data/ (no gold layer, no silver layer).")\n', 'df.to_csv("silver/EthanolMarketRate_20240701.csv", index=False)\nprint("Saved processed data to silver layer")\n\n# Gold layer output\ndf.to_csv("gold/output_final.csv", index=False)\nprint("\\nDone! Results saved to gold/.")\n')
p.write_text(s)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** data/customers.csv
**Sample agreement:** 100%
**Evidence:** The CSV header exposes direct identifier columns name, email, and phone.  Quoted: 'name,email,phone,salary'

**Suggested fix:** Replace the raw PII column headers with non-identifying snake_case labels in the CSV header only.

```
sed -i '1s/.*/full_name,contact_email,contact_phone,salary/' data/customers.csv
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'FinalProject' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from FinalProject to a compliant name matching the required pattern, using a placeholder prefix if the intended domain is not derivable from the evidence.

```
mv FinalProject <prefix>-code-<name>
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** Untitled.ipynb
**Sample agreement:** 100%
**Evidence:** The file performs data work but leaves no durable log or monitoring record beyond print output.  Quoted: "print('Customer data:')"

**Suggested fix:** Add a durable notebook log by writing the existing customer and market summaries to a text file instead of relying only on print output.

```
python - <<'PY'
import json
from pathlib import Path

path = Path('Untitled.ipynb')
nb = json.loads(path.read_text())

# Cell 0
nb['cells'][0]['source'] = [
    "import pandas as pd\n",
    "\n",
    "customers = pd.read_csv('data/customers.csv')\n",
    "with open('ops_log.txt', 'a') as log:\n",
    "    log.write('Customer data:\\n')\n",
    "    log.write(customers.to_string(index=False))\n",
    "    log.write('\\n')\n",
    "print('Customer data:')\n",
    "print(customers)\n",
]

# Cell 1
nb['cells'][1]['source'] = [
    "top = customers.nlargest(3, 'salary')[['name', 'salary', 'email']]\n",
    "with open('ops_log.txt', 'a') as log:\n",
    "    log.write('Top earners by salary:\\n')\n",
    "    log.write(top.to_string(index=False))\n",
    "    log.write(f'\\nAverage salary: {customers[\'salary\'].mean()}\\n')\n",
    "print('Top earners by salary:')\n",
    "print(top)\n",
    "print('\\nAverage salary:', customers['salary'].mean())\n",
]

# Cell 2
nb['cells'][2]['source'] = [
    "market = pd.read_csv('data/ethanol market rate.csv')\n",
    "with open('ops_log.txt', 'a') as log:\n",
    "    log.write('Market data loaded\\n')\n",
    "    log.write(market.head(2).to_string(index=False))\n",
    "    log.write('\\n')\n",
    "print('Market data loaded')\n",
    "print(market.head(2))\n",
]

path.write_text(json.dumps(nb, indent=1))
PY
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The script relies on print output only and does not use persistent logging or metric tracking.  Quoted: 'print("Data loaded:")'

**Suggested fix:** Replace print-only status messages with persistent logging to a file while preserving the existing console output behavior.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
text = text.replace('import pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n', 'import logging\nimport pandas as pd\nimport numpy as np\nfrom sklearn.linear_model import LinearRegression\nfrom sklearn.model_selection import train_test_split\n\nlogging.basicConfig(filename="final_v2_ACTUAL.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")\n')
repls = {
    'print("Data loaded:")': 'logging.info("Data loaded:")\nprint("Data loaded:")',
    'print(df)': 'logging.info("%s", df.to_string())\nprint(df)',
    'print("Shape:", df.shape)': 'logging.info("Shape: %s", df.shape)\nprint("Shape:", df.shape)',
    'print("\\nCustomer list:")': 'logging.info("Customer list:")\nprint("\\nCustomer list:")',
    'print(customers)': 'logging.info("%s", customers.to_string())\nprint(customers)',
    'print("\\nAverage price:", avg_price)': 'logging.info("Average price: %s", avg_price)\nprint("\\nAverage price:", avg_price)',
    'print("Total volume:", total_vol)': 'logging.info("Total volume: %s", total_vol)\nprint("Total volume:", total_vol)',
    'print("\\nModel trained")': 'logging.info("Model trained")\nprint("\\nModel trained")',
    'print("Score:", model.score(X_test, y_test))': 'logging.info("Score: %s", model.score(X_test, y_test))\nprint("Score:", model.score(X_test, y_test))',
    'print("Saved back to bronze (overwrote raw source!)")': 'logging.info("Saved back to bronze (overwrote raw source!)")\nprint("Saved back to bronze (overwrote raw source!)")',
    'print("\\nDone! Results saved to data/ (no gold layer, no silver layer).")': 'logging.info("Done! Results saved to data/ (no gold layer, no silver layer).")\nprint("\\nDone! Results saved to data/ (no gold layer, no silver layer).")',
}
for old, new in repls.items():
    text = text.replace(old, new)
path.write_text(text)
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The train/test split is not seeded, so the run is not reproducible.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!'

**Suggested fix:** Seed the train/test split for reproducibility by adding a fixed random_state.

```
python - <<'PY'
from pathlib import Path
path = Path('final_v2_ACTUAL.py')
text = path.read_text()
old = 'X_train, X_test, y_train, y_test = train_test_split(X, y)  # no random_state!\n'
new = 'X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)  # seeded for reproducibility\n'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new, 1))
PY
```

### REPRO-14 · Raw source data not modified in place [MEDIUM]

**Location:** final_v2_ACTUAL.py
**Sample agreement:** 100%
**Evidence:** The raw bronze file is overwritten in place after being read.  Quoted: 'df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)'

**Suggested fix:** Redirect the processed CSV output to a non-bronze file so the raw bronze source is not overwritten in place.

```
python - <<'PY'
from pathlib import Path
p = Path('final_v2_ACTUAL.py')
s = p.read_text()
s = s.replace('df.to_csv("bronze/EthanolMarketRate_20240701.csv", index=False)', 'df.to_csv("data/output final.csv", index=False)')
s = s.replace('print("Saved back to bronze (overwrote raw source!)")', 'print("Saved processed output to data/output final.csv")')
s = s.replace('df.to_csv("data/output final.csv")\nprint("\\nDone! Results saved to data/ (no gold layer, no silver layer).")', 'print("\\nDone! Results saved to data/output final.csv.")')
p.write_text(s)
PY
```

### GIT-8 · Git branching and commit standards [MEDIUM]

**Location:** pipeline.yml
**Sample agreement:** 100%
**Evidence:** The configured trigger branches violate the allowed branch naming standard.  Quoted: '- main\n      - my-analysis-branch\n      - hotfix'

**Suggested fix:** Update the pipeline trigger branches to use only allowed branch names by removing the noncompliant analysis branch.

```
python - <<'PY'
from pathlib import Path
p = Path('pipeline.yml')
text = p.read_text()
text = text.replace('      - my-analysis-branch\n', '')
p.write_text(text)
PY
```

### SQL-10 · SQL table and object naming convention [MEDIUM]

**Location:** sql/create_tables.sql
**Sample agreement:** 67%
**Evidence:** The SQL object names violate naming rules by using the forbidden tbl_ and sp_ prefixes and non-PascalCase names.  Quoted: 'CREATE TABLE tbl_ethanol_market_rate'  [2/3 samples agreed: NEEDS_REVIEWx1, NON_COMPLIANTx2]

**Suggested fix:** Rename the SQL tables and procedure to PascalCase without the forbidden tbl_/sp_ prefixes, and update the procedure body to reference the new object names.

```
sed -i -e 's/CREATE TABLE tbl_ethanol_market_rate/CREATE TABLE EthanolMarketRate/' -e 's/CREATE TABLE tbl_customers/CREATE TABLE Customers/' -e 's/CREATE PROCEDURE sp_GetData/CREATE PROCEDURE GetData/' -e 's/FROM tbl_ethanol_market_rate m/FROM EthanolMarketRate m/' -e 's/JOIN tbl_customers c/JOIN Customers c/' sql/create_tables.sql
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
# Preserve order and replace each unpinned requirement with an explicit placeholder pin.
# Exact versions cannot be derived from the provided file content.
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
**Evidence:** The CSV headers violate the naming convention because they are cryptic single-token names.  Quoted: 'dt,id,val,vol'

**Suggested fix:** Rename the CSV headers to descriptive snake_case names while preserving the data rows.

```
python - <<'PY'
from pathlib import Path
p = Path('bronze/EthanolMarketRate_20240701.csv')
text = p.read_text()
lines = text.splitlines()
lines[0] = 'date,market_id,market_value,market_volume'
p.write_text('\n'.join(lines) + ('\n' if text.endswith('\n') else ''))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/ethanol market rate.csv
**Sample agreement:** 100%
**Evidence:** The CSV header uses cryptic single-token column names that violate the naming convention.  Quoted: 'dt,id,val,vol'

**Suggested fix:** Rename the CSV header to snake_case descriptive column names while preserving the data rows.

```
sed -i '1s/.*/date,identifier,value,volume/' 'data/ethanol market rate.csv'
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/create_tables.sql
**Sample agreement:** 67%
**Evidence:** The column definitions violate naming rules with non-PascalCase and cryptic names such as dt, val, and vol.  Quoted: 'dt       DATE,'  [2/3 samples agreed: NEEDS_REVIEWx1, NON_COMPLIANTx2]

**Suggested fix:** Rename SQL table columns to PascalCase and replace cryptic names with clearer equivalents in the CREATE TABLE and SELECT statements.

```
sed -i -e 's/\bid       INT          PRIMARY KEY,/Id       INT          PRIMARY KEY,/' -e 's/\bdt       DATE,/Date       DATE,/' -e 's/\bval      DECIMAL(10,2),/Value      DECIMAL(10,2),/' -e 's/\bvol      DECIMAL(12,2)/Volume      DECIMAL(12,2)/' -e 's/\bm\.id,/m.Id,/' -e 's/\bm\.dt,/m.Date,/' -e 's/\bm\.val,/m.Value,/' -e 's/\bm\.vol,/m.Volume,/' -e 's/\bc\.name,/c.Name,/' -e 's/\bc\.email,/c.Email,/' -e 's/\bc\.salary,/c.Salary,/' sql/create_tables.sql
```

## Checks that passed or did not apply

11 checks passed; 21 did not apply to this repository. See machine_report.json for the full list.
