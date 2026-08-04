# Compliance Report — fin-code-filing_deadline_tracker

Run at: 2026-08-04T12:21:44.012066+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\not_applicable\fin-code-filing_deadline_tracker

## Summary

- Total findings evaluated: 43
- COMPLIANT: 12
- NEEDS_REVIEW: 1
- NON_COMPLIANT: 2
- NOT_APPLICABLE: 28

## Non-compliant findings

### REPRO-6 · Reproducibility [MEDIUM]

**Location:** azure-pipelines.yml
**Confidence:** 0.95  |  **Risk score:** 1.9
**Evidence:** requirements.txt is installed via `pip install -r requirements.txt`, but the file content does not show pinned versions; reproducibility policy requires every package to be pinned.

**Suggested fix:** Pin all packages in requirements.txt before installation to satisfy reproducibility.

```
# Update requirements.txt so every dependency is pinned to an exact version, then keep the existing install step:
pip install -r requirements.txt
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/UpcomingFilingAlerts_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'UpcomingFilingAlerts_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename the CSV file to use the required _yyyy-MM-dd date suffix format derived from the existing 20240901 value.

```
git mv data/UpcomingFilingAlerts_20240901.csv data/UpcomingFilingAlerts_2024-09-01.csv
```

## Needs human review (low-confidence findings)

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/RegulatoryFilingDeadlines_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'RegulatoryFilingDeadlines_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd  [no automated fix attached: model reported no violation to fix]

## Compliant checks

12 checks passed. See machine_report.json for the full list.
