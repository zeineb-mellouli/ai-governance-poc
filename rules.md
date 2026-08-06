# Governance Constitution — Data Pipeline Rules

> Auto-generated from `policies/policies.yaml`.
> **Do not edit manually** — run `python generate_rules_md.py` to regenerate.

---

## Part 1 — Hard rules (apply unconditionally to every file in every repo)

### SEC-3 · No hardcoded secrets or credentials  [HIGH]

API keys, database connection strings, tokens, and passwords must never appear directly in code or notebook cells, committed or not.

**Applies to:** `**/*`
**Except:** `.env.example`, `.env.template`, `.env.sample`, `*.example`, `*.template`, `*.sample`
**Decided by:** model

**Rule:**

A literal credential value that could actually authenticate a system is a violation wherever it appears: an API key, a token, a password, or a connection string with an embedded password. Reading from os.environ / os.getenv or a secrets manager is compliant. A placeholder is not a credential -- <PLACEHOLDER>, REPLACE_ME, your-value-here, xxx, or an empty KEY= documents what is required without exposing anything.

**Compliant examples:**

- `api_key = os.environ['API_KEY']`
- `DB_PASSWORD=<secret-never-commit>`

**Non-compliant examples:**

- `api_key = 'sk-prod-xK92mNpL4rTvQw8jYeB3fHdA6cUoZiG5'`
- `postgresql://admin:Hunter2@prod-db/warehouse`

---

### DM-7 · Shared output table grain documentation  [MEDIUM]

Any dataset published to the gold/reporting layer is consumed by people and systems outside the pipeline that produced it. Each must state its grain -- what exactly one row represents -- somewhere a consumer can find it. Without that, downstream joins silently double-count.

**Applies to:** the repository as a whole
**Decided by:** model

**Rule:**

This is a whole-repository check. Enumerate every gold/reporting/curated/ datamart output path the repository writes, and every CREATE TABLE with a Dim or Fact suffix. For each, look for a grain statement in ANY file: the writing module's docstring or comments, the README, or the table's DDL. A grain statement names what one row is -- "one row per counterparty per day". A statement of what the table is FOR is a purpose, not a grain. COMPLIANT if every such output has a grain statement somewhere. NON_COMPLIANT if at least one has none anywhere -- name the output path and the files you checked. Does not apply to bronze, silver, staging, or logs, nor to exploratory notebooks.

**Compliant examples:**

- `-- Grain: one row per product per market date`

**Non-compliant examples:**

- `gold/MarginCallReport.csv written; no file states what one row is`

---

### REPO-9 · Repository naming convention  [MEDIUM]

Repository names follow {department}-{resource}-{project_name}. Department is one of aud, fin, gfp, ops, tax. Resource is one of code, sql, synapse. Project name is snake_case. Examples: aud-code-cyber_security, ops-sql-market_rate, fin-synapse-capital_structure.

**Applies to:** the repository as a whole
**Decided by:** deterministic

**Rule:**

^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Compliant examples:**

- `fin-code-liquidity_forecast`
- `ops-sql-market_rate`

**Non-compliant examples:**

- `FinalProject`
- `code-polymer`
- `market-analysis`

---

### REPRO-13 · Dependency versions pinned  [LOW]

A project cannot be rebuilt as it was unless its dependency versions are recorded. A lockfile (requirements.lock, poetry.lock, uv.lock, Pipfile.lock, conda-lock.yml, pdm.lock) satisfies this on its own, since that is where transitive versions belong; without one, every package named in the manifest must carry an exact version. Severity is LOW deliberately. Standard Python packaging guidance separates the abstract dependency list from the lockfile and discourages exact pins in the former for libraries, so this is reproducibility hygiene rather than a control on par with a missing data quality gate.

**Applies to:** the repository as a whole
**Decided by:** deterministic

**Rule:**

Every package in requirements*.txt, environment.yml or pyproject.toml carries an exact version, or the repository has a lockfile.

**Compliant examples:**

- `pandas==2.1.4`
- `poetry.lock present`

**Non-compliant examples:**

- `scikit-learn`
- `pandas>=2.0`
- `statsmodels`

---

