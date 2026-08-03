<!--
SYNC IMPACT REPORT
==================
Version change: [UNVERSIONED] → 1.0.0
Type of bump: MINOR — initial population of constitution from policies.yaml (12 policies added)

Principles added:
  - I.  Data Quality & Medallion Architecture (DQ-1, ARCH-12)
  - II. Security & Data Privacy (SEC-3, PII-4)
  - III. Observability & Reproducibility (OPS-2, REPRO-6)
  - IV. Naming & Structural Standards (NAM-5, REPO-9, SQL-10, SQL-11)
  - V.  Data Modeling & Shared Output Design (DM-7)
  - VI. Version Control Workflow (GIT-8)

Sections added:
  - Policy Reference Table
  - Compliance Review

Templates reviewed:
  ✅ .specify/templates/plan-template.md  — Constitution Check section present; no updates needed
  ✅ .specify/templates/spec-template.md  — Requirements section aligned; no updates needed
  ✅ .specify/templates/tasks-template.md — Task phases aligned; no updates needed

Deferred items:
  - None. All placeholders resolved.
-->

# ops-code-customer_churn Constitution

## Core Principles

### I. Data Quality & Medallion Architecture

Every pipeline that reads data MUST validate it for missing values, duplicates, out-of-range
values, and leakage before the data is written downstream or used for training/analysis.
Accepted validation approaches: Databricks Lakeflow expectation decorators
(`@dp.expect_all`, `@dp.expect_all_or_drop`, `@dp.expect_all_or_fail`), a
CONSTRAINT … EXPECT clause, Great Expectations / pandera / PyDeequ calls, or explicit
programmatic checks (`assert` / `raise` / filter) on null counts, duplicate counts, or
value ranges. Loading data and using it with no checks is NON_COMPLIANT (DQ-1, HIGH).

All data lake / Delta Lake / ADLS / Unity Catalog pipelines MUST follow the three-layer
medallion architecture:

- **Bronze** — raw ingested data, written once, never modified by transform or load code.
- **Silver** — validated, cleansed, and deduplicated data; a data-quality gate (see DQ-1)
  MUST precede every write to this layer.
- **Gold** — aggregated, business-ready data; raw un-aggregated rows MUST NOT flow
  directly from Bronze to Gold without a Silver intermediate.

Data MUST flow strictly Bronze → Silver → Gold. Skipping layers or overwriting Bronze
paths in transform/load steps is NON_COMPLIANT (ARCH-12, HIGH).

### II. Security & Data Privacy

No API keys, database connection strings, tokens, passwords, or any credential value
MUST ever appear literally in code or notebook cells, whether committed or not.
Credentials MUST be injected via environment variables (`os.environ` / `os.getenv`) or a
secrets manager. A literal credential value assigned directly in code is NON_COMPLIANT
regardless of repository visibility (SEC-3, HIGH).

Data containing direct identifiers (names, emails, SSNs, phone numbers, addresses) MUST
NOT appear in saved notebook outputs, `print()` statements, or log lines. Permitted
patterns: `.head()` on masked/synthetic samples, redacting before display, or clearing
notebook outputs before commit. Displaying raw identifier values in any saved output or
log line is NON_COMPLIANT (PII-4, HIGH).

### III. Observability & Reproducibility

Any pipeline expected to run on a schedule or unattended, and any model-training or long
batch-processing run, MUST use Python's `logging` module rather than relying exclusively
on `print()`. Required signals:

- A log or metric call marking the start and end of every run.
- Exception handling that calls `logger.error` / `logger.exception` — bare `except: pass`
  is NON_COMPLIANT.
- Training-loop metrics MUST be captured in a persistent store (MLflow, Weights & Biases,
  a logged file, or a queryable event log) rather than only printed (OPS-2, MEDIUM).

Any code involving model training, random sampling, or stochastic statistical analysis MUST:

1. Pin all package dependencies (versions MUST be specified in `requirements.txt`,
   `environment.yml`, or `pyproject.toml`; floating/unversioned dependencies are
   NON_COMPLIANT).
2. Explicitly set random seeds for every stochastic step (`np.random.seed`,
   `random.seed`, `random_state=` in sklearn, or framework equivalents).
3. Treat raw data as read-only — source files MUST NOT be directly overwritten by
   processing code (REPRO-6, MEDIUM).

### IV. Naming & Structural Standards

**Repository name** MUST match the pattern `{dept}-{resource}-{project}` where:

- `dept` ∈ `{aud, fin, gfp, ops, tax}` (3-letter lowercase)
- `resource` ∈ `{code, sql, synapse}`
- `project` uses `snake_case` (lowercase letters, digits, underscores; no hyphens or
  uppercase)

Regex: `^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$`
This repository (`ops-code-customer_churn`) is COMPLIANT (REPO-9, MEDIUM).

**File and folder naming** MUST follow:

- Dataset/file names in `CamelCase` with date suffix `yyyyMMdd`
  (e.g., `CustomerChurn_20240701.csv`). `snake_case`, all-lowercase, or `yyyy-MM-dd`
  date variants are NON_COMPLIANT.
- Folder structure follows `<Project>_<Feature>` (e.g., `CustomerChurn_FeatureEngineering`).
- All names: begin with a letter; no trailing underscore; no consecutive underscores; no
  spaces; max 126 characters; no vague labels (`final`, `copy`, `v2`, `temp`, `test123`).
