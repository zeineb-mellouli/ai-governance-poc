# Quickstart: Validate Polymer Pricing ETL Pipeline

**Branch**: `001-polymer-pricing-etl` | **Phase 1** | **Date**: 2026-07-13

This guide documents runnable scenarios that prove the pipeline works end-to-end. Run these
before marking any user story complete. All expected outcomes are stated explicitly so failures
are unambiguous.

---

## Prerequisites

1. **Python 3.11** installed and on PATH.
2. **ODBC Driver 17 for SQL Server** installed
   ([Microsoft docs](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)).
3. **Azure SQL Server** database provisioned and reachable from the test machine.
4. DDL applied: run [contracts/sql-ddl.sql](contracts/sql-ddl.sql) against the target database.
5. Environment variables set (see **Setup** below).
6. Python dependencies installed: `pip install -r requirements.txt`

---

## Setup

```bash
# 1. Clone repository and navigate to root
git clone <repo-url>
cd code-polymer

# 2. Install dependencies (exact pinned versions)
pip install -r requirements.txt

# 3. Create .env from the example template (dev/test only — never commit .env)
copy .env.example .env
# Edit .env and fill in real values for all variables

# 4. Apply SQL DDL to the target database
sqlcmd -S %SQL_SERVER% -d %SQL_DATABASE% -U %SQL_USERNAME% -P %SQL_PASSWORD% \
       -i specs/001-polymer-pricing-etl/contracts/sql-ddl.sql

# 5. Create the data directory structure
mkdir data\landing data\bronze\CodePolymer_Pricing data\silver\CodePolymer_Pricing
mkdir data\gold\CodePolymer_Pricing logs
```

**Required environment variables** — see [contracts/pipeline-contracts.md §6](contracts/pipeline-contracts.md)
for the full contract. Minimum set for local validation:

```
SQL_SERVER=<your-server>.database.windows.net
SQL_DATABASE=PolymerReporting
SQL_USERNAME=svc_pipeline
SQL_PASSWORD=<secret>
LANDING_DIR=data/landing
BRONZE_DIR=data/bronze
SILVER_DIR=data/silver
GOLD_DIR=data/gold
LOG_DIR=logs
```

---

## Test Data

Create `data/landing/PolymerPricing_20260713.csv` with this content for the happy-path
scenarios:

```csv
material_code,pricing_date,price_value,unit_of_measure,currency_code
PE-HD-001,2026-07-13,1250.50,MT,USD
PP-HOM-002,2026-07-13,1180.00,MT,USD
PET-BG-003,2026-07-13,875.25,MT,EUR
PVC-SUS-004,2026-07-13,950.75,MT,USD
PA-6-005,2026-07-13,2400.00,MT,EUR
```

For the **validation rejection** scenario, create
`data/landing/PolymerPricing_20260714.csv`:

```csv
material_code,pricing_date,price_value,unit_of_measure,currency_code
PE-HD-001,2026-07-14,1260.00,MT,USD
,2026-07-14,1100.00,MT,USD
PP-HOM-002,2026-07-14,150000.00,MT,USD
PET-BG-003,2026-07-14,890.00,MT,EUR
PE-HD-001,2026-07-14,1265.00,MT,USD
```
*(Row 2: null material_code. Row 3: price_value > 100,000. Rows 1+5: duplicate material_code
for 2026-07-14.)*

---

## Scenario 1 — Happy Path: End-to-End Pipeline (User Story 3)

**Purpose**: Proves all three scripts run successfully and data reaches the reporting table.

```bash
python pipeline/01_IngestData.py --date 20260713
python pipeline/02_TransformData.py --date 20260713
python pipeline/03_LoadToWarehouse.py --date 20260713
```

**Expected outcomes**:

