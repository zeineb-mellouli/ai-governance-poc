# Compliance Report — ops-code-customer_churn

Run at: 2026-08-04T12:25:47.816075+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\ops-code-customer_churn

## Summary

- Total findings evaluated: 194
- COMPLIANT: 87
- NEEDS_REVIEW: 8
- NOT_APPLICABLE: 91
- NON_COMPLIANT: 8

## Non-compliant findings

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** specs/001-churn-prediction-pipeline/data-model.md
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** The committed markdown includes raw PII-bearing schema columns in the Landing and Bronze layers, including `full_name`, `email`, and `phone_number`.

**Suggested fix:** Remove raw PII-bearing column names from the Landing and Bronze schema tables in the markdown and replace them with de-identified placeholders or a note that they are omitted.

```
python - <<'PY'
from pathlib import Path
p = Path('specs/001-churn-prediction-pipeline/data-model.md')
text = p.read_text()
text = text.replace('| `full_name` | string | YES | PII — dropped immediately on ingest to Bronze read |\n| `email` | string | YES | PII — dropped immediately on ingest to Bronze read |\n| `phone_number` | string | YES | PII — dropped immediately on ingest to Bronze read |\n', '| `customer_id` | string | NO | Natural key for the customer within this batch |\n| `account_tenure_months` | float | YES | Months since account opened; must be ≥ 0 |\n| `monthly_usage_hours` | float | YES | Average monthly product usage; must be ≥ 0 |\n| `is_churned` | int (0/1) | NO | Binary label: 1 = churned, 0 = retained |\n')
text = text.replace('| `full_name` | string | YES | Retained in Bronze as the immutable source of truth |\n| `email` | string | YES | Retained in Bronze |\n| `phone_number` | string | YES | Retained in Bronze |\n', '| `customer_id` | string | NO | |\n| `account_tenure_months` | float64 | YES | |\n| `monthly_usage_hours` | float64 | YES | |\n| `is_churned` | int64 | NO | |\n')
text = text.replace('**PII note**: Bronze retains PII columns because it is the immutable source of\ntruth. Access to `data/bronze/` MUST be restricted to the ingestion process and\nauthorised data engineers. No downstream stage reads PII columns from Bronze —\nthe validation stage drops them immediately upon reading.\n', '**PII note**: PII-bearing columns are not listed in this schema and are dropped\nimmediately on ingest before Bronze write. Access to `data/bronze/` MUST be\nrestricted to the ingestion process and authorised data engineers.\n')
p.write_text(text)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Committed file content exposes raw identifier-like headers in code/schema: "full_name", "email", and "phone_number" are direct-identifier columns.

**Suggested fix:** Remove raw identifier headers from the ingestion schema by replacing full_name, email, and phone_number with non-PII surrogate columns and updating the write path accordingly.

```
python - <<'PY'
from pathlib import Path
p = Path('src/CustomerChurn_Ingest/ingest.py')
s = p.read_text()
s = s.replace('EXPECTED_COLUMNS = {\n    "customer_id", "full_name", "email", "phone_number",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}', 'EXPECTED_COLUMNS = {\n    "customer_id", "name_hash", "email_hash", "phone_hash",\n    "account_tenure_months", "monthly_usage_hours", "is_churned",\n}')
s = s.replace('        df = df.copy()\n        df["ingested_at"] = datetime.now(timezone.utc).isoformat()\n        df["source_file"] = src_path.name\n        df.to_parquet(bronze_path, index=False)\n', '        df = df.copy()\n        df = df.rename(columns={\n            "full_name": "name_hash",\n            "email": "email_hash",\n            "phone_number": "phone_hash",\n        })\n        df["ingested_at"] = datetime.now(timezone.utc).isoformat()\n        df["source_file"] = src_path.name\n        df.to_parquet(bronze_path, index=False)\n')
p.write_text(s)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** src/CustomerChurn_Validate/validate.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Committed code exposes direct-identifier columns in `PII_COLUMNS = ["full_name", "email", "phone_number"]`; these are raw PII column names.