- Data file column headers (CSV, Parquet) MUST use `snake_case` and be singular.
- A `README.md` MUST exist at the repository root (NAM-5, LOW).

**SQL objects** (tables, views, stored procedures) MUST use PascalCase. No Hungarian
notation prefixes (`tbl_`, `vw_`, `sp_`). Data-model tables MUST carry a `Dim` or `Fact`
suffix. Stored procedures MUST include a verb (`Load`, `Transform`, etc.). Schema names
MUST be from the approved list: `Staging`, `Production`, `MetaData`, `Logging`, `Config`,
`Reporting`, `PowerBI`, `DataMart`. A table MUST NOT share its name with any of its own
columns (SQL-10, MEDIUM).

**SQL column names** MUST be PascalCase and singular. Date/time columns MUST include a
qualifying prefix describing the business event (e.g., `ChurnPredictionDate`, not `Date`
or `Dt`). The `Key` suffix is reserved for primary and foreign keys in Dim/Fact tables.
Avoid bare `Id`; prefer qualified names like `CustomerId` or a `Key`-suffixed surrogate.
No abbreviated or cryptic names (`col1`, `val`, `qty` without context) (SQL-11, LOW).

### V. Data Modeling & Shared Output Design

When code produces a structured table or file explicitly intended for reuse by other
people or systems (shared database table, feature store, output for another team or
pipeline), it MUST:

1. Document the grain or primary key (comment, docstring, or README entry).
2. Use a stable surrogate/generated key for joins rather than a raw natural key where
   possible.
3. Never allow a foreign/join key to be NULL without an explicit "unknown" fallback.
4. Include documentation describing what one row represents.

This principle is NOT_APPLICABLE to exploratory notebooks, one-off analyses, or
intermediate files never intended for reuse outside the pipeline that creates them
(DM-7, MEDIUM).

### VI. Version Control Workflow

All work MUST follow the three-tier Git branch model:

- `master` — always stable and production-ready; protected.
- `develop` — integration branch before release; protected.
- `user-story/{id}` — feature work, where `{id}` is the numeric DevOps user-story number.

Branch names outside this set (e.g., `hotfix-thing`, `my-branch`, `feature/xyz`) are
NON_COMPLIANT. Commit messages MUST use a conventional prefix:
`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`. Each commit MUST be atomic — one logical
change per commit. Pull requests MUST link to a user story, require at least one reviewer
before merging, and MUST have all conflicts resolved (GIT-8, MEDIUM).

## Policy Reference Table

| Policy ID | Title | Severity | Principle |
|-----------|-------|----------|-----------|
| DQ-1 | Data quality validation present | HIGH | I |
| ARCH-12 | Medallion architecture (Bronze/Silver/Gold) | HIGH | I |
| SEC-3 | No hardcoded secrets or credentials | HIGH | II |
| PII-4 | No raw PII exposed in outputs | HIGH | II |
| OPS-2 | Logging and monitoring | MEDIUM | III |
| REPRO-6 | Reproducibility | MEDIUM | III |
| REPO-9 | Repository naming convention | MEDIUM | IV |
| NAM-5 | File and folder naming convention | LOW | IV |
| SQL-10 | SQL table and object naming convention | MEDIUM | IV |
| SQL-11 | SQL column naming convention | LOW | IV |
| DM-7 | Star schema / shared output table design | MEDIUM | V |
| GIT-8 | Git branching and commit standards | MEDIUM | VI |

## Compliance Review

All feature specs and plans MUST include a Constitution Check gate (see plan-template.md)
before Phase 0 research and again after Phase 1 design. The gate verifies:

- HIGH-severity policies (DQ-1, ARCH-12, SEC-3, PII-4) are addressed in the design —
  these are blocking; work MUST NOT proceed if they are unresolved.
- MEDIUM-severity policies (OPS-2, REPRO-6, REPO-9, SQL-10, DM-7, GIT-8) MUST be
  addressed before a PR is merged.
- LOW-severity policies (NAM-5, SQL-11) MUST be resolved before a feature is considered
  complete but are non-blocking for development start.

Any planned violation of a principle MUST be justified in the plan's Complexity Tracking
table with an explanation of why the simpler compliant approach was insufficient.

## Governance

This constitution is the authoritative governance document for `ops-code-customer_churn`.
It supersedes any informal practice or legacy convention. All policies trace to the
unified policy set defined in `policies/policies.yaml` (sources: Internal Git Workflow
Guide — Nilton Ferreira Nov 2025; File Naming Convention — Jordan Russell Oct 2025;
Repository Naming Convention — Nilton Ferreira Nov 2025; SQL Naming Conventions —
Jordan Russell Oct 2025; plus data quality, security, and reproducibility best practices).

**Amendment procedure**:
1. Propose change as a PR against this file on the `develop` branch.
2. At least one reviewer MUST approve before merging.
3. Version MUST be incremented following semantic versioning (MAJOR for removals/
   redefinitions, MINOR for new principles/sections, PATCH for clarifications).
4. `LAST_AMENDED_DATE` MUST be updated to the merge date.
5. Dependent templates (`plan-template.md`, `spec-template.md`, `tasks-template.md`)
   MUST be reviewed for consistency after any MAJOR or MINOR bump.

**Version**: 1.0.0 | **Ratified**: 2026-07-14 | **Last Amended**: 2026-07-14
