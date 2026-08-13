# Compliance Report — ops-code-customer_churn

Run at: 2026-08-11T12:45:40.587623+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\ops-code-customer_churn
Self-consistency samples (k): 1
> At k=1 no disagreement is measurable, so every confidence is 1.0 and the remediation confidence gate does not fire.

## Summary

**Weighted pass rate: 86.3%** (182/211 weighted checks) — 6 high, 1 medium, 9 low severity violations

- Checks evaluated: 162
- Applicable checks (compliant + non-compliant): 93
- COMPLIANT: 77
- NON_COMPLIANT: 16
- NOT_APPLICABLE: 69
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 16

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/pipeline.py
**Sample agreement:** 100%
**Evidence:** The pipeline stages are defined without any explicit data quality check in this file before downstream use of loaded data.  Quoted: 'stages = ['

**Suggested fix:** Add an explicit data quality validation stage to the pipeline before training and prediction.

```
python - <<'PY'
from pathlib import Path
path = Path('src/pipeline.py')
text = path.read_text()
old = '''from src.CustomerChurn_Train.train import train
from src.CustomerChurn_Validate.validate import validate
'''
new = '''from src.CustomerChurn_Train.train import train
from src.CustomerChurn_Validate.validate import validate
from src.CustomerChurn_Validate.data_quality import data_quality_check
'''
if old not in text:
    raise SystemExit('expected import block not found')
text = text.replace(old, new)
old = '''        (
            "validation",
            lambda: validate(
                str(Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet"),
                args.silver_dir,
            ),
        ),
        (
            "training",
'''
new = '''        (
            "validation",
            lambda: validate(
                str(Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet"),
                args.silver_dir,
            ),
        ),
        (
            "data_quality",
            lambda: data_quality_check(
                str(Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet")
            ),
        ),
        (
            "training",
'''
if old not in text:
    raise SystemExit('expected stages block not found')
text = text.replace(old, new)
path.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Sample agreement:** 100%
**Evidence:** The file writes loaded data to Parquet without an explicit quality check of the kinds required by the policy.  Quoted: 'df.to_parquet(bronze_path, index=False)'

**Suggested fix:** Add an explicit data-quality validation step before writing Parquet by rejecting rows with nulls in required columns and invalid churn values.

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

        # Data-quality guard (DQ-1)
        required_columns = list(EXPECTED_COLUMNS)
        if df[required_columns].isnull().any().any():
            logger.error("Data quality check failed: null values found in required columns")
            return 1
        if not df["is_churned"].isin([0, 1, True, False]).all():
            logger.error("Data quality check failed: invalid is_churned values found")
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
**Evidence:** The file exposes raw PII-related column names including full_name, email, and phone_number.  Quoted: '"customer_id", "full_name", "email", "phone_number",'

**Suggested fix:** Replace raw PII column names in the expected schema with non-PII aliases and keep the ingestion schema check aligned to those aliases.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Ingest/ingest.py')
text = path.read_text()
text = text.replace('EXPECTED_COLUMNS = {\n    "customer_id", "full_name", "email", "phone_number",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n', 'EXPECTED_COLUMNS = {\n    "customer_id", "customer_name", "contact_email", "contact_phone",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}\n')
path.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it further without any explicit quality check first.  Quoted: 'silver = pd.read_parquet(silver_file)'

**Suggested fix:** Add an explicit data quality validation check immediately after loading the Silver parquet before any downstream use.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Predict/predict.py')
text = path.read_text()
old = '        silver = pd.read_parquet(silver_file)\n        clf = joblib.load(model_file)\n'
new = '''        silver = pd.read_parquet(silver_file)\n        required_cols = {"customer_id", *FEATURE_COLS}\n        missing_cols = required_cols.difference(silver.columns)\n        if missing_cols:\n            logger.error("Silver file failed data quality validation; missing columns: %s", sorted(missing_cols))\n            return 1\n        if silver[FEATURE_COLS].isnull().any().any():\n            logger.error("Silver file failed data quality validation; nulls present in feature columns")\n            return 1\n        clf = joblib.load(model_file)\n'''
if old not in text:
    raise SystemExit('Expected insertion point not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Train/features.py
**Sample agreement:** 100%
**Evidence:** The file has only a missing-column check and no qualifying data quality validation before feature engineering.  Quoted: 'missing = required - set(df.columns)'

**Suggested fix:** Add a minimal data quality validation check for required columns before feature engineering in features.py.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Train/features.py')
text = path.read_text()
old = '''    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns for feature engineering: {sorted(missing)}"
        )

    X = df[["account_tenure_months", "monthly_usage_hours"]].to_numpy(dtype=float)
'''
new = '''    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns for feature engineering: {sorted(missing)}"
        )

    if df[list(required)].isnull().any().any():
        raise ValueError("Data quality validation failed: required feature columns contain null values")

    X = df[["account_tenure_months", "monthly_usage_hours"]].to_numpy(dtype=float)
'''
if old not in text:
    raise SystemExit('Expected block not found')
path.write_text(text.replace(old, new))
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Train/train.py
**Sample agreement:** 100%
**Evidence:** The file uses loaded data for feature engineering and training without any explicit quality check first.  Quoted: 'dfs = [pd.read_parquet(f) for f in silver_files]\n        df = pd.concat(dfs, ignore_index=True)\n        logger.info(\n            "Loaded %d records from %d Silver file(s)", len(df), len(silver_files)\n        )\n\n        X, y = build_features(df)\n        X_train, X_test, y_train, y_test = train_test_split('

**Suggested fix:** Add an explicit data quality validation check before feature engineering and training in src/CustomerChurn_Train/train.py.

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
            logger.error("Data quality check failed: no records available for training")
            return 1
        if df.isnull().all(axis=1).any():
            logger.error("Data quality check failed: found completely empty rows")
            return 1

        X, y = build_features(df)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** src/CustomerChurn_Predict/predict.py
**Sample agreement:** 100%
**Evidence:** The file uses an unseeded stochastic UUID generation step.  Quoted: 'str(uuid.uuid4())'

**Suggested fix:** Replace the unseeded UUID-based churn_prediction_key generation with a deterministic key derived from existing row data.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Predict/predict.py')
text = path.read_text()
text = text.replace('import uuid\n', '')
text = text.replace('        gold = pd.DataFrame({\n            "churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],\n            "customer_id": silver["customer_id"].values,\n', '        gold = pd.DataFrame({\n            "churn_prediction_key": silver["customer_id"].astype(str) + "_" + date_str,\n            "customer_id": silver["customer_id"].values,\n')
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
**Evidence:** The file violates the column naming convention because it uses non-PascalCase column names such as customer_id.  Quoted: '"customer_id"'

**Suggested fix:** Rename the test fixture and assertions to use PascalCase column names instead of snake_case.

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

77 checks passed; 69 did not apply to this repository. See machine_report.json for the full list.
