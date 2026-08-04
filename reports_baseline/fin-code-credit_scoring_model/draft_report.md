# Compliance Report — fin-code-credit_scoring_model

Run at: 2026-08-03T13:25:24.199756+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\ambiguous\fin-code-credit_scoring_model

## Summary

- Total findings evaluated: 72
- COMPLIANT: 33
- NOT_APPLICABLE: 37
- NON_COMPLIANT: 2

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** CreditScoring_Pipeline/02_TrainScoringModel.py
**Confidence:** 0.93  |  **Risk score:** 2.79
**Evidence:** Data is loaded and used with no validation checks before training: `applications = pd.read_csv(...)` followed directly by feature selection and `model.fit(...)`; no asserts, filters, or validation calls are present.

**Suggested fix:** Add a minimal data validation check before training to ensure required columns are present and contain no missing values.

```
python - <<'PY'
from pathlib import Path
path = Path('CreditScoring_Pipeline/02_TrainScoringModel.py')
text = path.read_text()
old = '''def main() -> None:
    applications = pd.read_csv("silver/CreditApplications_validated_20240901.csv")

    feature_cols = ["annual_income", "existing_debt", "credit_history_months"]
    X = applications[feature_cols].values
    y = applications["defaulted"].values
'''
new = '''def main() -> None:
    applications = pd.read_csv("silver/CreditApplications_validated_20240901.csv")

    feature_cols = ["annual_income", "existing_debt", "credit_history_months"]
    required_cols = feature_cols + ["defaulted"]
    missing = [c for c in required_cols if c not in applications.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if applications[required_cols].isna().any().any():
        raise ValueError("Input data contains missing values in required columns")

    X = applications[feature_cols].values
    y = applications["defaulted"].values
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### DM-7 · Star schema / shared output table design [MEDIUM]

**Location:** CreditScoring_Pipeline/02_TrainScoringModel.py
**Confidence:** 0.90  |  **Risk score:** 1.8
**Evidence:** The script writes a reusable output file `gold/CreditScoringResults_20240901.csv`, but there is no documented grain/primary key or row-level meaning in comments/docstring beyond a brief title.

**Suggested fix:** Add a brief docstring/comment documenting the output table grain and primary key for the reusable scoring results file.

```
python - <<'PY'
from pathlib import Path
p = Path('CreditScoring_Pipeline/02_TrainScoringModel.py')
text = p.read_text()
old = '"""Train the credit scoring model used to grade new credit applications."""\n'
new = '"""Train the credit scoring model used to grade new credit applications.\n\nOutput grain: one row per validated credit application; primary key: application_id.\nThe gold output file CreditScoringResults_20240901.csv contains one scored row per application.\n"""\n'
if old in text:
    text = text.replace(old, new, 1)
p.write_text(text)
PY
```

## Compliant checks

33 checks passed. See machine_report.json for the full list.
