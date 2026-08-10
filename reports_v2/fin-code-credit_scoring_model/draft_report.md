# Compliance Report — fin-code-credit_scoring_model

Run at: 2026-08-10T08:15:49.016031+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\ambiguous\fin-code-credit_scoring_model
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 90.4% (75/83 weighted checks)

> 1 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 40
- COMPLIANT: 35
- NON_COMPLIANT: 5
- NOT_APPLICABLE: 18
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 5

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** CreditScoring_Pipeline/02_TrainScoringModel.py
**Confidence:** 1.00  |  **Risk score:** 3.0
**Evidence:** The file uses loaded data for training and output without any explicit quality check first.  Quoted: 'applications = pd.read_csv("silver/CreditApplications_validated_20240901.csv")'

**Suggested fix:** Add an explicit data quality validation check before training and scoring the loaded applications data.

```
python - <<'PY'
from pathlib import Path
path = Path('CreditScoring_Pipeline/02_TrainScoringModel.py')
text = path.read_text()
old = 'def main() -> None:\n    applications = pd.read_csv("silver/CreditApplications_validated_20240901.csv")\n\n    feature_cols = ["annual_income", "existing_debt", "credit_history_months"]\n'
new = 'def main() -> None:\n    applications = pd.read_csv("silver/CreditApplications_validated_20240901.csv")\n\n    feature_cols = ["annual_income", "existing_debt", "credit_history_months"]\n    required_cols = feature_cols + ["defaulted"]\n    missing_cols = [col for col in required_cols if col not in applications.columns]\n    if missing_cols:\n        raise ValueError(f"Missing required columns: {missing_cols}")\n    if applications[required_cols].isnull().any().any():\n        raise ValueError("Data quality check failed: null values found in required columns")\n\n'
if old not in text:
    raise SystemExit('Target block not found')
path.write_text(text.replace(old, new))
PY
```

### REPRO-6 · Random seeds fixed for stochastic steps [MEDIUM]

**Location:** CreditScoring_Pipeline/02_TrainScoringModel.py
**Confidence:** 1.00  |  **Risk score:** 2.0
**Evidence:** The train/test split is stochastic but lacks a random_state, so reproducibility is not fully fixed.  Quoted: 'X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)'

**Suggested fix:** Add a fixed random_state to the stochastic train/test split in the training script.

```
python - <<'PY'
from pathlib import Path
path = Path('CreditScoring_Pipeline/02_TrainScoringModel.py')
text = path.read_text()
old = '    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)\n'
new = '    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)\n'
if old not in text:
    raise SystemExit('target line not found')
path.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/CreditApplications_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CreditApplications_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/CreditApplications_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/CreditApplications_20240901.csv bronze/CreditApplications_2024-09-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/CreditScoringResults_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CreditScoringResults_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/CreditScoringResults_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/CreditScoringResults_20240901.csv gold/CreditScoringResults_2024-09-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/CreditApplications_validated_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'CreditApplications_validated_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd; file name stem 'CreditApplications_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/CreditApplicationsValidated_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/CreditApplications_validated_20240901.csv silver/CreditApplicationsValidated_2024-09-01.csv
```

## Checks that passed or did not apply

35 checks passed; 18 did not apply to this repository. See machine_report.json for the full list.
