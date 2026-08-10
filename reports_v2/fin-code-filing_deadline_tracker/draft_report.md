# Compliance Report — fin-code-filing_deadline_tracker

Run at: 2026-08-10T08:24:30.961281+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\not_applicable\fin-code-filing_deadline_tracker
Self-consistency samples (k): 3

## Summary

**Grade: NEEDS_WORK** — severity-weighted pass rate 95.7% (45/47 weighted checks)

- Checks evaluated: 38
- Applicable checks (compliant + non-compliant): 23
- COMPLIANT: 21
- NON_COMPLIANT: 2
- NOT_APPLICABLE: 15
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 2

## Non-compliant findings

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/RegulatoryFilingDeadlines_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'RegulatoryFilingDeadlines_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'data/RegulatoryFilingDeadlines_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/RegulatoryFilingDeadlines_20240901.csv data/RegulatoryFilingDeadlines_2024-09-01.csv
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** data/UpcomingFilingAlerts_20240901.csv
**Confidence:** 1.00  |  **Risk score:** 1.0
**Evidence:** file name 'UpcomingFilingAlerts_20240901.csv' ends in an 8-digit date suffix '20240901'; the required format is _yyyy-MM-dd

**Suggested fix:** Rename to 'data/UpcomingFilingAlerts_2024-09-01.csv' to satisfy the NAM-5 naming grammar.

```
git mv data/UpcomingFilingAlerts_20240901.csv data/UpcomingFilingAlerts_2024-09-01.csv
```

## Checks that passed or did not apply

21 checks passed; 15 did not apply to this repository. See machine_report.json for the full list.
