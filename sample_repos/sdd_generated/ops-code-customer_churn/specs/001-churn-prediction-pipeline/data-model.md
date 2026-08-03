# Data Model: Customer Churn Prediction Pipeline

**Feature**: `specs/001-churn-prediction-pipeline/`
**Date**: 2026-07-14

All schemas use snake_case column names as required by NAM-5 (data file column
headers in CSV/Parquet MUST be snake_case and singular). The Gold layer is a Parquet
file consumed by BI tools; SQL-10/SQL-11 are NOT_APPLICABLE (no SQL DDL).

---

## Layer 1: Landing File (read-only source)

**Location**: `data/landing/CustomerChurn_<yyyyMMdd>.csv`
**Format**: CSV, header row present
**Grain**: One row per customer record in a daily batch
**Lifecycle**: Read-only drop zone; pipeline never writes to this directory

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `customer_id` | string | NO | Natural key for the customer within this batch |
| `full_name` | string | YES | PII — dropped immediately on ingest to Bronze read |
| `email` | string | YES | PII — dropped immediately on ingest to Bronze read |
| `phone_number` | string | YES | PII — dropped immediately on ingest to Bronze read |
| `account_tenure_months` | float | YES | Months since account opened; must be ≥ 0 |
| `monthly_usage_hours` | float | YES | Average monthly product usage; must be ≥ 0 |
| `is_churned` | int (0/1) | NO | Binary label: 1 = churned, 0 = retained |

---

## Layer 2: Bronze (immutable raw copy)

**Location**: `data/bronze/CustomerChurn_<yyyyMMdd>.parquet`
**Format**: Parquet (snappy compression)
**Grain**: One row per customer record, identical to the landing file row
**Lifecycle**: Append-only. Written once by the ingestion stage; never modified or
deleted by any downstream process. If ingestion is re-run for the same source file,
idempotency logic prevents duplicate rows.

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `customer_id` | string | NO | |
| `full_name` | string | YES | Retained in Bronze as the immutable source of truth |
| `email` | string | YES | Retained in Bronze |
| `phone_number` | string | YES | Retained in Bronze |
| `account_tenure_months` | float64 | YES | |
| `monthly_usage_hours` | float64 | YES | |
| `is_churned` | int64 | NO | |
| `ingested_at` | datetime64[UTC] | NO | Timestamp when this record was written to Bronze |
| `source_file` | string | NO | Filename of the originating landing CSV |

**PII note**: Bronze retains PII columns because it is the immutable source of
truth. Access to `data/bronze/` MUST be restricted to the ingestion process and
authorised data engineers. No downstream stage reads PII columns from Bronze —
the validation stage drops them immediately upon reading.

---

## Layer 3: Silver (validated, de-identified)

**Location**: `data/silver/CustomerChurn_<yyyyMMdd>.parquet`
**Format**: Parquet (snappy compression)
**Grain**: One row per valid, unique customer identifier in the batch
**Lifecycle**: Written by the validation stage after the quality gate passes.
Not modified after write.

**Quality gate (pandera schema — must pass before write)**:
- `customer_id`: not null, unique within batch
- `account_tenure_months`: not null, ≥ 0.0
- `monthly_usage_hours`: not null, ≥ 0.0
- `is_churned`: not null, in {0, 1}

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `customer_id` | string | NO | Unique within this Silver file |
| `account_tenure_months` | float64 | NO | ≥ 0.0 (validated) |
| `monthly_usage_hours` | float64 | NO | ≥ 0.0 (validated) |
| `is_churned` | int64 | NO | 0 or 1 (validated) |
| `validated_at` | datetime64[UTC] | NO | Timestamp of Silver write |
| `batch_id` | string | NO | Unique identifier for the processing batch (UUID) |

**PII guarantee**: `full_name`, `email`, and `phone_number` columns are absent from
this schema by design. They are dropped from the Bronze DataFrame before any
validation, logging, or write call in the validation stage.

---

## Layer 4: Validation Report

**Location**: `data/silver/ValidationReport_<yyyyMMdd>.json`
**Format**: JSON
**Grain**: One document per validation batch run
**Lifecycle**: Written alongside the Silver file. Never modified.

```json
{
  "batch_id": "uuid-string",
  "source_file": "CustomerChurn_20260714.parquet",
  "validated_at": "2026-07-14T10:00:00Z",
  "total_records": 5000,
  "accepted_count": 4923,
  "rejected_count": 77,
  "rejections": [
    { "row_index": 12, "reason": "missing_required_field:account_tenure_months" },
    { "row_index": 45, "reason": "duplicate_customer_id" },
    { "row_index": 99, "reason": "out_of_range:monthly_usage_hours<0" }
  ]
}
```

