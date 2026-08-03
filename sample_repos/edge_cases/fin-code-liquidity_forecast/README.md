# fin-code-liquidity_forecast

Finance · Code · Treasury Liquidity Forecast

## Purpose

Aggregates daily bank account balances and cash movements across
currencies to forecast a 30-day liquidity position for Treasury.

## Structure — Medallion architecture

Data flows strictly Bronze → Silver → Gold. Bronze is immutable.

| Folder | Medallion layer | Contents |
|---|---|---|
| `bronze/` | Bronze | Raw ingested bank balance and cash movement CSVs |
| `silver/` | Silver | Validated, deduplicated balances and movements |
| `gold/` | Gold | 30-day liquidity forecast, ready for the Treasury dashboard |
| `Treasury_Pipeline/` | — | `01` Bronze→Silver · `02` Silver validation · `03` Silver→Gold forecast |
| `Treasury_SQL/` | — | DDL for Reporting.CounterpartyDim and Reporting.LiquidityForecastFact |

## How to run

```bash
pip install -r requirements.txt

python Treasury_Pipeline/01_IngestCashPositions.py
python Treasury_Pipeline/02_ValidateAndTransform.py
python Treasury_Pipeline/03_ForecastLiquidity.py
```

## Branch strategy

| Branch | Purpose |
|---|---|
| `master` | Production-ready — protected, requires PR review |
| `develop` | Integration branch — merge target for feature branches |
| `user-story/{id}` | Feature work — id is the DevOps user-story number |

Commit message format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
Each commit represents one logical change.
