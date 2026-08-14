# Compliance Report — ops-code-customer_churn

Run at: 2026-08-13T12:24:22.607144+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\ops-code-customer_churn
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 88.4%** (183/207 weighted checks) — 4 high, 1 medium, 10 low severity violations

- Checks evaluated: 162
- Applicable checks (compliant + non-compliant): 92
- COMPLIANT: 77
- NON_COMPLIANT: 15
- NOT_APPLICABLE: 70
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 15

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Sample agreement:** 100%
**Evidence:** The file has only a schema/empty-file guard and lacks a qualifying data quality check before writing the loaded data.  Quoted: 'df = pd.read_csv(source_file)\n        except Exception:\n            logger.exception("Failed to read source file: %s", source_file)\n            return 1\n\n        # Schema guard (FR-015 / H3)\n        actual = set(df.columns)\n        missing = EXPECTED_COLUMNS - actual\n        unexpected = actual - EXPECTED_COLUMNS\n        if missing or unexpected:\n            logger.error(\n                "Column schema mismatch | missing=%s | unexpected=%s",\n                sorted(missing),\n                sorted(unexpected),\n            )\n            return 1\n\n        # Empty-file guard (M2)'

**Suggested fix:** Add a minimal data quality validation that rejects rows with missing required values before writing Bronze output.

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
'''
new = '''        # Data quality guard: required fields must be present on every row
        required_columns = sorted(EXPECTED_COLUMNS)
        null_rows = df[required_columns].isna().any(axis=1)
        if null_rows.any():
            logger.error(
                "Data quality check failed | rows_with_missing_required_values=%d",
                int(null_rows.sum()),
            )
            return 1

        # Empty-file guard (M2)
        if len(df) == 0:
            logger.warning(
                "Empty batch: zero records in %s, no Bronze written", src_path.name
            )
            logger.info("Stage end: ingestion | records_written=0")
            return 0
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for prediction and output without any explicit quality check first.  Quoted: 'silver = pd.read_parquet(silver_file)\n        clf = joblib.load(model_file)\n\n        X = silver[FEATURE_COLS].to_numpy(dtype=float)\n        is_churn_predicted = clf.predict(X).astype(int)\n        churn_probability = clf.predict_proba(X)[:, 1]'

**Suggested fix:** Add an explicit data quality validation check before loading the Silver data for prediction.

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
        clf = joblib.load(model_file)

        # Data quality validation: required columns must exist and be non-null.
        required_cols = ["customer_id", *FEATURE_COLS]
        missing_cols = [c for c in required_cols if c not in silver.columns]
        if missing_cols:
            logger.error("Silver file missing required columns: %s", missing_cols)
            return 1
        if silver[required_cols].isnull().any().any():
            logger.error("Silver file contains null values in required prediction columns")
            return 1

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

**Suggested fix:** Add an explicit data quality validation step before feature building and training in train.py.

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

        required_columns = ["customer_id", "churn"]
        missing_columns = [c for c in required_columns if c not in df.columns]
        if missing_columns:
            logger.error("Data quality check failed: missing required columns %s", missing_columns)
            return 1
        if df.empty:
            logger.error("Data quality check failed: no records available for training")
            return 1
        if df[required_columns].isnull().any().any():
            logger.error("Data quality check failed: null values found in required columns")
            return 1

        X, y = build_features(df)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Sample agreement:** 67%
**Evidence:** The file exposes direct identifier columns full_name, email, and phone_number.  Quoted: '"customer_id", "full_name", "email", "phone_number",'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Remove raw PII columns from the ingestion schema guard so the stage no longer accepts or exposes full_name, email, or phone_number.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Ingest/ingest.py')
text = path.read_text()
old = 'EXPECTED_COLUMNS = {\n    "customer_id", "full_name", "email", "phone_number",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n'
new = 'EXPECTED_COLUMNS = {\n    "customer_id",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n'
if old not in text:
    raise SystemExit('expected block not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 67%
**Evidence:** The file uses an unseeded stochastic UUID generation step.  Quoted: 'churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))]'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Replace the unseeded UUID-based churn_prediction_key with a deterministic key derived from existing row data.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Predict/predict.py')
text = path.read_text()
text = text.replace('import uuid\n', '')
text = text.replace('        gold = pd.DataFrame({\n            "churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],\n            "customer_id": silver["customer_id"].values,\n', '        gold = pd.DataFrame({\n            "churn_prediction_key": silver["customer_id"].astype(str).radd("churn_").values,\n            "customer_id": silver["customer_id"].values,\n')
path.write_text(text)
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

**Location:** tests/unit/test_predict.py
**Sample agreement:** 100%
**Evidence:** The file uses non-PascalCase DataFrame column names such as customer_id, which violates the column naming convention.  Quoted: '"customer_id": ["C001", "C002", "C003"],'

**Suggested fix:** Rename the test DataFrame columns in tests/unit/test_predict.py from snake_case to PascalCase to satisfy SQL-11 without changing test behavior.

```
python - <<'PY'
from pathlib import Path
path = Path('tests/unit/test_predict.py')
text = path.read_text()
replacements = {
    '"customer_id"': '"CustomerId"',
    '"account_tenure_months"': '"AccountTenureMonths"',
    '"monthly_usage_hours"': '"MonthlyUsageHours"',
    '"is_churned"': '"IsChurned"',
    '"validated_at"': '"ValidatedAt"',
    '"batch_id"': '"BatchId"',
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** tests/unit/test_features.py
**Sample agreement:** 67%
**Evidence:** The file violates the column naming convention by using lowercase underscored column names such as customer_id.  Quoted: '"customer_id": ["C001", "C002", "C003"],'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Rename the test DataFrame columns to PascalCase to satisfy SQL-11 without changing test behavior.

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
text = text.replace('pd.DataFrame({"customer_id": ["C001"], "account_tenure_months": [5.0]})', 'pd.DataFrame({"CustomerId": ["C001"], "AccountTenureMonths": [5.0]})')
path.write_text(text)
PY
```

## Checks that passed or did not apply

77 checks passed; 70 did not apply to this repository. See machine_report.json for the full list.
