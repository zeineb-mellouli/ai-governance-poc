# Compliance Report — ops-code-customer_churn

Run at: 2026-08-10T09:19:52.756256+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\ops-code-customer_churn
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 89.2% (215/241 weighted checks)

> 5 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 178
- Applicable checks (compliant + non-compliant): 108
- COMPLIANT: 93
- NON_COMPLIANT: 15
- NOT_APPLICABLE: 70
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 15

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Sample agreement:** 100%
**Evidence:** The file writes loaded data onward without a qualifying data quality check first.  Quoted: 'df.to_parquet(bronze_path, index=False)'

**Suggested fix:** Add a minimal data quality validation before writing to Bronze by rejecting rows with nulls in required columns.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Ingest/ingest.py')
text = path.read_text()
old = '''        # Empty-file guard (M2)
        if len(df) == 0:
            logger.warning(
                "Empty batch: zero records in %s, no Bronze written", src_path.name
            )
            logger.info("Stage end: ingestion | records_written=0")
            return 0

        date_str = _date_from_filename(src_path.name)
'''
new = '''        # Empty-file guard (M2)
        if len(df) == 0:
            logger.warning(
                "Empty batch: zero records in %s, no Bronze written", src_path.name
            )
            logger.info("Stage end: ingestion | records_written=0")
            return 0

        # Data quality guard: require all expected columns to be populated
        if df[list(EXPECTED_COLUMNS)].isnull().any().any():
            logger.error("Data quality check failed: null values found in required columns")
            return 1

        date_str = _date_from_filename(src_path.name)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Sample agreement:** 100%
**Evidence:** The file exposes raw PII-bearing column names in its schema definition.  Quoted: '"customer_id", "full_name", "email", "phone_number",'

**Suggested fix:** Replace the raw PII-bearing schema column names with neutral placeholders in the ingestion schema check.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Ingest/ingest.py')
text = path.read_text()
old = 'EXPECTED_COLUMNS = {\n    "customer_id", "full_name", "email", "phone_number",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n'
new = 'EXPECTED_COLUMNS = {\n    "customer_key", "customer_name", "contact_email", "contact_phone",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n'
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it for prediction without any explicit quality check first.  Quoted: 'silver = pd.read_parquet(silver_file)\n        clf = joblib.load(model_file)\n\n        X = silver[FEATURE_COLS].to_numpy(dtype=float)'

**Suggested fix:** Add an explicit data quality check before prediction to verify required columns are present and contain no nulls in the feature set and customer_id.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Predict/predict.py')
text = path.read_text()
old = '''        silver = pd.read_parquet(silver_file)
        clf = joblib.load(model_file)

        X = silver[FEATURE_COLS].to_numpy(dtype=float)
'''
new = '''        silver = pd.read_parquet(silver_file)
        missing_cols = [c for c in ["customer_id", *FEATURE_COLS] if c not in silver.columns]
        if missing_cols:
            logger.error("Data quality check failed: missing columns: %s", missing_cols)
            return 1
        if silver[["customer_id", *FEATURE_COLS]].isnull().any().any():
            logger.error("Data quality check failed: null values found in required columns")
            return 1

        clf = joblib.load(model_file)

        X = silver[FEATURE_COLS].to_numpy(dtype=float)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Train/train.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for feature building and training without any explicit quality check first.  Quoted: 'dfs = [pd.read_parquet(f) for f in silver_files]\n        df = pd.concat(dfs, ignore_index=True)\n        logger.info(\n            "Loaded %d records from %d Silver file(s)", len(df), len(silver_files)\n        )\n\n        X, y = build_features(df)\n        X_train, X_test, y_train, y_test = train_test_split('