**PII guarantee**: `rejections` entries contain only `row_index` (integer position)
and `reason` (categorical string). No customer field values are included.

---

## Layer 5: Trained Model Artifact

**Location**: `models/ChurnClassifier_<yyyyMMdd>.joblib`
**Format**: joblib-serialised `RandomForestClassifier`
**Grain**: One file per training run date
**Lifecycle**: Written by the training stage. Never overwritten — each run date
produces a new file. Old files are retained for rollback.

**Associated MLflow run** (stored in `mlruns/`):

| Field | Type | Notes |
|-------|------|-------|
| `run_id` | string (UUID) | MLflow auto-generated |
| `run_date` | date | Date training was executed |
| `random_seed` | int | Always 42 |
| `train_record_count` | int | Number of Silver records used for training |
| `test_record_count` | int | Number of Silver records used for evaluation |
| `accuracy` | float | 0.0–1.0 |
| `precision` | float | 0.0–1.0 |
| `recall` | float | 0.0–1.0 |
| `auc_roc` | float | 0.0–1.0 |
| `model_path` | string | Relative path to joblib artifact |

---

## Layer 6: Gold Predictions (shared output)

**Location**: `data/gold/CustomerChurnPrediction_<yyyyMMdd>.parquet`
**Format**: Parquet (snappy compression)

**Grain**: One churn prediction per `customer_id` per `run_date`.
Each row represents the model's churn prediction for one customer as of one
pipeline execution date. A customer may appear in multiple Gold files across
different run dates, but appears exactly once per file.

**Primary key**: `churn_prediction_key` (UUID surrogate, stable within a run)
**Natural key**: `customer_id` (unique within a Gold file)

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `churn_prediction_key` | string (UUID) | NO | Surrogate key assigned once when the Gold file is written; unique per row across all Gold files |
| `customer_id` | string | NO | Joins back to Silver; never null |
| `is_churn_predicted` | int64 (0/1) | NO | Binary prediction: 1 = predicted to churn |
| `churn_probability` | float64 | NO | Model confidence score (0.0–1.0) |
| `run_date` | date | NO | Date this prediction was generated |
| `model_version` | string | NO | Filename of the model artifact used (e.g., `ChurnClassifier_20260714.joblib`) |

**Key stability note**: `churn_prediction_key` is stable for the lifetime of the
Gold file in which it was written. It is assigned once at write time using a random
UUID and is not deterministically reproducible from input data — if the Gold file
for a given `run_date` is deleted and the prediction stage is re-run, new UUIDs will
be generated. Stability is guaranteed by the idempotency guard: if a Gold file already
exists for the target `run_date`, the stage exits without overwriting it.

**Consumer notes for customer success team**:
- Filter `is_churn_predicted = 1` to get at-risk customers.
- Use `churn_probability` to prioritise outreach (higher = more urgent).
- Join on `customer_id` to your CRM system.
- Each Gold file is a full snapshot for that `run_date`; use the latest file for
  current predictions or union files for trend analysis.

---

## Entity Relationships

```
LandingFile (CSV)
    │ ingested by CustomerChurn_Ingest
    ▼
BronzeRecord (Parquet)   ──── PII present: full_name, email, phone_number
    │ validated + de-identified by CustomerChurn_Validate
    ▼
SilverRecord (Parquet)   ──── No PII; quality-gated
ValidationReport (JSON)  ──── Rejection log; no PII values
    │ feature-engineered + trained by CustomerChurn_Train
    ▼
TrainedModel (.joblib)
ExperimentLog (mlruns/)
    │ predictions published by CustomerChurn_Predict
    ▼
ChurnPrediction / Gold (Parquet)  ──── One row per customer per run_date
```

---

## Validation Rules Summary

| Rule | Layer | Field | Constraint |
|------|-------|-------|------------|
| Not null | Silver | `customer_id` | Required |
| Unique | Silver | `customer_id` | Per batch |
| Not null | Silver | `account_tenure_months` | Required |
| Range | Silver | `account_tenure_months` | ≥ 0.0 |
| Not null | Silver | `monthly_usage_hours` | Required |
| Range | Silver | `monthly_usage_hours` | ≥ 0.0 |
| Not null | Silver | `is_churned` | Required |
| Categorical | Silver | `is_churned` | In {0, 1} |
| Not null | Gold | `churn_prediction_key` | Required |
| Unique | Gold | `churn_prediction_key` | Per Gold file |
| Unique | Gold | `customer_id` | Per Gold file |
| Not null | Gold | `customer_id` | Required |
