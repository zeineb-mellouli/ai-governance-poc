# Pipeline Interface Contract: Customer Churn Prediction Pipeline

**Feature**: `specs/001-churn-prediction-pipeline/`
**Date**: 2026-07-14

This document defines the invocation contract for each pipeline stage. Each stage is
an independently runnable Python module. Stages are designed to be composed sequentially
(Bronze → Silver → Train → Gold) but can be run individually for testing or reprocessing.

---

## Stage 1: Ingestion (Bronze)

**Module**: `src.CustomerChurn_Ingest.ingest`

```bash
python -m src.CustomerChurn_Ingest.ingest \
  --source-file data/landing/CustomerChurn_20260714.csv \
  [--bronze-dir data/bronze]
```

**Arguments**:

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--source-file` | YES | — | Path to the landing CSV file to ingest |
| `--bronze-dir` | NO | `data/bronze` | Output directory for the Bronze Parquet file |

**Outputs**:
- `data/bronze/CustomerChurn_<yyyyMMdd>.parquet` — immutable Bronze record
- Log entry in `logs/pipeline_<yyyyMMdd>.log`:
  - `INFO` stage start marker
  - `INFO` record count written
  - `INFO` stage end marker
  - `ERROR` on any failure

**Exit codes**:
- `0` — success; also the exit code for idempotent re-runs (Bronze file already exists — logs `WARNING`, no records written)
- `1` — source file not found, unreadable, or column schema mismatch

**Idempotency**: If a Bronze file for the same source date already exists, the stage
logs a `WARNING` and exits `0` without writing duplicates.

**Empty / schema-mismatch guard**: If the landing CSV has zero data rows (empty batch),
the stage logs a `WARNING` and exits `0` with zero records written. If required columns
are missing or the file has an unrecognised schema, the stage logs an `ERROR` naming the
missing/unexpected columns and exits `1`.

---

## Stage 2: Validation & De-identification (Silver)

**Module**: `src.CustomerChurn_Validate.validate`

```bash
python -m src.CustomerChurn_Validate.validate \
  --bronze-file data/bronze/CustomerChurn_20260714.parquet \
  [--silver-dir data/silver]
```

**Arguments**:

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--bronze-file` | YES | — | Path to the Bronze Parquet file to validate |
| `--silver-dir` | NO | `data/silver` | Output directory for Silver Parquet and ValidationReport |

**Outputs**:
- `data/silver/CustomerChurn_<yyyyMMdd>.parquet` — validated, de-identified records
- `data/silver/ValidationReport_<yyyyMMdd>.json` — rejection report (no PII values)
- Log entries:
  - `INFO` stage start, record counts, acceptance/rejection counts, stage end
  - `WARNING` for each validation category (missing fields, duplicates, out-of-range)
  - `ERROR` for unexpected failures

**Behaviour on zero valid records**: If all records fail validation, no Silver file is
written. A `ValidationReport` is still written. The stage exits with code `3` and logs
an `ERROR` so the pipeline does not proceed to training on an empty dataset.

**Exit codes**:
- `0` — success (at least one valid record written to Silver)
- `1` — Bronze file not found
- `3` — all records rejected; Silver not written

---

## Stage 3: Model Training

**Module**: `src.CustomerChurn_Train.train`

```bash
python -m src.CustomerChurn_Train.train \
  --silver-dir data/silver \
  [--model-dir models] \
  [--random-seed 42] \
  [--test-split 0.2]
```

**Arguments**:

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--silver-dir` | YES | — | Directory containing one or more Silver Parquet files to use as training data |
| `--model-dir` | NO | `models` | Output directory for the serialised classifier |
| `--random-seed` | NO | `42` | Random seed passed to all stochastic operations |
| `--test-split` | NO | `0.2` | Fraction of Silver data held out for evaluation |

**Outputs**:
- `models/ChurnClassifier_<yyyyMMdd>.joblib` — serialised `RandomForestClassifier`
- MLflow run logged to `mlruns/` with:
  - Parameters: `random_seed`, `test_split`, `n_estimators`, `silver_record_count`
  - Metrics: `accuracy`, `precision`, `recall`, `auc_roc`
  - Artifact: relative path to the saved model file
  - Tags: `run_date`, `silver_dir`
- Log entries:
  - `INFO` stage start, training start, evaluation results, stage end
  - `ERROR / EXCEPTION` on failures

**Reproducibility guarantee**: Given the same Silver dataset and `--random-seed`,
all metrics and the serialised model are bit-for-bit identical across runs.

**Exit codes**:
- `0` — success
- `1` — Silver directory not found or contains no Parquet files
- `4` — MLflow logging failure (model trained but metrics not persisted — logs error and exits 4 so the issue is visible)

---

## Stage 4: Prediction Publishing (Gold)

**Module**: `src.CustomerChurn_Predict.predict`

```bash
python -m src.CustomerChurn_Predict.predict \
  --silver-file data/silver/CustomerChurn_20260714.parquet \
  --model-file models/ChurnClassifier_20260714.joblib \
  [--gold-dir data/gold]
```

**Arguments**:

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--silver-file` | YES | — | Silver Parquet file to generate predictions for |
| `--model-file` | YES | — | Path to the trained classifier joblib file |
| `--gold-dir` | NO | `data/gold` | Output directory for the Gold Parquet file |

**Outputs**:
- `data/gold/CustomerChurnPrediction_<yyyyMMdd>.parquet` — one row per customer
- Log entries:
  - `INFO` stage start, prediction count, stage end
  - `ERROR` on failures

**Gold grain**: One row per `customer_id` per `run_date`. Previous days' Gold files
are never overwritten; history accumulates across runs.

**Exit codes**:
- `0` — success; also the exit code for idempotent re-runs (Gold file already exists — logs `WARNING`, no records written)
- `1` — Silver file or model file not found

---

## Full Pipeline Runner

A convenience script that chains all four stages in order:

```bash
python -m src.pipeline \
  --source-file data/landing/CustomerChurn_20260714.csv \
  [--bronze-dir data/bronze] \
  [--silver-dir data/silver] \
  [--model-dir models] \
  [--gold-dir data/gold] \
  [--random-seed 42]
```

The runner invokes each stage in sequence and aborts on any non-zero exit code,
logging the failed stage before exiting.

---

## Shared Logging Contract

All four stages share the same logging configuration:

- Logger name: `customer_churn.<stage_name>` (e.g., `customer_churn.ingest`)
- File handler: `logs/pipeline_<yyyyMMdd>.log` (appended to during a pipeline run)
- Stream handler: stdout at `INFO` level
- Format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`
- PII constraint: log messages MUST contain only counts, identifiers (batch_id,
  run_id), file paths, and metric values — never raw field values from customer records

---

## Environment Variables

No credentials are required for a local filesystem pipeline. The following optional
environment variables can override defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `MLFLOW_TRACKING_URI` | `mlruns` | MLflow tracking store path or URI |
| `CHURN_LOG_DIR` | `logs` | Directory for pipeline log files |
| `CHURN_RANDOM_SEED` | `42` | Global random seed override |

No secrets or credentials are needed. If a remote MLflow tracking server is used in
future, `MLFLOW_TRACKING_URI` points to it — the value MUST be set via environment
variable, never hardcoded.