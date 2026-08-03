# Quickstart Validation Guide: Customer Churn Prediction Pipeline

**Feature**: `specs/001-churn-prediction-pipeline/`
**Date**: 2026-07-14

This guide walks through validating the full pipeline end-to-end using the project's
fixture file. Follow each step in order; expected outcomes are shown after each command
so you can verify before proceeding.

---

## Prerequisites

- Python 3.11 installed
- Project root is your working directory (`ops-code-customer_churn/`)
- Dependencies installed: `pip install -r requirements.txt`
- Directory structure initialised (created by T001 in tasks.md)

---

## Step 1: Verify the Landing File

The fixture file is already present at:

```
data/landing/CustomerChurn_20260714.csv
```

It contains **30 data rows** (plus a header). The breakdown is:

| Rows | Customer IDs | Status | Rejection reason |
|------|-------------|--------|-----------------|
| 25 | CUST-10001 – CUST-10025 | Valid | — |
| 2 | CUST-10026 (appears twice) | Invalid | Duplicate `customer_id` — both occurrences rejected |
| 1 | CUST-10027 | Invalid | `account_tenure_months` is `-3` (negative) |
| 1 | CUST-10028 | Invalid | `monthly_usage_hours` is `-4.5` (negative) |
| 1 | CUST-10029 | Invalid | `account_tenure_months` is blank (missing required field) |

Confirm the row count before proceeding:

```bash
# Expect 31 lines total (1 header + 30 data rows)
wc -l data/landing/CustomerChurn_20260714.csv
```

---

## Step 2: Run Ingestion (Bronze)

```bash
python -m src.CustomerChurn_Ingest.ingest \
  --source-file data/landing/CustomerChurn_20260714.csv
```

**Expected outcomes**:
- Exit code: `0`
- File created: `data/bronze/CustomerChurn_20260714.parquet`
- Log entries in `logs/pipeline_20260714.log`:
  - `INFO | customer_churn.ingest | Stage start: ingestion`
  - `INFO | customer_churn.ingest | 30 records written to bronze`
  - `INFO | customer_churn.ingest | Stage end: ingestion`
- Verify Bronze contents:
  ```python
  import pandas as pd
  df = pd.read_parquet("data/bronze/CustomerChurn_20260714.parquet")
  assert len(df) == 30                    # all landing rows preserved
  assert "full_name" in df.columns        # PII retained in Bronze (source of truth)
  assert "email" in df.columns
  assert "phone_number" in df.columns
  assert "source_file" in df.columns
  assert "ingested_at" in df.columns
  # Invalid rows are present — Bronze is a raw copy, no filtering here
  assert (df["customer_id"] == "CUST-10026").sum() == 2
  assert df.loc[df["customer_id"] == "CUST-10027", "account_tenure_months"].iloc[0] == -3
  ```

**Re-run idempotency check**:
```bash
python -m src.CustomerChurn_Ingest.ingest \
  --source-file data/landing/CustomerChurn_20260714.csv
```
Expected: exit `0`, warning logged, no additional rows written to Bronze.

---

## Step 3: Run Validation & De-identification (Silver)

```bash
python -m src.CustomerChurn_Validate.validate \
  --bronze-file data/bronze/CustomerChurn_20260714.parquet
```

**Expected outcomes**:
- Exit code: `0`
- Files created:
  - `data/silver/CustomerChurn_20260714.parquet`
  - `data/silver/ValidationReport_20260714.json`
- Log summary in `logs/pipeline_20260714.log`:
  - Stage start / end markers
  - `INFO | customer_churn.validate | 25 records accepted, 5 records rejected`
  - `WARNING` entries for each rejection category (duplicate, out-of-range ×2, missing field)

