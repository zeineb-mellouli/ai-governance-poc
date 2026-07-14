# Pipeline Data Contracts

**Branch**: `001-polymer-pricing-etl` | **Phase 1** | **Date**: 2026-07-13

These contracts define the data interfaces between pipeline stages. Any change to a contract
requires updating the corresponding pandera schema in `pipeline/schemas/pricing_schema.py` and
the downstream stage that consumes it.

---

## 1. Source CSV Contract (Landing Zone)

**File naming**: `PolymerPricing_yyyyMMdd.csv` (Constitution VI: CamelCase + date suffix)
**Location**: `data/landing/`
**Encoding**: UTF-8
**Delimiter**: comma (`,`)
**Header row**: required (row 1)
**Quote character**: `"` (double-quote, optional)

| Column | Expected type | Nullable | Example value |
|--------|--------------|----------|---------------|
| `material_code` | string | No | `PE-HD-001` |
| `pricing_date` | date string `YYYY-MM-DD` | No | `2026-07-13` |
| `price_value` | decimal | No | `1250.50` |
| `unit_of_measure` | string | No | `MT` |
| `currency_code` | string (3-char ISO 4217) | No | `USD` |

**Contract violation handling**: If mandatory columns are missing or the file cannot be parsed,
`01_IngestData` fails with a structured ERROR log entry. No partial data is written. The run is
safe to retry once the source file is corrected.

---

## 2. Bronze Layer Contract

**File naming**: `PolymerPricingBronze_yyyyMMdd.csv`
**Location**: `data/bronze/CodePolymer_Pricing/`
**Format**: CSV (same as source; never transformed)
**Written by**: `01_IngestData`
**Read by**: `01_IngestData` (silver step, same execution)

All source columns preserved exactly. Two metadata columns appended:

| Column | Type | Added by | Notes |
|--------|------|----------|-------|
| `source_file_name` | string | `01_IngestData` | Basename of source file (e.g. `PolymerPricing_20260713.csv`) |
| `ingestion_timestamp` | ISO 8601 datetime string | `01_IngestData` | UTC timestamp at ingest time |

**Immutability contract**: No script other than `01_IngestData` (write path only) may write to
`data/bronze/`. Transform scripts (`02_TransformData`, `03_LoadToWarehouse`) must never read
from or write to the bronze path. `01_IngestData` must check for an existing bronze file for the
given date and skip the write if one exists (idempotency).

---

## 3. Silver Layer Contract

**File naming**: `PolymerPricingSilver_yyyyMMdd.parquet`
**Location**: `data/silver/CodePolymer_Pricing/`
**Format**: Apache Parquet (typed, snappy-compressed)
**Written by**: `01_IngestData` (after pandera `SilverSchema` validation)
**Read by**: `02_TransformData`

| Column | pandas dtype | Nullable | Validation |
|--------|-------------|----------|------------|
| `material_code` | `object` | No | Not null; not empty string |
| `pricing_date` | `datetime64[ns]` | No | Not null; valid date; not in future |
| `price_value` | `float64` | No | `> 0.0` and `< 100_000.0` |
| `unit_of_measure` | `object` | No | Not null; not empty string |
| `currency_code` | `object` | No | Not null; exactly 3 uppercase alpha chars (`^[A-Z]{3}$`) |
| `source_file_name` | `object` | No | Not null; not empty string |
| `ingestion_timestamp` | `datetime64[ns]` | No | Not null |

**Uniqueness guarantee**: Exactly one row per (`material_code`, `pricing_date`) after the
pre-validation deduplication step.

**Pandera gate**: `SilverSchema.validate(df)` MUST pass before the Parquet file is written.
Any pandera `SchemaError` is logged as ERROR and halts the current run.

---

## 4. Gold Layer Contract

**File naming**: `PolymerPricingGold_yyyyMMdd.parquet`
**Location**: `data/gold/CodePolymer_Pricing/`
**Format**: Apache Parquet (typed, snappy-compressed)
**Written by**: `02_TransformData` (after pandera `GoldSchema` validation)
**Read by**: `03_LoadToWarehouse`

| Column | pandas dtype | Nullable | Notes |
|--------|-------------|----------|-------|
| `material_code` | `object` | No | Unchanged from silver |
| `pricing_date` | `datetime64[ns]` | No | Unchanged from silver |
| `price_value` | `float64` | No | Unchanged from silver |
| `unit_of_measure` | `object` | No | Unchanged from silver |
| `currency_code` | `object` | No | Unchanged from silver |
| `source_file_name` | `object` | No | Unchanged from silver |
| `ingestion_timestamp` | `datetime64[ns]` | No | Unchanged from silver |
| `loaded_at` | `datetime64[ns]` | No | UTC timestamp when gold file is written; added by `02_TransformData` |

**Uniqueness guarantee**: Exactly one row per (`material_code`, `pricing_date`).

**Pandera gate**: `GoldSchema.validate(df)` MUST pass before the Parquet file is written.

---

## 5. SQL Target Contract

**Target table**: `Reporting.PolymerPricingFact`
**Reference table**: `dbo.MaterialDim`
**Full DDL**: see [sql-ddl.sql](sql-ddl.sql)

**Load operation**: `03_LoadToWarehouse` executes the following sequence within a single
database transaction:
1. Upsert `material_code` values into `dbo.MaterialDim` (INSERT if not exists).
2. Resolve `MaterialKey` for each gold row via join on `material_code`.
3. Write resolved DataFrame to session-scoped temp table `#StagingPolymerPricing`.
4. Execute T-SQL `MERGE` from `#StagingPolymerPricing` into `Reporting.PolymerPricingFact`
   on key `(MaterialKey, pricing_date)`.

**Upsert key**: `(MaterialKey, pricing_date)` — matches the unique constraint
`UQ_PolymerPricingFact_MaterialDate` in the DDL.

---

## 6. Environment Variable Contract

All variables MUST be set before any pipeline script starts. A missing or empty variable causes
the script to raise a `KeyError` / `ValueError`, log a structured ERROR entry, and exit with a
non-zero return code before reading any data.

| Variable | Purpose | Example |
|----------|---------|---------|
| `SQL_SERVER` | Azure SQL Server FQDN | `myserver.database.windows.net` |
| `SQL_DATABASE` | Target database name | `PolymerReporting` |
| `SQL_USERNAME` | SQL login username | `svc_pipeline` |
| `SQL_PASSWORD` | SQL login password | *(secret — never log or print)* |
| `LANDING_DIR` | Absolute path to landing zone folder | `C:\data\landing` |
| `BRONZE_DIR` | Absolute path to bronze root | `C:\data\bronze` |
| `SILVER_DIR` | Absolute path to silver root | `C:\data\silver` |
| `GOLD_DIR` | Absolute path to gold root | `C:\data\gold` |
| `LOG_DIR` | Absolute path to log output folder | `C:\logs` |

A `.env.example` file at repository root documents all variables with placeholder values.
The actual `.env` file MUST be listed in `.gitignore` (Constitution I).

---

## 7. Script Interface Summary

| Script | Reads from | Writes to | Key gate |
|--------|-----------|-----------|----------|
| `01_IngestData.py` | `LANDING_DIR/PolymerPricing_yyyyMMdd.csv` | Bronze CSV, Silver Parquet | `SilverSchema.validate()` |
| `02_TransformData.py` | Silver Parquet | Gold Parquet | `GoldSchema.validate()` |
| `03_LoadToWarehouse.py` | Gold Parquet | `MaterialDim`, `PolymerPricingFact` (via MERGE) | SQL FK constraint + UNIQUE constraint |
