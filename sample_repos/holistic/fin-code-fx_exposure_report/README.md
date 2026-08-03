# fin-code-fx_exposure_report

Finance · Code · Treasury FX Exposure Report

## Purpose

Aggregates the quarter-end FX position feed from the custodian into the
quarterly FX exposure report used in the Treasury board pack.

## Structure — Medallion architecture

| Folder | Medallion layer | Contents |
|---|---|---|
| `bronze/` | Bronze | Raw FX positions as received from the custodian feed |
| `staging/` | Silver | Validated FX positions, ready for reporting |
| `gold/` | Gold | Quarterly FX exposure report for the board pack |
| `Treasury_Pipeline/` | — | `01` Bronze→Silver · `02` Silver→Gold |
| `Treasury_SQL/` | — | DDL for Reporting.FXExposureFact |

## How to run

```bash
pip install -r requirements.txt

python Treasury_Pipeline/01_IngestFXPositions.py
python Treasury_Pipeline/02_GenerateExposureReport.py
```

## Branch strategy

| Branch | Purpose |
|---|---|
| `master` | Production-ready — protected, requires PR review |
| `develop` | Integration branch |
| `user-story/{id}` | Feature work |

Commit message format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