- Verify Silver contents:
  ```python
  import pandas as pd, json

  silver = pd.read_parquet("data/silver/CustomerChurn_20260714.parquet")
  assert len(silver) == 25                      # CUST-10001 to CUST-10025 only
  assert "full_name" not in silver.columns      # PII absent
  assert "email" not in silver.columns
  assert "phone_number" not in silver.columns
  assert silver["account_tenure_months"].min() >= 0
  assert silver["monthly_usage_hours"].min() >= 0
  assert silver["customer_id"].nunique() == 25  # no duplicates
  # Confirm the five invalid customer IDs are absent from Silver
  for bad_id in ["CUST-10026", "CUST-10027", "CUST-10028", "CUST-10029"]:
      assert bad_id not in silver["customer_id"].values, f"{bad_id} must not reach Silver"
  ```

- Verify ValidationReport:
  ```python
  report = json.load(open("data/silver/ValidationReport_20260714.json"))
  assert report["total_records"] == 30
  assert report["accepted_count"] == 25
  assert report["rejected_count"] == 5
  # Confirm rejection reasons are present for the known invalid rows
  reasons = [r["reason"] for r in report["rejections"]]
  assert any("duplicate_customer_id" in r for r in reasons)        # CUST-10026 ×2
  assert any("out_of_range:account_tenure_months<0" in r for r in reasons)  # CUST-10027
  assert any("out_of_range:monthly_usage_hours<0" in r for r in reasons)    # CUST-10028
  assert any("missing_required_field:account_tenure_months" in r for r in reasons)  # CUST-10029
  # No customer field values in rejection entries — only row index and reason
  for r in report["rejections"]:
      assert "priya" not in str(r).lower()      # CUST-10026 name must not appear
      assert "example.com" not in str(r)
      assert "555-" not in str(r)
  ```

- **PII audit** — scan the log file for any raw PII that leaked:
  ```bash
  grep -iE \
    "(jordan|priya|marcus|sofia|kwame|elin|ravi|nora|tomas|aisha|\
alex|dana|sam|@example\.com|555-01)" \
    logs/pipeline_20260714.log
  # Expected: zero matches
  ```

---

## Step 4: Run Model Training

```bash
python -m src.CustomerChurn_Train.train \
  --silver-dir data/silver \
  --random-seed 42
```

**Expected outcomes**:
- Exit code: `0`
- File created: `models/ChurnClassifier_20260714.joblib`
- MLflow run logged to `mlruns/` — query it after the session to confirm persistence:
  ```python
  import mlflow
  mlflow.set_tracking_uri("mlruns")
  runs = mlflow.search_runs()
  latest = runs.iloc[0]
  assert pd.notna(latest["metrics.accuracy"])
  assert pd.notna(latest["metrics.precision"])
  assert pd.notna(latest["metrics.recall"])
  assert pd.notna(latest["metrics.auc_roc"])
  assert int(latest["params.random_seed"]) == 42
  ```
- Log in `logs/pipeline_20260714.log`:
  - Stage start and end markers
  - Training start and end timestamps
  - Metric values at `INFO` level

**Reproducibility check** — run training a second time and confirm identical metrics:
```bash
python -m src.CustomerChurn_Train.train \
  --silver-dir data/silver \
  --random-seed 42
```
```python
import mlflow, pandas as pd
mlflow.set_tracking_uri("mlruns")
runs = mlflow.search_runs().sort_values("start_time")
assert runs.iloc[-1]["metrics.accuracy"] == runs.iloc[-2]["metrics.accuracy"]
assert runs.iloc[-1]["metrics.auc_roc"]  == runs.iloc[-2]["metrics.auc_roc"]
```

---

## Step 5: Publish Predictions (Gold)

```bash
python -m src.CustomerChurn_Predict.predict \
  --silver-file data/silver/CustomerChurn_20260714.parquet \
  --model-file models/ChurnClassifier_20260714.joblib
```

