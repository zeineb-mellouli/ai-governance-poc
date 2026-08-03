# fin-code-polymer_pricing — Polymer Pricing ETL Pipeline

Daily batch ETL pipeline for the Finance team. Ingests polymer pricing CSV files
into a three-layer medallion architecture (bronze → silver → gold) and loads the
gold data into `Reporting.PolymerPricingFact` in Azure SQL Server.

> **Note (Constitution X)**: The target repository name should follow the
> `{dept}-{resource}-{project_name}` pattern — e.g. `fin-code-polymer_pricing`.
> If the current repo is not yet renamed, coordinate the rename with the team.

---

## Medallion Architecture

```
data/landing/                           ← Source CSVs (PolymerPricing_yyyyMMdd.csv)
    │
    ▼ [01_IngestData.py]
data/bronze/CodePolymer_Pricing/        ← Immutable raw copy + metadata (CSV)
    │
    ▼ [01_IngestData.py — silver step]
data/silver/CodePolymer_Pricing/        ← Validated & deduplicated (Parquet)
    │
    ▼ [02_TransformData.py]
data/gold/CodePolymer_Pricing/          ← 1 row per material per date (Parquet)
    │
    ▼ [03_LoadToWarehouse.py]
Reporting.PolymerPricingFact            ← Azure SQL Server (MERGE upsert)
```

Bronze is **immutable** — no transform script may overwrite it.

---

## Prerequisites

- Python 3.11
- [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Azure SQL Server database with DDL applied (see **Database Setup** below)

---

## Setup

```bash
# 1. Install dependencies (exact pinned versions — Constitution VII)
pip install -r requirements.txt

# 2. Configure environment variables
copy .env.example .env
# Edit .env with real values — NEVER commit .env
```

---

## Required Environment Variables

See `.env.example` for the full list with descriptions.

| Variable | Purpose |
|----------|---------|
| `SQL_SERVER` | Azure SQL Server hostname |
| `SQL_DATABASE` | Database name |
| `SQL_USERNAME` | SQL login |
| `SQL_PASSWORD` | SQL password (**secret**) |
| `LANDING_DIR` | Path to source CSV landing folder |
| `BRONZE_DIR` | Path to bronze root |
| `SILVER_DIR` | Path to silver root |
| `GOLD_DIR` | Path to gold root |
| `LOG_DIR` | Path for log file output |

---

## Database Setup

Apply the DDL scripts once to provision the target tables:

```bash
sqlcmd -S %SQL_SERVER% -d %SQL_DATABASE% -U %SQL_USERNAME% -P %SQL_PASSWORD% \
       -i sql/CreateMaterialDim.sql

sqlcmd -S %SQL_SERVER% -d %SQL_DATABASE% -U %SQL_USERNAME% -P %SQL_PASSWORD% \
       -i sql/CreatePolymerPricingFact.sql
```

---

## Running the Pipeline

Run the three scripts in order for a given processing date (`YYYYMMDD`):

```bash
python pipeline/01_IngestData.py --date 20260713
python pipeline/02_TransformData.py --date 20260713
python pipeline/03_LoadToWarehouse.py --date 20260713
```

All operational output is written to `LOG_DIR/PipelineRun_yyyyMMdd.log`.
No `print()` statements — all messages go through the Python `logging` module
with a `FileHandler` (Constitution IV).

---

## Running Tests

```bash
# Unit tests only (no DB connection required)
pytest tests/unit/ -v

# All tests including integration (requires live Azure SQL + env vars set)
pytest tests/ -v
```

---

## Azure DevOps Branch Policy Setup (Constitution VIII)

The minimum-1-reviewer PR policy **cannot** be set in `azure-pipelines.yml`.
Configure it in the Azure DevOps portal for both `master` and `develop` branches:

1. **Repos** → **Branches** → select `master` (repeat for `develop`)
2. **Branch policies** → enable **"Require a minimum number of reviewers"** → set to **1**
3. Enable **"Build validation"** → link to the `azure-pipelines.yml` pipeline
4. Optionally enable **"Check for linked work items"**

---

## Project Constitution

Governance principles for this project are documented in
[`.specify/memory/constitution.md`](.specify/memory/constitution.md).
Key NON-NEGOTIABLE principles:

- **I. Security First** — credentials from `os.environ` only
- **II. Data Quality Gate** — pandera validation before every layer write
- **III. Medallion Architecture** — bronze never overwritten; no layer skipping