| Check | How to verify | Expected result |
|-------|--------------|-----------------|
| Bronze CSV created | `dir data\bronze\CodePolymer_Pricing\` | `PolymerPricingBronze_20260713.csv` present |
| Bronze has 5 rows + metadata | Open CSV | 5 data rows; `source_file_name` and `ingestion_timestamp` columns present |
| Silver Parquet created | `dir data\silver\CodePolymer_Pricing\` | `PolymerPricingSilver_20260713.parquet` present |
| Silver has 5 rows | `python -c "import pandas as pd; print(len(pd.read_parquet('data/silver/CodePolymer_Pricing/PolymerPricingSilver_20260713.parquet')))"` | `5` |
| Gold Parquet created | `dir data\gold\CodePolymer_Pricing\` | `PolymerPricingGold_20260713.parquet` present |
| Gold has 5 rows (1 per material per date) | Same as silver check | `5` |
| Rows in PolymerPricingFact | `sqlcmd -Q "SELECT COUNT(*) FROM Reporting.PolymerPricingFact WHERE pricing_date = '2026-07-13'"` | `5` |
| Log file present with START/END entries | `dir logs\` then open log | Log file for run date; contains `START` and `END` entries; no ERROR entries |

---

## Scenario 2 — Idempotency: Re-run Same Date (FR-011, SC-006)

**Purpose**: Proves that re-running the pipeline for an already-processed date does not
duplicate records.

```bash
# Re-run all three scripts for the same date as Scenario 1
python pipeline/01_IngestData.py --date 20260713
python pipeline/02_TransformData.py --date 20260713
python pipeline/03_LoadToWarehouse.py --date 20260713
```

**Expected outcomes**:

| Check | Expected result |
|-------|-----------------|
| Bronze step | Logs a WARNING ("bronze file already exists for 20260713, skipping ingest"); exits cleanly |
| Silver Parquet row count | Unchanged — still 5 rows |
| Gold Parquet row count | Unchanged — still 5 rows |
| `Reporting.PolymerPricingFact` row count for `pricing_date = '2026-07-13'` | Still `5` — MERGE upserted, did not insert new rows |

---

## Scenario 3 — Validation Rejection: Dirty Input (User Story 2, FR-004, FR-005)

**Purpose**: Proves pandera validation correctly rejects nulls, out-of-range prices, and
deduplicates before writing to silver.

```bash
python pipeline/01_IngestData.py --date 20260714
```

**Expected outcomes** (no `02_TransformData` or `03_LoadToWarehouse` run needed):

| Check | Expected result |
|-------|-----------------|
| Bronze CSV row count | 5 rows (all source rows preserved, including the invalid ones) |
| Silver Parquet row count | 2 rows (`PET-BG-003` and first `PE-HD-001`; others rejected) |
| Log WARNING: null rejection | Log entry: 1 row rejected — null `material_code` |
| Log WARNING: range rejection | Log entry: 1 row rejected — `price_value` 150000.00 exceeds 100,000 |
| Log WARNING: duplicate dropped | Log entry: 1 duplicate row dropped (`PE-HD-001` / `2026-07-14`) |
| No ERROR log entries | Run completes as WARNING, not failure |

---

## Scenario 4 — Missing Credential: Startup Failure (FR-008, SC-005)

**Purpose**: Proves the pipeline fails safely at startup when a required environment variable
is absent.

```bash
# Temporarily unset SQL_PASSWORD
set SQL_PASSWORD=
python pipeline/03_LoadToWarehouse.py --date 20260713
```

**Expected outcomes**:

| Check | Expected result |
|-------|-----------------|
| Exit code | Non-zero |
| Log file | Contains `ERROR` entry: "Required environment variable SQL_PASSWORD is not set" |
| Bronze/Silver/Gold files | Unchanged — no data was read or written |
| Database | Unchanged — no connection was attempted |

---

## Scenario 5 — Empty Source File (Edge Case)

**Purpose**: Proves the pipeline handles a zero-row CSV without error.

Create `data/landing/PolymerPricing_20260715.csv` with headers only (no data rows):

```csv
material_code,pricing_date,price_value,unit_of_measure,currency_code
```

```bash
python pipeline/01_IngestData.py --date 20260715
```

**Expected outcomes**:

| Check | Expected result |
|-------|-----------------|
| Exit code | `0` (success) |
| Bronze CSV | Not written (zero-row batch; WARNING logged) |
| Silver Parquet | Not written |
| Log | WARNING entry: "Source file has 0 data rows for date 20260715; skipping all layer writes" |

---

## Full Pipeline Sign-off Checklist

Before merging the feature branch, confirm all of the following with a reviewer:

- [ ] Scenario 1 passes: all 5 rows in `Reporting.PolymerPricingFact` with `pricing_date = '2026-07-13'`
- [ ] Scenario 2 passes: re-run produces no new rows
- [ ] Scenario 3 passes: silver has 2 rows; log shows 3 rejected/dropped entries
- [ ] Scenario 4 passes: fails at startup with ERROR log; no data written
- [ ] Scenario 5 passes: exits cleanly with WARNING; no files written
- [ ] No `print()` calls present in any pipeline script (Constitution IV)
- [ ] No credential values present in any committed file (Constitution I)
- [ ] `requirements.txt` uses exact version pins for all 7 dependencies (Constitution VII)
- [ ] `azure-pipelines.yml` CI build passes on the feature branch
- [ ] All pytest unit and integration tests pass: `pytest tests/ -v`
