# Compliance Report — fin-code-filing_deadline_tracker

Run at: 2026-08-10T09:12:04.013408+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\not_applicable\fin-code-filing_deadline_tracker
Self-consistency samples (k): 3

## Summary

**Grade: NEEDS_WORK** — severity-weighted pass rate 91.8% (45/49 weighted checks)

- Checks evaluated: 38
- Applicable checks (compliant + non-compliant): 24
- COMPLIANT: 21
- NON_COMPLIANT: 3
- NOT_APPLICABLE: 14
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 3

## Non-compliant findings

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 67%
**Evidence:** The output path data/UpcomingFilingAlerts_20240901.csv is written by FilingTracker_Pipeline/01_CheckUpcomingDeadlines.py, and no file in the repository states what one row in that report represents.  Quoted: 'data/UpcomingFilingAlerts_20240901.csv'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Add repository-level documentation stating the row grain for data/UpcomingFilingAlerts_20240901.csv as one alert per upcoming filing deadline per entity.

```
printf '%s
' 'data/UpcomingFilingAlerts_20240901.csv: one row per upcoming filing deadline alert for a single entity/filing.' > OUTPUT_GRAIN.md
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/RegulatoryFilingDeadlines_20240901.csv
**Sample agreement:** 100%
**Evidence:** file name 'RegulatoryFilingDeadlines_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'data/RegulatoryFilingDeadlines_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/RegulatoryFilingDeadlines_20240901.csv data/RegulatoryFilingDeadlines_2024-09-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/UpcomingFilingAlerts_20240901.csv
**Sample agreement:** 100%
**Evidence:** file name 'UpcomingFilingAlerts_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'data/UpcomingFilingAlerts_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/UpcomingFilingAlerts_20240901.csv data/UpcomingFilingAlerts_2024-09-01.csv
```

## Checks that passed or did not apply

21 checks passed; 14 did not apply to this repository. See machine_report.json for the full list.
