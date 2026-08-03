# fin-code-collateral_management

Finance · Code · Collateral Management

## Purpose

Tracks collateral posted and received against derivative positions and
computes daily margin call requirements.

## Structure — Medallion architecture

| Folder | Medallion layer | Contents |
|---|---|---|
| `bronze/` | Bronze | Raw collateral positions from the collateral management system |
| `silver/` | Silver | Validated collateral positions |
| `gold/` | Gold | Daily margin call report |
| `Collateral_Pipeline/` | — | `01` Bronze→Silver · `02` Silver→Gold margin call computation |
| `Collateral_SQL/` | — | DDL for Reporting.CollateralFact |

## How to run

```bash
pip install -r requirements.txt

python Collateral_Pipeline/01_IngestPositions.py
python Collateral_Pipeline/02_ComputeMarginCalls.py
```

## Branch strategy

| Branch | Purpose |
|---|---|
| `master` | Production-ready — protected, requires PR review |
| `develop` | Integration branch |
| `user-story/{id}` | Feature work |

Commit message format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