## Part 2 — Conditional rules (check `applies_when` before evaluating)

### DQ-1 · Data quality validation present  [HIGH]

Before data is written downstream or used for analysis/training, it should be checked for basic quality issues -- missing values, duplicates, out-of-range values, leakage -- rather than trusted blindly.

**Applies to:** `**/*.py`, `**/*.ipynb`, `**/*.sql`
**Except:** `test_*.py`, `*_test.py`, `conftest.py`, `__init__.py`
**Decided by:** model

**Rule:**

Data that is loaded and then used further -- written to a table, aggregated, feature-engineered, or used to train a model -- must pass a quality check first. Any of these counts: a Lakeflow expectation decorator (@dp.expect_all, @dp.expect_all_or_drop, @dp.expect_all_or_fail) or CONSTRAINT ... EXPECT clause; a Great Expectations, pandera, or PyDeequ call; or an explicit assert / raise / filter on null counts, duplicate counts, value ranges, or train-test leakage. A file that only defines structure (CREATE TABLE / VIEW / INDEX, ALTER, DROP) loads no data and this does not apply to it.

**Compliant examples:**

- `@dp.expect_all_or_drop({'valid_price': 'price > 0'})`
- `schema.validate(df)  # pandera`
- `assert df['customer_id'].notna().all(); assert not df.duplicated().any()`

**Non-compliant examples:**

- `df = pd.read_csv(src); df.to_parquet(dest)  # nothing checked in between`

---

### PII-4 · No raw PII exposed in outputs  [HIGH]

Data containing direct identifiers (names, emails, etc.) should never appear in a saved notebook output, a print statement, or a log line -- regardless of access controls on the source data. Committed identifier data is an exposure whether or not any code prints it.

**Applies to:** `**/*.py`, `**/*.ipynb`, `**/*.csv`, `**/*.parquet`
**Except:** `test_*.py`, `*_test.py`, `conftest.py`
**Decided by:** model

**Rule:**

Two things are violations. (1) A committed CSV/Parquet whose header carries a direct identifier -- name, full_name, first_name, last_name, email, phone, ssn, address, date_of_birth, or an obvious equivalent. Name the offending columns. Clearly synthetic, masked, or placeholder values are not an exposure. (2) Raw identifier values visible in a saved notebook output, a print, or a log line. Masking or redacting before display, sampling synthetic data, or clearing outputs before commit is compliant. A test that asserts an identifier does NOT appear in a log is a guardrail, not an exposure.

**Compliant examples:**

- `print(df[['customer_id', 'region']].head())`
- `customer_id,region,volume_tonnes`

**Non-compliant examples:**

- `customer_id,full_name,email,phone`
- `logger.info('processing %s', row['email'])`

---

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold)  [HIGH]

Bronze holds raw ingested data. Silver holds validated, cleansed, deduplicated data. Gold holds aggregated, business-ready data. Data flows Bronze -> Silver -> Gold with no layer skipped.

**Applies to:** `**/*.py`, `**/*.ipynb`, `**/*.sql`
**Except:** `test_*.py`, `*_test.py`, `conftest.py`, `__init__.py`
**Decided by:** model

**Rule:**

Treat silver, cleansed, curated, refined, staging, validated and processed as the same middle layer, whatever the folder is called, including when a README maps a folder to a layer. Violations: (1) no layer separation at all -- every write lands in one undifferentiated location, e.g. final output written back beside the raw input; (2) a layer skip -- code reads a bronze/raw path and writes straight to a gold/reporting path with no middle-layer step; (3) a write into the middle layer with no data quality validation immediately before it. A silver -> gold write is the correct flow. Never flag it here, even if it performs no validation and no aggregation: validation before a gold write is DQ-1's concern. There is no quality gate before gold in this policy. Does not apply to a file with no tiered storage paths, or to a pure schema definition file.

**Compliant examples:**

- `df = read('bronze/x.csv'); validate(df); write('silver/x.csv')`
- `df = read('silver/x.csv'); write('gold/Summary.csv')`

**Non-compliant examples:**

- `df = read('bronze/x.csv'); write('gold/Report.csv')  # skips silver`
- `df = read('bronze/x.csv'); write('silver/x.csv')  # no validation`

