# Implementation Plan: Customer Churn Prediction Pipeline

**Branch**: `user-story/001-churn-prediction-pipeline` | **Date**: 2026-07-14 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-churn-prediction-pipeline/spec.md`

## Summary

Build a four-stage batch pipeline that ingests raw customer CSV files into an immutable
Bronze store, validates and de-identifies records into a Silver store, trains a
reproducible binary churn classifier on Silver data with persistent experiment logging,
and publishes one-row-per-customer predictions to a Gold Parquet file for the customer
success team. Every stage is governed by the medallion architecture, PII removal before
Silver, pinned dependencies, a fixed random seed, and structured persistent logging.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**:
- `pandas==2.2.2` — DataFrame ingestion, validation, feature engineering, Parquet I/O
- `pandera==0.19.2` — Declarative schema validation for the Silver quality gate
- `scikit-learn==1.5.0` — Binary classifier (`RandomForestClassifier`, `random_state=42`)
- `mlflow==2.13.0` — Persistent experiment tracking (local file store, no server needed)
- `joblib==1.4.2` — Model serialization / deserialization
- `numpy==1.26.4` — Numerical operations
- `pyarrow==16.1.0` — Parquet read/write backend
- `pytest==8.2.0` — Unit and integration tests

**Storage**: Local tiered folder structure mirroring medallion layers:
- `data/landing/` — drop zone; pipeline reads only, never writes
- `data/bronze/` — raw Parquet copies; append-only, never overwritten
- `data/silver/` — validated, de-identified Parquet
- `data/gold/` — churn prediction Parquet (one file per run date)
- `models/` — serialized classifier artifacts
- `logs/` — structured log files (FileHandler)
- `mlruns/` — MLflow local tracking store

**Testing**: pytest (unit tests per module, one integration test for full pipeline)

**Target Platform**: Linux / macOS (local workstation or CI runner)

**Project Type**: Batch data pipeline + supervised ML training script

**Performance Goals**: Process up to 100 000 customer records per daily batch in under
5 minutes on commodity hardware (≥4 CPU cores, 8 GB RAM)

**Constraints**:
- `requirements.txt` with pinned versions — no floating specifiers
- `random_state=42` passed to every stochastic operation
- PII columns (`full_name`, `email`, `phone_number`) dropped from the DataFrame
  before any logging call and before the Silver write
- Bronze Parquet files opened read-only by convention; no transform step may write to
  the `data/bronze/` directory

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Policy IDs | Status | Evidence |
|-----------|-----------|--------|----------|
| I. Data Quality & Medallion Architecture | DQ-1, ARCH-12 | ✅ PASS | pandera schema gate before every Silver write; strict Bronze→Silver→Gold flow; Bronze directory is write-locked for all non-ingestion code |
| II. Security & Data Privacy | SEC-3, PII-4 | ✅ PASS | No credentials needed (local filesystem); `full_name`, `email`, `phone_number` dropped before any log call or Silver write; Silver and Gold contain no PII columns |
| III. Observability & Reproducibility | OPS-2, REPRO-6 | ✅ PASS | Python `logging` module with `FileHandler`; MLflow logs start/end markers and all metrics persistently; `random_state=42` explicit; `requirements.txt` fully pinned |
| IV. Naming & Structural Standards | NAM-5, REPO-9, SQL-10, SQL-11 | ✅ PASS | Repo name `ops-code-customer_churn` is compliant; landing file `CustomerChurn_20260714.csv` is compliant CamelCase + yyyyMMdd; Parquet column headers snake_case (NAM-5); SQL-10/SQL-11 NOT_APPLICABLE (no SQL DDL — Gold is Parquet); README.md required (Task T002) |
| V. Data Modeling & Shared Output Design | DM-7 | ✅ PASS | Gold grain documented ("one prediction per customer_id per run_date"); `churn_prediction_key` UUID surrogate on every row; `customer_id` never null; grain statement in README and inline schema comment |
| VI. Version Control Workflow | GIT-8 | ✅ PASS | Working on `user-story/001-churn-prediction-pipeline`; all commits will use conventional prefixes; PR will require one reviewer |

**Gate result: ALL CLEAR — no violations. Phase 0 may proceed.**

## Project Structure

### Documentation (this feature)

```text
specs/001-churn-prediction-pipeline/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── pipeline-interface.md   # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
src/
├── CustomerChurn_Ingest/
│   ├── __init__.py
│   └── ingest.py           # Bronze ingestion stage
├── CustomerChurn_Validate/
│   ├── __init__.py
│   └── validate.py         # Silver validation + PII removal stage
├── CustomerChurn_Train/
│   ├── __init__.py
│   ├── features.py         # Feature engineering (tenure, usage features)
│   └── train.py            # Model training + MLflow logging
└── CustomerChurn_Predict/
    ├── __init__.py
    └── predict.py          # Gold prediction publishing stage

data/
├── landing/                # Drop zone — pipeline reads; never writes
├── bronze/                 # Immutable raw Parquet copies
├── silver/                 # Validated, de-identified Parquet
└── gold/                   # Churn prediction Parquet

models/                     # Serialized classifier artifacts (joblib)
logs/                       # Structured log files
mlruns/                     # MLflow local experiment tracking store

tests/
├── unit/
│   ├── test_ingest.py
│   ├── test_validate.py
│   ├── test_features.py
│   └── test_predict.py
└── integration/
    └── test_pipeline_e2e.py

requirements.txt            # Pinned package versions
README.md                   # Required by NAM-5; includes Gold grain statement
```

**Structure Decision**: Single-project layout. Each pipeline stage is an independent
Python module under `src/` following the `<Project>_<Feature>` folder naming convention
(NAM-5). Data layers mirror the medallion architecture directly. No web frontend or
mobile layer required.

## Complexity Tracking

> No violations to justify. All constitution principles are met by design.
