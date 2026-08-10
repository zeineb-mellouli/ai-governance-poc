# Compliance Report — fin-code-credit_scoring_model

Run at: 2026-08-10T09:03:47.162615+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\ambiguous\fin-code-credit_scoring_model
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 93.0% (80/86 weighted checks)

> 1 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 58
- Applicable checks (compliant + non-compliant): 41
- COMPLIANT: 37
- NON_COMPLIANT: 4
- NOT_APPLICABLE: 17
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 4

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** CreditScoring_Pipeline/02_TrainScoringModel.py
**Sample agreement:** 100%
**Evidence:** The file loads data and uses it for modeling and output without any explicit quality validation first.  Quoted: 'applications = pd.read_csv("silver/CreditApplications_validated_20240901.csv")'

**Suggested fix:** Add an explicit data-quality validation step before modeling and output in the training script.

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
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    if applications[required_cols].isnull().any().any():
        raise ValueError("Data quality validation failed: null values found in required columns")

    X = applications[feature_cols].values
    y = applications["defaulted"].values
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** bronze/CreditApplications_20240901.csv
**Sample agreement:** 100%
**Evidence:** file name 'CreditApplications_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'bronze/CreditApplications_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv bronze/CreditApplications_20240901.csv bronze/CreditApplications_2024-09-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/CreditScoringResults_20240901.csv
**Sample agreement:** 100%
**Evidence:** file name 'CreditScoringResults_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'gold/CreditScoringResults_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv gold/CreditScoringResults_20240901.csv gold/CreditScoringResults_2024-09-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** silver/CreditApplications_validated_20240901.csv
**Sample agreement:** 100%
**Evidence:** file name 'CreditApplications_validated_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd; file name stem 'CreditApplications_validated' is not CamelCase

**Suggested fix:** Rename to 'silver/CreditApplicationsValidated_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv silver/CreditApplications_validated_20240901.csv silver/CreditApplicationsValidated_2024-09-01.csv
```

## Checks that passed or did not apply

37 checks passed; 17 did not apply to this repository. See machine_report.json for the full list.