---

### OPS-2 · Logging and monitoring  [MEDIUM]

Any pipeline job or model training run should log progress and errors in a way that persists after the session ends, rather than relying on terminal output or print statements.

**Applies to:** `**/*.py`, `**/*.ipynb`
**Except:** `test_*.py`, `*_test.py`, `conftest.py`, `__init__.py`
**Decided by:** model

**Rule:**

A pipeline job or training run must leave a record that outlives the session. Look for the logging module rather than print() alone, an error path that logs the exception (logger.error / logger.exception) rather than swallowing it, and -- for a training loop -- metrics written somewhere queryable (MLflow, Weights & Biases, a log file) rather than only printed.

**Compliant examples:**

- `logging.basicConfig(filename='logs/run.log'); logger.exception('load failed')`
- `mlflow.log_metric('auc', auc)`

**Non-compliant examples:**

- `print('done')  # only output, and `except: pass` on the error path`

---

### REPRO-6 · Random seeds fixed for stochastic steps  [MEDIUM]

A result produced by a stochastic step cannot be reproduced by anyone else unless the seed is fixed. Split REPRO-6 (was a three-in-one policy) so that seeding, dependency pinning (REPRO-13) and raw-data immutability (REPRO-14) are judged separately, on the files where each is visible.

**Applies to:** `**/*.py`, `**/*.ipynb`
**Except:** `test_*.py`, `*_test.py`, `conftest.py`, `__init__.py`
**Decided by:** model

**Rule:**

Every stochastic step in this file must have its randomness fixed: a train/test split, a sample, a shuffle, a weight initialisation, or a simulation. Any of np.random.seed, random.seed, random_state=, torch.manual_seed, or a framework equivalent counts, and it must cover the call that actually uses randomness -- np.random.seed does not seed sklearn's train_test_split, which needs its own random_state. Judge only this file. If it performs no stochastic operation, this does not apply. Dependency versions are REPRO-13's concern, not yours.

**Compliant examples:**

- `train_test_split(X, y, test_size=0.2, random_state=42)`
- `np.random.seed(42); np.random.normal(size=1000)`

**Non-compliant examples:**

- `train_test_split(X, y, test_size=0.2)  # no random_state`

---

### GIT-8 · Git branching and commit standards  [MEDIUM]

Three-tier Git workflow: master (stable), develop (integration), user-story/{id} (feature work). Commit messages use conventional prefixes (feat:, fix:, chore:, docs:, refactor:) and each commit is atomic. Pull requests link to a user story and require at least one reviewer.

**Applies to:** `azure-pipelines.yml`, `.github/workflows/*.yml`, `.github/workflows/*.yaml`, `PULL_REQUEST_TEMPLATE.md`, `**/PULL_REQUEST_TEMPLATE.md`, `CONTRIBUTING.md`
**Decided by:** model

**Rule:**

Branch names configured in this file must be master, develop, or user-story/<number>. Anything else (hotfix-thing, feature/xyz, test) is a violation. In a PR template or contribution guide, check that at least one reviewer is required and a user story is referenced. {id} or {number} is a valid numeric placeholder, not a bad branch name.

**Compliant examples:**

- `trigger:
  branches:
    include: [master, develop]`
- `user-story/{id}`

**Non-compliant examples:**

- `trigger:
  branches:
    include: [master, hotfix-urgent-fix]`

---

### SQL-10 · SQL table and object naming convention  [MEDIUM]

SQL tables, views and stored procedures are PascalCase with no Hungarian prefixes. Data model tables carry a Dim or Fact suffix. Stored procedures contain a verb. Approved schemas: Staging, Production, MetaData, Logging, Config, Reporting, PowerBI, DataMart.

**Applies to:** `**/*.sql`, `**/*.py`, `**/*.ipynb`
**Decided by:** model

**Rule:**