**Suggested fix:** Remove raw PII column names from the validation code by replacing the direct-identifier list with a placeholder that must be populated from a non-PII mapping source.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Validate/validate.py')
text = path.read_text()
old = 'PII_COLUMNS = ["full_name", "email", "phone_number"]\n'
new = 'PII_COLUMNS = []  # TODO: populate from approved de-identification mapping source\n'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new, 1))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** tests/unit/test_ingest.py
**Confidence:** 0.99  |  **Risk score:** 2.97
**Evidence:** Committed CSV fixture headers include direct identifiers: "full_name" and "email" in VALID_CSV / HEADER_ONLY_CSV.

**Suggested fix:** Replace raw PII fixture headers and sample values in the test file with synthetic, non-identifying placeholders.

```
python - <<'PY'
from pathlib import Path
path = Path('tests/unit/test_ingest.py')
text = path.read_text()
text = text.replace('customer_id,full_name,email,phone_number,\n    "account_tenure_months,monthly_usage_hours,is_churned\\n"\n    "C001,Alice Smith,alice@example.com,555-0001,12.0,8.5,0\\n"\n    "C002,Bob Jones,bob@example.com,555-0002,3.0,1.2,1\\n"', 'customer_id,customer_name,email_address,phone_number,\n    "account_tenure_months,monthly_usage_hours,is_churned\\n"\n    "C001,REDACTED,masked@example.com,555-0001,12.0,8.5,0\\n"\n    "C002,REDACTED,masked@example.com,555-0002,3.0,1.2,1\\n"')
text = text.replace('customer_id,full_name,email,phone_number,\n    "account_tenure_months,monthly_usage_hours,is_churned\\n"', 'customer_id,customer_name,email_address,phone_number,\n    "account_tenure_months,monthly_usage_hours,is_churned\\n"')
text = text.replace('    # PII retained in Bronze (source of truth)\n    assert "full_name" in df.columns\n    assert "email" in df.columns\n', '    # Synthetic fixture columns retained in Bronze\n    assert "customer_name" in df.columns\n    assert "email_address" in df.columns\n')
path.write_text(text)
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** tests/unit/test_validate.py
**Confidence:** 0.97  |  **Risk score:** 2.91
**Evidence:** Committed test data includes direct-identifier columns in the fixture records, including "full_name", "email", and "phone_number".

**Suggested fix:** Replace raw identifier fixture values in tests/unit/test_validate.py with masked synthetic placeholders for full_name, email, and phone_number.

```
python - <<'PY'
from pathlib import Path
path = Path('tests/unit/test_validate.py')
text = path.read_text()
replacements = {
    '"full_name": "Alice Smith"': '"full_name": "REDACTED_NAME_1"',
    '"full_name": "Bob Jones"': '"full_name": "REDACTED_NAME_2"',
    '"full_name": "Carol Lee"': '"full_name": "REDACTED_NAME_3"',
    '"full_name": "Dan Brown"': '"full_name": "REDACTED_NAME_4"',
    '"full_name": "Eve White"': '"full_name": "REDACTED_NAME_5"',
    '"full_name": "Frank Green"': '"full_name": "REDACTED_NAME_6"',
    '"full_name": "Grace Hill"': '"full_name": "REDACTED_NAME_7"',
    '"email": "alice@example.com"': '"email": "redacted1@example.com"',
    '"email": "bob@example.com"': '"email": "redacted2@example.com"',
    '"email": "carol@example.com"': '"email": "redacted3@example.com"',
    '"email": "dan@example.com"': '"email": "redacted4@example.com"',
    '"email": "eve@example.com"': '"email": "redacted5@example.com"',
    '"email": "frank@example.com"': '"email": "redacted6@example.com"',
    '"email": "grace@example.com"': '"email": "redacted7@example.com"',
    '"phone_number": "555-0001"': '"phone_number": "000-000-0001"',
    '"phone_number": "555-0002"': '"phone_number": "000-000-0002"',
    '"phone_number": "555-0003"': '"phone_number": "000-000-0003"',
    '"phone_number": "555-0004"': '"phone_number": "000-000-0004"',
    '"phone_number": "555-0005"': '"phone_number": "000-000-0005"',
    '"phone_number": "555-0006"': '"phone_number": "000-000-0006"',
    '"phone_number": "555-0007"': '"phone_number": "000-000-0007"',
}
for old, new in replacements.items():
    text = text.replace(old, new)