**Expected outcomes**:
- Exit code: `0`
- File created: `data/gold/CustomerChurnPrediction_20260714.parquet`
- Verify Gold contents:
  ```python
  import pandas as pd
  gold = pd.read_parquet("data/gold/CustomerChurnPrediction_20260714.parquet")
  assert len(gold) == 25                              # one row per valid Silver customer
  assert gold["customer_id"].nunique() == 25          # no duplicates
  assert gold["churn_prediction_key"].nunique() == 25 # stable surrogate keys
  assert gold["churn_prediction_key"].notna().all()
  assert gold["is_churn_predicted"].isin([0, 1]).all()
  assert gold["churn_probability"].between(0.0, 1.0).all()
  assert (gold["run_date"] == pd.Timestamp("2026-07-14").date()).all()
  # The five invalid IDs must not appear in Gold
  for bad_id in ["CUST-10026", "CUST-10027", "CUST-10028", "CUST-10029"]:
      assert bad_id not in gold["customer_id"].values
  ```
- See [data-model.md](data-model.md#layer-6-gold-predictions-shared-output) for full
  column definitions and consumer notes.

---

## Step 6: Full Pipeline Runner Validation

```bash
# Remove Silver and Gold outputs from previous steps (Bronze is the source of truth —
# do not delete it)
rm -f data/silver/CustomerChurn_20260714.parquet \
      data/silver/ValidationReport_20260714.json \
      data/gold/CustomerChurnPrediction_20260714.parquet

python -m src.pipeline \
  --source-file data/landing/CustomerChurn_20260714.csv \
  --random-seed 42
```

**Expected outcome**: all four stages run in sequence, exit code `0`. Log file shows
start/end markers for every stage. Final record counts: Bronze 30, Silver 25, Gold 25.

---

## Step 7: Error Path Validation

**Missing source file** (tests FR-010 — no silent failures):
```bash
python -m src.CustomerChurn_Ingest.ingest \
  --source-file data/landing/CustomerChurn_99991231.csv
```
Expected: exit code `1`, `ERROR` entry in `logs/pipeline_20260714.log` with a
meaningful message. No silent failure.

**All-records-rejected edge case** (tests the zero-valid-records guard):

Create a file containing only the five invalid rows from the fixture:
```
data/landing/CustomerChurnInvalid_20260714.csv
```
```
customer_id,full_name,email,phone_number,account_tenure_months,monthly_usage_hours,is_churned
CUST-10026,Priya Sundaram,priya.sundaram@example.com,555-0126,15,19.4,0
CUST-10026,Priya Sundaram,priya.sundaram@example.com,555-0126,15,19.4,0
CUST-10027,Alex Kim,alex.kim@example.com,555-0127,-3,12.0,0
CUST-10028,Dana Reyes,dana.reyes@example.com,555-0128,10,-4.5,1
CUST-10029,Sam Okoye,sam.okoye@example.com,555-0129,,18.2,1
```

Then ingest and validate:
```bash
python -m src.CustomerChurn_Ingest.ingest \
  --source-file data/landing/CustomerChurnInvalid_20260714.csv \
  --bronze-dir data/bronze

python -m src.CustomerChurn_Validate.validate \
  --bronze-file data/bronze/CustomerChurnInvalid_20260714.parquet \
  --silver-dir data/silver
```
Expected: validation exits with code `3`, `ERROR` logged, no Silver file created,
`ValidationReport` written with `accepted_count: 0` and `rejected_count: 5`.

---

## Artifact Reference

| Artifact | Location | Reference |
|----------|----------|-----------|
| Landing fixture | `data/landing/CustomerChurn_20260714.csv` | This file |
| Bronze schema | `data/bronze/` | [data-model.md § Layer 2](data-model.md#layer-2-bronze-immutable-raw-copy) |
| Silver schema | `data/silver/` | [data-model.md § Layer 3](data-model.md#layer-3-silver-validated-de-identified) |
| Gold schema | `data/gold/` | [data-model.md § Layer 6](data-model.md#layer-6-gold-predictions-shared-output) |
| Stage CLI contracts | — | [contracts/pipeline-interface.md](contracts/pipeline-interface.md) |
| Validation rules | — | [data-model.md § Validation Rules](data-model.md#validation-rules-summary) |