Judge SQL object definitions only -- CREATE TABLE / VIEW / PROCEDURE, including SQL embedded in Python strings. Violations: (1) a table or view name not in PascalCase; (2) a Hungarian prefix -- tbl_, vw_, sp_, fn_, udf_; (3) a data model table missing a Dim or Fact suffix, or carrying it as a prefix (DimCustomer, FactSales are wrong; CustomerDim, SalesFact right); (4) a stored procedure whose object name uses Create, Delete or Drop as its verb -- this is about the name after CREATE PROCEDURE, never the .sql filename; (5) a schema outside the approved list, or using underscores, or over 30 characters; (6) a table whose name exactly matches one of its own columns.

**Compliant examples:**

- `Reporting.EthanolMarketRateFact`
- `Production.EthanolLoadMarketRate`

**Non-compliant examples:**

- `tbl_ethanol`
- `ethanol_market_rate`
- `Reporting.DimCustomer`

---

### REPRO-14 · Raw source data not modified in place  [MEDIUM]

A pipeline that overwrites its own input cannot be re-run, and the original data is gone. Raw and source data must be treated as read-only by everything downstream of ingestion. This rule previously lived inside ARCH-12 as "bronze immutability", where it only fired on repositories that happened to use medallion layer names; it applies just as much to a repository with no layers at all.

**Applies to:** `**/*.py`, `**/*.ipynb`
**Except:** `test_*.py`, `*_test.py`, `conftest.py`, `__init__.py`
**Decided by:** model

**Rule:**

A transformation, load or analysis step must not write back over the data it read. Flag it when this file reads a raw/source/bronze/landing path and then writes to that same path, or deletes or truncates it. Ingestion code writing a raw path for the first time is correct and is not a violation. Judge only paths visible in this file.

**Compliant examples:**

- `df = pd.read_csv('bronze/x.csv'); df.to_csv('silver/x.csv')`

**Non-compliant examples:**

- `df = pd.read_csv('bronze/x.csv'); df.to_csv('bronze/x.csv')`

---

### NAM-5 · File and folder naming convention  [LOW]

Dataset and file names are CamelCase. Folders use <Project>_<Feature> (e.g. Polymers_MarketRate). File names follow <DatasetName>_<yyyy-MM-dd>. Names begin with a letter, contain only letters, numbers and underscores (hyphens only inside the date), have no consecutive underscores, no spaces, and no vague tokens (Untitled, final, copy, v2, ACTUAL, temp). A README at the repository root is required. Column names in data files are snake_case and singular.

**Applies to:** `**/*.csv`, `**/*.parquet`
**Decided by:** hybrid

**Rule:**

Judge ONLY the CSV/Parquet column headers. Headers must be snake_case and the entity noun must be singular -- judge the head noun alone. A plural unit of measure (tonnes, days, months) or a multi-word qualifier is not a plural entity. Also flag a cryptic single-token header with no qualifier (dt, id, val, vol, num, qty, col1, flag). snake_case is the required form here. Never propose CamelCase, PascalCase, or kebab-case for a data-file column.

**Compliant examples:**

- `customer_id`
- `source_region`
- `volume_tonnes`
- `realized_vol_10d`

**Non-compliant examples:**

- `customerID`
- `CustomerId`
- `customers`
- `customer-id`
- `dt`
- `val`

---

### SQL-11 · SQL column naming convention  [LOW]

SQL columns are PascalCase and singular. Date and time columns qualify what the date represents. The Key suffix is reserved for primary and foreign keys in Dim/Fact tables.

**Applies to:** `**/*.sql`, `**/*.py`, `**/*.ipynb`
**Decided by:** model

**Rule:**

Judge SQL column definitions only -- CREATE TABLE, ALTER TABLE ADD COLUMN, or DataFrame columns destined for a SQL table. Violations: (1) a column not in PascalCase (start_date, customer_id); (2) a generic or cryptic name -- standalone Id, Dt, Col, Val, Num, Flag, Qty, Amt with no qualifier; (3) a date/time column named Date, Time, Timestamp or CreatedAt with no qualifier describing the business event (OrderDate is fine); (4) the Key suffix on a non-key column; (5) a plural column name.

**Compliant examples:**

- `CustomerKey`
- `OrderDate`
- `VarAmount`

**Non-compliant examples:**

- `customer_id`
- `Dt`
- `Orders`
- `StatusKey`

---
