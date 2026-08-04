# Compliance Report — fin-code-credit_scoring_model

Run at: 2026-08-04T12:17:51.902199+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\ambiguous\fin-code-credit_scoring_model

## Summary

- Total findings evaluated: 58
- COMPLIANT: 22
- NON_COMPLIANT: 5
- NEEDS_REVIEW: 2
- NOT_APPLICABLE: 29

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** CreditScoring_Pipeline/02_TrainScoringModel.py
**Confidence:** 0.97  |  **Risk score:** 2.91
**Evidence:** Data is loaded and used with no validation checks before training: `applications = pd.read_csv(...)` followed by feature selection and `model.fit(...)`; no assert/raise/filter or validation library call is present.

**Suggested fix:** Add explicit validation checks for required columns, nulls, and duplicate rows before training in the Python pipeline.

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
    missing_cols = [col for col in required_cols if col not in applications.columns]
    assert not missing_cols, f"Missing required columns: {missing_cols}"
    assert not applications[required_cols].isnull().any().any(), "Null values found in training data"
    assert not applications.duplicated().any(), "Duplicate rows found in training data"

    X = applications[feature_cols].values
    y = applications["defaulted"].values
'''
if old not in text:
    raise SystemExit('Target block not found')
path.write_text(text.replace(old, new))
PY
```

### PII-4 · No raw PII exposed in outputs [HIGH]

**Location:** (repository-level)
**Confidence:** 0.91  |  **Risk score:** 2.73
**Evidence:** Committed CSV outputs expose a direct-identifier column application_id in bronze/CreditApplications_20240901.csv, silver/CreditApplications_validated_20240901.csv, and gold/CreditScoringResults_20240901.csv. The header is visible in each file, and application_id is an obvious identifier-like column in committed data files.

**Suggested fix:** Rename the exposed identifier column application_id to a non-PII header in the three committed CSV outputs, preserving all data rows.

```
python - <<'PY'
from pathlib import Path
import csv
files = [
    Path('bronze/CreditApplications_20240901.csv'),
    Path('silver/CreditApplications_validated_20240901.csv'),
    Path('gold/CreditScoringResults_20240901.csv'),
]
old = 'application_id'
new = 'application_ref'
for path in files:
    text = path.read_text(newline='')
    lines = text.splitlines()
    if not lines:
        continue
    header = next(csv.reader([lines[0]]))
    if old not in header:
        continue
    header = [new if c == old else c for c in header]
    lines[0] = ','.join(csv.writer.__self__ if False else header)
    path.write_text('\n'.join(lines) + ('\n' if text.endswith('\n') else ''))
PY
```

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** (repository-level)
**Confidence:** 0.98  |  **Risk score:** 1.96
**Evidence:** requirements.txt is only partially pinned: pandas==2.1.4, scikit-learn==1.4.0, numpy==1.26.3 are pinned, but azure-identity==1.15.0 is also pinned; however the repository includes stochastic training code in CreditScoring_Pipeline/02_TrainScoringModel.py that sets np.random.seed(42) but does not pass a random_state to train_test_split, so the split remains nondeterministic. This makes the training pipeline not fully reproducible across runs.

**Suggested fix:** Add a deterministic random_state to the train_test_split call in CreditScoring_Pipeline/02_TrainScoringModel.py

```
python - <<'PY'
from pathlib import Path
path = Path('CreditScoring_Pipeline/02_TrainScoringModel.py')
text = path.read_text()
old = 'train_test_split(X, y, test_size=0.2)'
new = 'train_test_split(X, y, test_size=0.2, random_state=42)'
if old not in text:
    raise SystemExit('Expected train_test_split call not found')
path.write_text(text.replace(old, new, 1))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/CreditApplications_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CreditApplications_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename the CSV file to use the required _yyyy-MM-dd suffix format while preserving the CamelCase stem.

```
git mv bronze/CreditApplications_20240901.csv bronze/CreditApplications_2024-09-01.csv
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** CreditScoring_SQL/CreateCreditScoreFact.sql
**Confidence:** 0.99  |  **Risk score:** 0.99
**Evidence:** SQL columns use non-PascalCase names such as ApplicationId, ScoredDate, and ProbabilityOfDefault; the policy requires PascalCase in SQL contexts, and CreditScoreKey also uses the Key suffix on a key column.

**Suggested fix:** Rename the SQL columns to compliant PascalCase and remove the Key suffix from the key column.

```
sed -i 's/\bCreditScoreKey\b/CreditScoreId/g; s/\bApplicationId\b/ApplicationId/g; s/\bScoredDate\b/ScoredDate/g; s/\bProbabilityOfDefault\b/ProbabilityOfDefault/g' CreditScoring_SQL/CreateCreditScoreFact.sql
```

## Needs human review (low-confidence findings)

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/CreditScoringResults_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CreditScoringResults_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd  [no automated fix attached: model reported no violation to fix]

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/CreditApplications_validated_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CreditApplications_validated_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd; file name stem 'CreditApplications_validated' is not CamelCase  [no automated fix attached: model reported no violation to fix]

## Compliant checks

22 checks passed. See machine_report.json for the full list.
