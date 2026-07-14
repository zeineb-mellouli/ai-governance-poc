# ops-code-market_rate

Operations · Code · Market Rate Pipeline

## Purpose

ETL pipeline that ingests daily ethanol and polymers market rate data,
validates quality, transforms to a star-schema structure, and loads
into the Reporting data warehouse.

## Structure — Medallion architecture

Data flows strictly Bronze → Silver → Gold. Bronze is immutable.

| Folder | Medallion layer | Contents |
|---|---|---|
| `bronze/` | Bronze | Raw ingested CSVs — written once by ingestion, never modified downstream |
| `silver/` | Silver | Validated and cleansed records — quality checks applied before every write |
| `gold/` | Gold | Aggregated, warehouse-ready records — consumed by the load script and reporting |
| `MarketRate_Pipeline/` | — | `01` Bronze→Silver · `02` Silver→Gold · `03` Gold→Warehouse |
| `MarketRate_SQL/` | — | DDL for Reporting.EthanolMarketRateFact and Reporting.ProductDim |

## How to run

```bash
pip install -r requirements.txt

python MarketRate_Pipeline/01_IngestData.py
python MarketRate_Pipeline/02_TransformData.py
python MarketRate_Pipeline/03_LoadToWarehouse.py
```

Set the following environment variables before running:

| Variable | Description |
|---|---|
| `DB_SERVER` | SQL Server hostname |
| `DB_NAME` | Target database name |
| `DB_USERNAME` | Service account username |
| `DB_PASSWORD` | Service account password (use Azure Key Vault in production) |
| `DATA_PATH` | Override default data folder (optional) |

## Branch strategy

| Branch | Purpose |
|---|---|
| `master` | Production-ready — protected, requires PR review |
| `develop` | Integration branch — merge target for feature branches |
| `user-story/{id}` | Feature work — id is the DevOps user-story number |

Commit message format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
Each commit represents one logical change.
