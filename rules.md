# Governance Constitution — Data Pipeline Rules

> Auto-generated from `policies/policies.yaml`.
> **Do not edit manually** — run `python generate_rules_md.py` to regenerate.

---

## Part 1 — Hard rules (apply unconditionally to every file in every repo)

### SEC-3 · No hardcoded secrets or credentials  [HIGH]

API keys, database connection strings, tokens, and passwords must never appear directly in code or notebook cells, committed or not.

**Applies when:** Every repo.

**How to evaluate:**

Search all code and notebook cells for patterns resembling API keys, connection strings with embedded passwords, or tokens (e.g. postgresql://user:password@host, api_key = "sk-...", hardcoded AWS credentials). Environment variable usage (os.environ, os.getenv) or a secrets manager reference is compliant. A literal credential value assigned directly in code is NON_COMPLIANT regardless of repo visibility.

---

### REPO-9 · Repository naming convention  [MEDIUM]

Repository names must follow the pattern: {department}-{resource}-{project_name}. Department is a 3-letter lowercase code: aud (audit), fin (finance), gfp (gfpr), ops (operations), tax (tax). Resource is one of: code, sql, synapse. Project name uses snake_case with underscores separating words. Hyphens separate the three components. No uppercase, no spaces. Examples: aud-code-cyber_security, ops-sql-market_rate, fin-synapse-capital_structure.

**Applies when:** Every repo -- evaluate the root directory or repository name.

**How to evaluate:**

Inspect the repository root folder name or the name field in any project config (pyproject.toml, setup.cfg, package.json, azure-pipelines.yml). Validate against the pattern: ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$ Flag NON_COMPLIANT if: (1) the department segment is not one of the five allowed codes (e.g. "operations", "finance", "audit" in full are violations); (2) the resource type is missing, wrong, or abbreviated differently; (3) the project_name uses hyphens instead of underscores, contains uppercase letters, or starts with a digit; (4) the separators between the three segments are not single hyphens; (5) the name is completely free-form with no recognisable structure (e.g. "FinalProject", "market-analysis", "my_repo").

---

### NAM-5 · File and folder naming convention  [LOW]

All files and folders must follow the organisation's naming convention. Dataset and file names are written in CamelCase. Folder structure uses the pattern <Project>_<Feature> (e.g. Polymers_MarketRate). File names follow <DatasetName>_<yyyyMMdd> (e.g. EthanolMarketRate_20240701.csv). Rules that apply to all names: begin with a letter; do not end with an underscore; only letters, numbers, and underscores; no consecutive underscores; no spaces; max 126 characters; avoid abbreviations unless commonly understood. Column names in data files (CSV, Parquet) use snake_case and are always singular. A README describing the project's purpose and structure is required at the repository root.

**Applies when:** Every repo.

**How to evaluate:**

Inspect all filenames, folder names, and data file column headers for: (1) CamelCase on dataset/file names -- flag snake_case, all-lowercase, or space-separated file names as NON_COMPLIANT (e.g. ethanol_market_rate.csv or "Ethanol Market Rate.csv" are violations; EthanolMarketRate_20240701.csv is compliant); (2) date suffixes must be yyyyMMdd format -- flag yyyy-MM-dd, dd-MM-yyyy, or any other variant as NON_COMPLIANT; (3) folder names following <Project>_<Feature> -- flag a flat root with no project/feature separation as NON_COMPLIANT; (4) vague or versioned names anywhere in the tree: Untitled, final, copy, v2, ACTUAL, temp, test123 -- flag as NON_COMPLIANT; (5) names ending with underscore, containing consecutive underscores, or containing spaces -- flag as NON_COMPLIANT; (6) names starting with a digit or special character -- flag as NON_COMPLIANT; (7) data file column headers not in snake_case, or plural column names (e.g. customers, products) -- flag as NON_COMPLIANT; (8) missing README.md at the repository root -- flag as NON_COMPLIANT.

---

## Part 2 — Conditional rules (check `applies_when` before evaluating)

### DQ-1 · Data quality validation present  [HIGH]

Before data is written downstream or used for analysis/training, it should be checked for basic quality issues -- missing values, duplicates, out-of-range values, leakage -- rather than trusted blindly.

**Applies when:** Any code that loads a dataset and then uses it further: writes it to a table, uses it for feature engineering, or trains a model on it.

**How to evaluate:**

Search for validation logic appearing after data is loaded and before it is used further. Any of the following counts as compliant: (a) Databricks Lakeflow expectation decorators (@dp.expect_all, @dp.expect_all_or_drop, @dp.expect_all_or_fail) or a CONSTRAINT ... EXPECT clause; (b) a Great Expectations, pandera, or PyDeequ validation call; (c) explicit programmatic checks (assert / raise / filter) validating null counts, duplicate counts, value ranges, or train/test leakage. If data is loaded and used with no such checks anywhere in the file, flag NON_COMPLIANT.

---

### PII-4 · No raw PII exposed in outputs  [HIGH]

Data containing direct identifiers (names, emails, etc.) should never appear in a saved notebook output, a print statement, or a log line -- regardless of access controls on the source data.

**Applies when:** Any code that loads data containing potential direct identifiers (name, email, ssn, phone, address) and displays, prints, or logs it.

**How to evaluate:**

Check saved notebook cell outputs and any print()/log statements for dataframes or values containing identifier-like columns with real-looking, non-masked, non-synthetic values visible. Using .head() on a masked or synthetic sample, redacting before display, or clearing notebook outputs before commit is compliant. Flag NON_COMPLIANT if raw identifier values are visible in a saved output or a print/log statement.

---

### ARCH-12 · Medallion architecture (Bronze / Silver / Gold)  [HIGH]

Data pipelines must follow the three-layer medallion architecture. Bronze: raw ingested data, written once and never modified -- the immutable source of truth. Silver: validated, cleansed, and deduplicated data -- data quality checks (null counts, duplicates, schema validation) must be applied before any write to this layer. Gold: aggregated, business-ready data consumed by reporting, analytics, or downstream teams. Data must flow strictly in order (Bronze → Silver → Gold); no layer may be skipped. Bronze paths must never be overwritten or deleted by transformation or load code.

**Applies when:** Any pipeline, notebook, or script that reads from or writes to a data lake, Delta Lake, Azure Data Lake Storage, or any structured multi-stage storage system (e.g. Databricks Unity Catalog, ADLS Gen2 containers, local tiered folders). Not applicable to standalone model training scripts or exploratory notebooks with no storage layer references.

**How to evaluate:**

Check path strings, schema names, container names, and folder references throughout the code for: (1) Presence of three distinct layers -- look for names or paths containing bronze/silver/gold, raw/cleansed/curated, landing/refined/reporting, or equivalent tiered labels. Flag as NON_COMPLIANT if all writes go to a single undifferentiated location with no layer separation (e.g. writing final output directly to the same folder as raw input); (2) Layer ordering -- flag as NON_COMPLIANT if code reads from a bronze/raw path and writes directly to gold/reporting without any silver/cleansed intermediate step (layer skipping); (3) Bronze immutability -- flag as NON_COMPLIANT if any transformation, overwrite, or delete operation targets a bronze/raw path (bronze writes should only come from ingestion code, never from transform or load steps); (4) Silver quality gate -- flag as NON_COMPLIANT if code writes to a silver/cleansed path without data quality validation logic immediately preceding the write (see DQ-1 for what counts as validation); (5) Gold aggregation -- flag as NON_COMPLIANT if a gold/reporting path receives raw, un-aggregated rows directly from bronze without any grouping, aggregation, or enrichment step. Return NOT_APPLICABLE if the code has no references to tiered storage paths or schemas.

---

### OPS-2 · Logging and monitoring  [MEDIUM]

Any pipeline job or model training run should log progress and errors in a way that persists after the session ends, rather than relying on terminal output or print statements.

**Applies when:** Any pipeline expected to run on a schedule or unattended, and any model training or long batch-processing run.

**How to evaluate:**

Search for use of Python's logging module rather than exclusive reliance on print(). Check for: (1) a log or metric call marking the start and end of a run; (2) exception handling that logs the error (logger.error / logger.exception) rather than a bare except: pass; (3) if a training loop, whether metrics are captured somewhere persistent (MLflow, Weights & Biases, a logged file, or a queryable event log) rather than only printed to screen. Flag NON_COMPLIANT if the file relies only on print() with no persistent record and no error-path logging.

---

### REPRO-6 · Reproducibility  [MEDIUM]

A project's results should be reproducible by someone other than the original author: pinned dependencies, fixed random seeds, immutable raw data.

**Applies when:** Any code involving model training, random sampling, or statistical analysis with a stochastic component.

**How to evaluate:**

Check for: (1) a requirements.txt, environment.yml, or pyproject.toml with pinned, not floating/unversioned, package versions; (2) random seeds explicitly set for any stochastic step (np.random.seed, random.seed, random_state= in sklearn, or framework equivalents); (3) raw data read-only or copied rather than transformed in place. Flag NON_COMPLIANT if dependencies are unpinned, no random seed is set anywhere in a training/sampling step, or raw source files are directly overwritten by processing code.

---

### DM-7 · Star schema / shared output table design  [MEDIUM]

When code produces a structured table meant for reuse by other people or systems, it should have a clear key, documented columns, and no ambiguous duplicates -- this is the one policy that is genuinely conditional, not universal.

**Applies when:** Only when the code writes a structured table or file explicitly intended for reuse outside itself: a shared database table, a feature store, or an output meant for another team or pipeline to consume. Does NOT apply to exploratory notebooks, one-off analysis, or intermediate files never intended for reuse -- return NOT_APPLICABLE for those rather than a compliance verdict.

**How to evaluate:**

First check whether the code writes such a reusable output. If not, return NOT_APPLICABLE. If it does, check: (1) is the grain or primary key documented (comment, docstring, or README); (2) do joins use a stable surrogate/generated key rather than a raw natural key; (3) is any foreign/join key ever allowed to be null without an explicit "unknown" fallback; (4) is there documentation describing what one row represents. Flag NON_COMPLIANT only if these basics are missing on a table genuinely meant for reuse.

---

### GIT-8 · Git branching and commit standards  [MEDIUM]

All repositories must follow the standard three-tier Git workflow. Branches: master (always stable, production-ready), develop (integration before release), user-story/{id} (feature work, where id is the numeric DevOps user-story number). Commit messages must use conventional prefixes (feat:, fix:, chore:, docs:, refactor:) and each commit must be atomic -- one logical change per commit. Pull requests must link to a user story, require at least one reviewer before merging, and must have all conflicts resolved.

**Applies when:** Any repository with a .git directory, a CI/CD configuration file (azure-pipelines.yml, .github/workflows/*.yml), or a PR/commit template.

**How to evaluate:**

Check for: (1) CI/CD YAML files referencing branches -- flag any branch name that is not master, develop, or matching user-story/\d+ as NON_COMPLIANT (e.g. hotfix-thing, my-branch, test, feature/xyz are violations); (2) a PR template or CONTRIBUTING.md -- if present, check it enforces at least one reviewer and references a user story; (3) any commit message samples or git log snippets -- flag messages without a conventional prefix (feat:, fix:, chore:, docs:, refactor:) or messages that bundle multiple unrelated changes in one commit; (4) if a branch protection config file exists, check that master and develop require reviews before merge. Flag NON_COMPLIANT for any deviation from the three-tier branch model or missing review requirement.

---

### SQL-10 · SQL table and object naming convention  [MEDIUM]

SQL tables, views, and stored procedures must follow PascalCase naming. No Hungarian notation prefixes are permitted (no tbl_, vw_, sp_). Table structure: <Schema>.<ProjectName><DatasetName><AdditionalInfo>. Data model tables must carry a Dim or Fact suffix (e.g. Reporting.EthanolMarketRateFact). Stored procedures must contain a verb and follow <Schema>.<ProjectName><Verb><DatasetName> (e.g. Production.EthanolLoadMarketRate). Schemas must be PascalCase, alphanumeric only, max 30 characters. Approved core schemas: Staging, Production, MetaData, Logging, Config. Approved data model schemas: Reporting, PowerBI, DataMart. A table must never share its name with any of its columns.

**Applies when:** Any .sql file or Python/notebook code that contains SQL DDL (CREATE TABLE, CREATE VIEW, CREATE PROCEDURE) or DML referencing named SQL objects.

**How to evaluate:**

Scan .sql files and SQL strings embedded in .py or .ipynb files for: (1) table or view names not in PascalCase -- flag all-lowercase or snake_case names (e.g. ethanol_market_rate, tbl_ethanol) as NON_COMPLIANT; (2) any Hungarian notation prefix: tbl_, vw_, sp_, fn_, udf_ -- flag as NON_COMPLIANT regardless of the rest of the name; (3) data model tables (used in star-schema joins with dimension/fact relationships) missing the Dim or Fact suffix -- flag as NON_COMPLIANT; (4) stored procedures lacking a verb in their name, or using a forbidden verb like Create or Creating -- flag as NON_COMPLIANT; (5) schema names not in the approved list or that use underscores or exceed 30 characters -- flag as NON_COMPLIANT; (6) any table whose name exactly matches one of its own column names -- flag as NON_COMPLIANT. Return NOT_APPLICABLE if no SQL object definitions are present.

---

### SQL-11 · SQL column naming convention  [LOW]

SQL table columns must be written in PascalCase and use singular names. Date and time columns must be descriptive -- they must qualify what the date represents (e.g. StartDate, CallEndDate, ProcessedDate) rather than generic names like Date, Dt, or Timestamp. The suffix Key is reserved exclusively for primary and foreign keys in data model (Dim/Fact) tables (e.g. PipelineKey, CountryKey, CustomerKey). Using bare Id as the sole primary key identifier should be avoided; prefer a qualified name (CustomerId, PipelineId) or a Key-suffixed surrogate. No abbreviated or cryptic column names (e.g. col1, val, num, dt, qty without context).

**Applies when:** Any .sql file containing CREATE TABLE or column definitions, or Python/ notebook code that defines DataFrame column names intended for a persistent SQL table or data model.

**How to evaluate:**

Scan CREATE TABLE statements, ALTER TABLE ADD COLUMN, and any DataFrame.columns / DataFrame.rename() assignments destined for SQL for: (1) column names not in PascalCase in SQL contexts -- flag snake_case column names (e.g. start_date, customer_id, pipeline_key) as NON_COMPLIANT; (2) generic or cryptic names: Id (standalone), Dt, Col, Val, Num, Flag, Qty, Amt without a qualifying prefix -- flag as NON_COMPLIANT; (3) date/time columns named simply Date, Time, Timestamp, or CreatedAt without a qualifying prefix describing the business event -- flag as NON_COMPLIANT (OrderDate, InvoiceCreatedAt are compliant); (4) the Key suffix appearing on non-key columns (e.g. StatusKey, NameKey) -- flag as NON_COMPLIANT; (5) plural column names (e.g. Orders, Products, Tags) -- flag as NON_COMPLIANT. Return NOT_APPLICABLE if no SQL column definitions are present.

---