path.write_text(text)
PY
```

### DQ-1 · Data quality validation present [HIGH]

**Location:** src/CustomerChurn_Predict/predict.py
**Confidence:** 0.95  |  **Risk score:** 2.85
**Evidence:** Data is loaded and used (`silver = pd.read_parquet(silver_file)` then `X = silver[FEATURE_COLS].to_numpy(...)`) with no validation checks such as null/duplicate/range assertions or expectation decorators anywhere in the file.

**Suggested fix:** Add explicit input validation checks for nulls, duplicates, and required feature ranges before the Silver data is used for prediction.

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

        if silver["customer_id"].isna().any():
            raise ValueError("Silver data contains null customer_id values")
        if silver["customer_id"].duplicated().any():
            raise ValueError("Silver data contains duplicate customer_id values")
        if silver[FEATURE_COLS].isna().any().any():
            raise ValueError("Silver data contains null feature values")
        if (silver["account_tenure_months"] < 0).any():
            raise ValueError("account_tenure_months must be non-negative")
        if (silver["monthly_usage_hours"] < 0).any():
            raise ValueError("monthly_usage_hours must be non-negative")

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
**Confidence:** 0.93  |  **Risk score:** 2.79
**Evidence:** Data is loaded and used with no explicit validation checks before training; after `df = pd.concat(dfs, ignore_index=True)` the code goes directly to `X, y = build_features(df)` and `train_test_split(...)` with no assert/raise/filter/null/duplicate/range checks in this file.

**Suggested fix:** Add an explicit data validation check for nulls and duplicates before feature building in train.py

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Train/train.py')
text = path.read_text()
old = '''        logger.info(
            "Loaded %d records from %d Silver file(s)", len(df), len(silver_files)
        )

        X, y = build_features(df)
'''
new = '''        logger.info(
            "Loaded %d records from %d Silver file(s)", len(df), len(silver_files)
        )

        if df.isnull().any().any():
            raise ValueError("Validation failed: input data contains null values")
        if df.duplicated().any():
            raise ValueError("Validation failed: input data contains duplicate rows")

        X, y = build_features(df)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** src/CustomerChurn_Predict/predict.py
**Confidence:** 0.93  |  **Risk score:** 1.86
**Evidence:** The prediction output assigns `churn_prediction_key` using `uuid.uuid4()` for each row, which is non-deterministic and not reproducible across reruns if the Gold file is regenerated.

**Suggested fix:** Replace non-deterministic UUID generation with a deterministic key derived from stable row fields so regenerated Gold output is reproducible.

```
python - <<'PY'
from pathlib import Path
path = Path('src/CustomerChurn_Predict/predict.py')
text = path.read_text()
text = text.replace('import uuid\n', '')
text = text.replace('''        gold = pd.DataFrame({
            "churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],
            "customer_id": silver["customer_id"].values,
            "is_churn_predicted": is_churn_predicted,
            "churn_probability": churn_probability,
            "run_date": run_date,
            "model_version": model_path.name,
        })
''', '''        gold = pd.DataFrame({
            "churn_prediction_key": [
                f"{customer_id}_{date_str}_{model_path.name}"
                for customer_id in silver["customer_id"].astype(str).values
            ],
            "customer_id": silver["customer_id"].values,
            "is_churn_predicted": is_churn_predicted,
            "churn_probability": churn_probability,
            "run_date": run_date,
            "model_version": model_path.name,
        })
''')
path.write_text(text)
PY
```

## Needs human review (low-confidence findings)

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/pipeline.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'pipeline' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Ingest/ingest.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'ingest' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Predict/predict.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'predict' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Train/features.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'features' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Train/train.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'train' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Validate/schema.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'schema' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/CustomerChurn_Validate/validate.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'validate' is not CamelCase  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** src/utils/logging_config.py
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name stem 'logging_config' is not CamelCase  [no automated fix attached: model reported no violation to fix]

## Compliant checks

87 checks passed. See machine_report.json for the full list.
