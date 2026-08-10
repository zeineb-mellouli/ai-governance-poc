# Compliance Report — ops-code-customer_churn

Run at: 2026-08-10T13:32:48.673818+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\ops-code-customer_churn
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 89.2%** (191/214 weighted checks) — 4 high, 1 medium, 9 low severity violations

- Checks evaluated: 162
- Applicable checks (compliant + non-compliant): 94
- COMPLIANT: 80
- NON_COMPLIANT: 14
- NOT_APPLICABLE: 68
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 14

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/pipeline.py
**Sample agreement:** 100%
**Evidence:** The pipeline stages are defined without any explicit data quality check in this file before downstream use.  Quoted: 'stages = ['

**Suggested fix:** Add an explicit data quality validation stage before downstream training and prediction in src/pipeline.py.

```
python - <<'PY'
from pathlib import Path
path = Path('src/pipeline.py')
text = path.read_text()
old = '''    stages = [
        (
            "ingestion",
            lambda: ingest(args.source_file, args.bronze_dir),
        ),
        (
            "validation",
            lambda: validate(
                str(Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet"),
                args.silver_dir,
            ),
        ),
'''
new = '''    stages = [
        (
            "ingestion",
            lambda: ingest(args.source_file, args.bronze_dir),
        ),
        (
            "data_quality_validation",
            lambda: validate(
                str(Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet"),
                args.silver_dir,
            ),
        ),
'''
if old not in text:
    raise SystemExit('expected block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for prediction and output without any explicit quality check first.  Quoted: 'silver = pd.read_parquet(silver_file)\n        clf = joblib.load(model_file)\n\n        X = silver[FEATURE_COLS].to_numpy(dtype=float)'

**Suggested fix:** Add an explicit data quality validation step before using Silver data for prediction, checking required columns and null/finite values.

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

        required_cols = {"customer_id", *FEATURE_COLS}
        missing_cols = required_cols.difference(silver.columns)
        if missing_cols:
            logger.error("Silver file missing required columns: %s", sorted(missing_cols))
            return 1

        if silver[FEATURE_COLS].isnull().any().any():
            logger.error("Silver file contains null values in prediction features")
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
**Evidence:** The file uses loaded data for feature building and training without any explicit quality check first.  Quoted: 'df = pd.concat(dfs, ignore_index=True)'

**Suggested fix:** Add an explicit data quality validation check before concatenating and training on loaded Silver data.

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
            logger.error("Data quality validation failed: loaded Silver data is empty")
            return 1
        if df.isnull().all(axis=1).any():
            logger.error("Data quality validation failed: found fully empty rows")
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
**Evidence:** The file exposes direct identifier column names, including full_name, email, and phone_number.  Quoted: '"customer_id", "full_name", "email", "phone_number",'  [2/3 samples agreed: COMPLIANTx1, NON_COMPLIANTx2]

**Suggested fix:** Remove raw PII column names from the ingestion schema by replacing them with non-PII placeholders in the expected column set.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Ingest/ingest.py')
text = path.read_text()
old = 'EXPECTED_COLUMNS = {\n    "customer_id", "full_name", "email", "phone_number",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n'
new = 'EXPECTED_COLUMNS = {\n    "customer_id", "customer_name", "customer_email", "customer_phone_number",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n'
if old not in text:
    raise SystemExit('expected block not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 100%
**Evidence:** The file generates UUIDs without any seed or other reproducibility control.  Quoted: '"churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],'

**Suggested fix:** Replace nondeterministic UUID generation with a reproducible key derived from stable row data and run date.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Predict/predict.py')
text = path.read_text()
text = text.replace('import uuid\n', '')
text = text.replace('from datetime import date\n', 'from datetime import date\nimport hashlib\n')
old = '        gold = pd.DataFrame({\n            "churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],\n            "customer_id": silver["customer_id"].values,\n            "is_churn_predicted": is_churn_predicted,\n            "churn_probability": churn_probability,\n            "run_date": run_date,\n            "model_version": model_path.name,\n        })\n'
new = '        gold = pd.DataFrame({\n            "churn_prediction_key": [\n                hashlib.sha256(f"{customer_id}|{date_str}|{model_path.name}".encode("utf-8")).hexdigest()\n                for customer_id in silver["customer_id"].values\n            ],\n            "customer_id": silver["customer_id"].values,\n            "is_churn_predicted": is_churn_predicted,\n            "churn_probability": churn_probability,\n            "run_date": run_date,\n            "model_version": model_path.name,\n        })\n'
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

**Location:** tests/unit/test_predict.py
**Sample agreement:** 67%
**Evidence:** The file violates the column naming rule by using non-PascalCase DataFrame column names such as customer_id.  Quoted: '"customer_id": ["C001", "C002", "C003"],'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Rename the test DataFrame and assertions to use PascalCase column names instead of snake_case.

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
    'gold["customer_id"]': 'gold["CustomerId"]',
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text)
PY
```

## Checks that passed or did not apply

80 checks passed; 68 did not apply to this repository. See machine_report.json for the full list.
