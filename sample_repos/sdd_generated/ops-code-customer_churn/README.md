# ops-code-customer_churn

Customer churn prediction pipeline — Operations department, code resource.

## Overview

A four-stage batch pipeline that ingests raw customer CSV files into an immutable
Bronze store, validates and de-identifies records into a Silver store, trains a
reproducible binary churn classifier, and publishes predictions for the customer
success team.

## Medallion Architecture

| Layer | Location | Description |
|-------|----------|-------------|
| Bronze | `data/bronze/` | Immutable raw copy of each landing file. Append-only; never modified after ingestion. |
| Silver | `data/silver/` | Validated, de-identified records. PII columns dropped; quality gate enforced before every write. |
| Gold | `data/gold/` | Churn predictions — one row per customer per run date, for the customer success team. |

## Gold Table Grain

**Grain**: one churn prediction per `customer_id` per `run_date`.

Each Gold file (`data/gold/CustomerChurnPrediction_<yyyyMMdd>.parquet`) is a full
snapshot for that run date. Previous files are never overwritten; history accumulates
across runs.

`churn_prediction_key` is a UUID assigned once when the Gold file is written. It is
stable for the lifetime of that file, but is not deterministically reproducible from
input data — if a Gold file is deleted and regenerated, new UUIDs are assigned.
Stability is guaranteed by the idempotency guard.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Run individual stages

```bash
# 1. Ingest landing CSV to Bronze
python -m src.CustomerChurn_Ingest.ingest \
  --source-file data/landing/CustomerChurn_20260714.csv

# 2. Validate and de-identify Bronze to Silver
python -m src.CustomerChurn_Validate.validate \
  --bronze-file data/bronze/CustomerChurn_20260714.parquet

# 3. Train model on Silver data
python -m src.CustomerChurn_Train.train \
  --silver-dir data/silver

# 4. Publish predictions to Gold
python -m src.CustomerChurn_Predict.predict \
  --silver-file data/silver/CustomerChurn_20260714.parquet \
  --model-file models/ChurnClassifier_20260714.joblib
```

### Run full pipeline

```bash
python -m src.pipeline \
  --source-file data/landing/CustomerChurn_20260714.csv \
  --random-seed 42
```

## Running Tests

```bash
# Unit tests (no fixture file required)
pytest tests/unit/

# Integration test (requires data/landing/CustomerChurn_20260714.csv)
pytest tests/integration/
```

## Landing File Schema

Expected columns: `customer_id`, `full_name`, `email`, `phone_number`,
`account_tenure_months`, `monthly_usage_hours`, `is_churned`.

The pipeline validates that all seven columns are present before writing to Bronze.
An empty batch (header only, no data rows) is treated as a no-op (exit 0).

## Governance

See `specs/001-churn-prediction-pipeline/` for full specification, implementation
plan, data model, interface contracts, and task breakdown.
Constitution: `.specify/memory/constitution.md`.
