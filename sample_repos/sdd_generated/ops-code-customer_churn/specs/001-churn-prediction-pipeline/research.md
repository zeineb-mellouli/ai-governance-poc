# Research: Customer Churn Prediction Pipeline

**Feature**: `specs/001-churn-prediction-pipeline/`
**Date**: 2026-07-14

All technical unknowns from the spec's Assumptions section are resolved here. Each
decision is recorded with rationale and alternatives considered.

---

## Decision 1: Validation Library for Silver Quality Gate

**Decision**: `pandera==0.19.2`

**Rationale**: pandera defines schemas as Python objects, integrating naturally with
pandas DataFrames. It produces structured error reports (which rows failed and why)
without exposing cell values — critical for PII safety. Schemas are version-controlled
alongside code. Validation errors raise typed exceptions that the logging layer can
catch and record without printing raw data.

**Alternatives considered**:
- *Great Expectations*: powerful but heavy; requires a "Data Context" directory and
  more configuration overhead for a single-table pipeline. Overkill for this scope.
- *Manual assert/raise*: compliant per DQ-1, but less declarative and harder to
  extend. Pandera's declarative schemas are more maintainable.
- *PyDeequ*: requires Apache Spark; incompatible with local pandas-based pipeline.

---

## Decision 2: Experiment Tracking for Persistent Metrics

**Decision**: `mlflow==2.13.0` with local file-based tracking store (`mlruns/` in
project root)

**Rationale**: MLflow's local file store writes experiment metadata to disk
immediately — it persists after the Python session ends, satisfying OPS-2 and FR-009.
No server is required; runs are queryable via `mlflow ui` or programmatically via the
MLflow Python API. The tracking URI is set via `mlflow.set_tracking_uri("mlruns")`
— no hardcoded path. MLflow is widely adopted in ML teams and integrates with most BI
and governance tooling.

**Alternatives considered**:
- *Weights & Biases*: cloud-hosted by default; requires an API key (SEC-3 risk) and
  internet access. Not suitable for an on-premise or air-gapped deployment.
- *File-based Python logging only*: satisfies OPS-2 minimally but does not provide
  queryable metric history across runs. MLflow adds structured search at low cost.
- *TensorBoard*: designed for deep-learning training loops; not idiomatic for
  sklearn batch pipelines.

---

## Decision 3: ML Algorithm

**Decision**: `sklearn.ensemble.RandomForestClassifier` with `random_state=42`

**Rationale**: RandomForest is robust to class imbalance (common in churn datasets
where churners are a minority), requires no feature scaling, and produces calibrated
probability estimates via `predict_proba`. The `random_state` parameter fully pins
stochastic behaviour, satisfying REPRO-6. Feature importance scores provide a natural
audit trail for model explainability. Training a forest on up to 100k records with
default hyperparameters completes in seconds on a laptop.

**Alternatives considered**:
- *LogisticRegression*: interpretable but requires feature scaling and struggles with
  non-linear interactions. Less accurate on raw tenure/usage features without careful
  engineering.
- *XGBoost / LightGBM*: more accurate but adds a non-standard dependency (not in
  the standard sklearn ecosystem) and complicates the `random_state` pinning story
  (multiple seeds required). Can be introduced in a v2 iteration.
- *Deep learning*: completely disproportionate for a two-feature tabular dataset.

---

## Decision 4: Storage Format for Bronze / Silver / Gold

**Decision**: Parquet (via `pyarrow==16.1.0`)

**Rationale**: Parquet is columnar, compressed, and type-preserving — a float column
written as float64 is read back as float64 with no silent type coercion. It is
natively queryable by pandas, DuckDB, Spark, and most BI tools (Power BI, Tableau,
Databricks), making it the right format for a Gold layer consumed by the customer
success team. Append-only Bronze Parquet files can be named with the source file date
(`CustomerChurn_<yyyyMMdd>.parquet`) satisfying NAM-5.

**Alternatives considered**:
- *CSV*: no schema enforcement, slow for large datasets, silent type coercion on read.
  Acceptable for the landing zone (input format) but wrong for processed layers.
- *SQLite / DuckDB file*: would require SQL DDL and trigger SQL-10/SQL-11 compliance
  work. The customer success team's BI tools work directly with Parquet via connectors,
  so a database file adds friction without benefit.
- *JSON Lines*: verbose, no columnar efficiency, poor BI tool support.

---

## Decision 5: PII Removal Strategy

**Decision**: Drop columns (`full_name`, `email`, `phone_number`) from the DataFrame
immediately after reading from Bronze, before any other processing or logging.

**Rationale**: Dropping is simpler, safer, and irreversible compared to hashing or
pseudonymisation. `customer_id` is the only identifier needed downstream. Because
columns are dropped before any validation, logging, or feature engineering call,
there is no code path through which raw PII could leak into a log line or Silver
file, even due to a programming error in a later stage.

**Alternatives considered**:
- *SHA-256 hashing of PII columns*: would allow re-identification if the original
  values are known (rainbow table attack on low-entropy names/emails). Dropping is
  strictly safer.
- *Masking with a fixed token (e.g., `***`)*: adds a column with no downstream
  value and wastes storage. Dropped columns occupy zero space.
- *Keeping in Bronze only, never accessing*: Bronze columns are still loaded into
  memory on every Silver read if not explicitly dropped. Explicit drop is safer.

---

## Decision 6: Logging Architecture

**Decision**: Python standard `logging` module with two handlers:
1. `FileHandler` writing to `logs/pipeline_<yyyyMMdd>.log` (persistent)
2. `StreamHandler` to stdout (developer convenience, not the persistence mechanism)

Log level: `INFO` for stage markers and metrics, `ERROR` / `EXCEPTION` for failures.
PII-safe logging: only log `customer_id` counts (integers), never field values.

**Rationale**: The standard library `logging` module is always available (no extra
dependency), and `FileHandler` guarantees persistence after session termination,
satisfying OPS-2. The dual-handler setup lets CI capture stdout while ensuring
on-disk persistence for audit. MLflow handles metric-level persistence; the log file
handles stage markers and errors.

**Alternatives considered**:
- *structlog*: structured JSON logging is useful in distributed systems but adds a
  dependency; the standard library is sufficient for a single-process batch pipeline.
- *loguru*: popular but non-standard; same trade-off as structlog.

---

## Decision 7: Dependency Manifest Format

**Decision**: `requirements.txt` with exact version pins (`==`)

**Rationale**: `requirements.txt` is the simplest, most universally supported format.
Every package version is pinned with `==` (not `>=`, `~=`, or `^`) to satisfy REPRO-6.
The file is generated from a fresh virtual environment with `pip freeze` to capture
transitive dependencies. A `pyproject.toml` wrapper can be added in v2 if the project
evolves into a distributable package.

**Alternatives considered**:
- *conda `environment.yml`*: valid alternative but requires conda/mamba; pip-only
  environments are simpler for CI integration.
- *Poetry `pyproject.toml`*: excellent for library distribution, but the lockfile
  (`poetry.lock`) is the actual pin source; for a pipeline script `requirements.txt`
  is sufficient and more portable.