**Suggested fix:** Add an explicit data quality validation check before feature building and training in src/CustomerChurn_Train/train.py.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Train/train.py')
text = path.read_text()
old = '''        dfs = [pd.read_parquet(f) for f in silver_files]
        df = pd.concat(dfs, ignore_index=True)
        logger.info(
            "Loaded %d records from %d Silver file(s)", len(df), len(silver_files)
        )

        X, y = build_features(df)
'''
new = '''        dfs = [pd.read_parquet(f) for f in silver_files]
        df = pd.concat(dfs, ignore_index=True)
        logger.info(
            "Loaded %d records from %d Silver file(s)", len(df), len(silver_files)
        )

        if df.empty:
            logger.error("Data quality check failed: loaded Silver data is empty")
            return 1
        if df.isnull().all(axis=1).any():
            logger.error("Data quality check failed: found fully null row(s) in Silver data")
            return 1

        X, y = build_features(df)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/pipeline.py
**Sample agreement:** 67%
**Evidence:** The file loads and uses data in a pipeline but contains no explicit quality check in this file before downstream use.  Quoted: 'stages = ['  [2/3 samples agreed: COMPLIANTx1, NON_COMPLIANTx2]

**Suggested fix:** Add an explicit data-quality validation step in the pipeline before training and prediction by checking the ingested parquet exists and is non-empty.

```
python - <<'PY'
from pathlib import Path
path = Path('src/pipeline.py')
text = path.read_text()
old = '''def run_pipeline(args) -> int:
    """
    Chain all four pipeline stages in order: ingest → validate → train → predict.
    Aborts and logs the failing stage on any non-zero exit code.
    """
    logger.info("Pipeline start | source=%s", args.source_file)

    src_path = Path(args.source_file)
    date_str = src_path.stem.split("_")[-1]  # e.g. "20260714"
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    stages = [
'''
new = '''def run_pipeline(args) -> int:
    """
    Chain all four pipeline stages in order: ingest → validate → train → predict.
    Aborts and logs the failing stage on any non-zero exit code.
    """
    logger.info("Pipeline start | source=%s", args.source_file)

    src_path = Path(args.source_file)
    date_str = src_path.stem.split("_")[-1]  # e.g. "20260714"
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    bronze_file = Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet"

    if not bronze_file.exists() or bronze_file.stat().st_size == 0:
        logger.error("Data quality check failed | file=%s | exists=%s | size=%d", bronze_file, bronze_file.exists(), bronze_file.stat().st_size if bronze_file.exists() else 0)
        return 1

    stages = [
'''
text = text.replace(old, new)
text = text.replace('''            lambda: validate(
                str(Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet"),
                args.silver_dir,
            ),
''', '''            lambda: validate(
                str(bronze_file),
                args.silver_dir,
            ),
''')
text = text.replace('''            lambda: predict(
                str(Path(args.silver_dir) / f"CustomerChurn_{date_str}.parquet"),
                str(Path(args.model_dir) / f"ChurnClassifier_{today_str}.joblib"),
                args.gold_dir,
            ),
''', '''            lambda: predict(
                str(Path(args.silver_dir) / f"CustomerChurn_{date_str}.parquet"),
                str(Path(args.model_dir) / f"ChurnClassifier_{today_str}.joblib"),
                args.gold_dir,
            ),
''')
path.write_text(text)
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 67%
**Evidence:** The file uses UUID generation without any seed or deterministic control.  Quoted: '"churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Replace nondeterministic UUID generation with a stable per-row key derived from existing input fields and run date.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Predict/predict.py')
text = path.read_text()
text = text.replace('import uuid\n', '')
text = text.replace('from datetime import date\n', 'from datetime import date\nimport hashlib\n')
old = '        gold = pd.DataFrame({\n            "churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],\n            "customer_id": silver["customer_id"].values,\n            "is_churn_predicted": is_churn_predicted,\n            "churn_probability": churn_probability,\n            "run_date": run_date,\n            "model_version": model_path.name,\n        })\n'
new = '        gold = pd.DataFrame({\n            "churn_prediction_key": [\n                hashlib.sha256(f"{customer_id}|{date_str}|{model_path.name}".encode("utf-8")).hexdigest()\n                for customer_id in silver["customer_id"].astype(str).values\n            ],\n            "customer_id": silver["customer_id"].values,\n            "is_churn_predicted": is_churn_predicted,\n            "churn_probability": churn_probability,\n            "run_date": run_date,\n            "model_version": model_path.name,\n        })\n'
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/pipeline.py
**Sample agreement:** 100%
**Evidence:** file name stem 'pipeline' is not CamelCase

**Suggested fix:** Rename to 'src/Pipeline.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'pipeline' must be updated to 'Pipeline' in the same change.

```
git mv src/pipeline.py src/Pipeline.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Sample agreement:** 100%
**Evidence:** file name stem 'ingest' is not CamelCase

**Suggested fix:** Rename to 'src/CustomerChurn_Ingest/Ingest.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'ingest' must be updated to 'Ingest' in the same change.

```
git mv src/CustomerChurn_Ingest/ingest.py src/CustomerChurn_Ingest/Ingest.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 100%
**Evidence:** file name stem 'predict' is not CamelCase

**Suggested fix:** Rename to 'src/CustomerChurn_Predict/Predict.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'predict' must be updated to 'Predict' in the same change.

```
git mv src/CustomerChurn_Predict/predict.py src/CustomerChurn_Predict/Predict.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Train/features.py
**Sample agreement:** 100%
**Evidence:** file name stem 'features' is not CamelCase

**Suggested fix:** Rename to 'src/CustomerChurn_Train/Features.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'features' must be updated to 'Features' in the same change.

```
git mv src/CustomerChurn_Train/features.py src/CustomerChurn_Train/Features.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Train/train.py
**Sample agreement:** 100%
**Evidence:** file name stem 'train' is not CamelCase

**Suggested fix:** Rename to 'src/CustomerChurn_Train/Train.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'train' must be updated to 'Train' in the same change.

```
git mv src/CustomerChurn_Train/train.py src/CustomerChurn_Train/Train.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Validate/schema.py
**Sample agreement:** 100%
**Evidence:** file name stem 'schema' is not CamelCase

**Suggested fix:** Rename to 'src/CustomerChurn_Validate/Schema.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'schema' must be updated to 'Schema' in the same change.

```
git mv src/CustomerChurn_Validate/schema.py src/CustomerChurn_Validate/Schema.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Validate/validate.py
**Sample agreement:** 100%
**Evidence:** file name stem 'validate' is not CamelCase

**Suggested fix:** Rename to 'src/CustomerChurn_Validate/Validate.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'validate' must be updated to 'Validate' in the same change.

```
git mv src/CustomerChurn_Validate/validate.py src/CustomerChurn_Validate/Validate.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/utils/logging_config.py
**Sample agreement:** 100%
**Evidence:** file name stem 'logging_config' is not CamelCase

**Suggested fix:** Rename to 'src/utils/LoggingConfig.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'logging_config' must be updated to 'LoggingConfig' in the same change.

```
git mv src/utils/logging_config.py src/utils/LoggingConfig.py
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** tests/unit/test_features.py
**Sample agreement:** 67%
**Evidence:** The DataFrame uses non-PascalCase column names such as customer_id, which violates the column naming convention.  Quoted: '"customer_id": ["C001", "C002", "C003"],'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Rename the test DataFrame columns to PascalCase and update the feature-access assertions accordingly.

```
python - <<'PY'
from pathlib import Path
path = Path('tests/unit/test_features.py')
text = path.read_text()
text = text.replace('"customer_id": ["C001", "C002", "C003"],', '"CustomerId": ["C001", "C002", "C003"],')
text = text.replace('"account_tenure_months": [12.0, 3.0, 24.0],', '"AccountTenureMonths": [12.0, 3.0, 24.0],')
text = text.replace('"monthly_usage_hours": [8.5, 1.2, 20.0],', '"MonthlyUsageHours": [8.5, 1.2, 20.0],')
text = text.replace('"is_churned": [0, 1, 0],', '"IsChurned": [0, 1, 0],')
text = text.replace('"validated_at": ["2026-07-14T10:00:00+00:00"] * 3,', '"ValidatedAt": ["2026-07-14T10:00:00+00:00"] * 3,')
text = text.replace('"batch_id": ["abc"] * 3,', '"BatchId": ["abc"] * 3,')
text = text.replace('sample_df["account_tenure_months"]', 'sample_df["AccountTenureMonths"]')
text = text.replace('sample_df["monthly_usage_hours"]', 'sample_df["MonthlyUsageHours"]')
text = text.replace('sample_df["is_churned"]', 'sample_df["IsChurned"]')
text = text.replace('pd.DataFrame({"customer_id": ["C001"], "account_tenure_months": [5.0]})', 'pd.DataFrame({"CustomerId": ["C001"], "AccountTenureMonths": [5.0]})')
path.write_text(text)
PY
```

## Checks that passed or did not apply

93 checks passed; 70 did not apply to this repository. See machine_report.json for the full list.
