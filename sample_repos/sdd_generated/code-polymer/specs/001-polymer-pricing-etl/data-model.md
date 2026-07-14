# Data Model: Polymer Pricing ETL Pipeline

**Branch**: `001-polymer-pricing-etl` | **Phase 1** | **Date**: 2026-07-13

---

## Medallion Layer Schemas

### Bronze Layer — `PolymerPricingRecord` (raw)

**File**: `data/bronze/CodePolymer_Pricing/PolymerPricingBronze_yyyyMMdd.csv`
**Format**: CSV (exact copy of source + appended metadata columns)
**Pandera class**: `BronzeSchema`

| Column | pandas dtype | Nullable | Constraints | Source |
|--------|-------------|----------|-------------|--------|
| `material_code` | `object` (str) | No | Not empty string | Source CSV |
| `pricing_date` | `object` (str) | No | Parseable as date | Source CSV |
| `price_value` | `float64` | No | Numeric (raw; no range check at bronze) | Source CSV |
| `unit_of_measure` | `object` (str) | No | Not empty string | Source CSV |
| `currency_code` | `object` (str) | No | Not empty string | Source CSV |
| `source_file_name` | `object` (str) | No | Not empty string | Added by `01_IngestData` |
| `ingestion_timestamp` | `object` (str) | No | ISO 8601 datetime | Added by `01_IngestData` |

**Validation rules**: Bronze schema validates column presence and nullability only. No range or
format rules — bronze preserves raw source data with maximum fidelity. Any row that cannot be
parsed from the source CSV fails the entire bronze write (malformed-file edge case).

**Immutability rule**: Once written, no script may overwrite or delete files in
`data/bronze/CodePolymer_Pricing/`. A file for a given date already present causes the bronze
step to log a warning and skip re-ingest (idempotency, FR-011).

---

### Silver Layer — `PolymerPricingRecord` (validated)

**File**: `data/silver/CodePolymer_Pricing/PolymerPricingSilver_yyyyMMdd.parquet`
**Format**: Apache Parquet (typed)
**Pandera class**: `SilverSchema`

| Column | pandas dtype | Nullable | Validation Rules |
|--------|-------------|----------|-----------------|
| `material_code` | `object` (str) | No | Not null; not empty string |
| `pricing_date` | `datetime64[ns]` | No | Not null; valid date; not in future |
| `price_value` | `float64` | No | Not null; `> 0.0`; `< 100_000.0` |
| `unit_of_measure` | `object` (str) | No | Not null; not empty string |
| `currency_code` | `object` (str) | No | Not null; exactly 3 uppercase alphabetic chars |
| `source_file_name` | `object` (str) | No | Not null; not empty string |
| `ingestion_timestamp` | `datetime64[ns]` | No | Not null |

**Deduplication**: Before pandera validation, deduplicate on composite key
(`material_code`, `pricing_date`). Keep first occurrence per key. Log count of dropped
duplicates at INFO level.

**Rejection handling**: Rows failing pandera validation are excluded from the silver output.
Total rejection count and a summary of failed checks are logged at WARNING level. The silver
file is only written if at least one valid row remains; otherwise the step logs a WARNING and
skips the write (no error, downstream gold step is also skipped).

---

### Gold Layer — `PolymerPricingRecord` (aggregated)

**File**: `data/gold/CodePolymer_Pricing/PolymerPricingGold_yyyyMMdd.parquet`
**Format**: Apache Parquet (typed)
**Pandera class**: `GoldSchema`

| Column | pandas dtype | Nullable | Notes |
|--------|-------------|----------|-------|
| `material_code` | `object` (str) | No | Unchanged from silver |
| `pricing_date` | `datetime64[ns]` | No | Unchanged from silver |
| `price_value` | `float64` | No | Unchanged from silver |
| `unit_of_measure` | `object` (str) | No | Unchanged from silver |
| `currency_code` | `object` (str) | No | Unchanged from silver |
| `source_file_name` | `object` (str) | No | Unchanged from silver |
| `ingestion_timestamp` | `datetime64[ns]` | No | Unchanged from silver |
| `loaded_at` | `datetime64[ns]` | No | Timestamp when gold file is written; added by `02_TransformData` |

**Aggregation guarantee**: `GoldSchema` enforces a uniqueness check on (`material_code`,
`pricing_date`) — if silver was correctly validated, this is always satisfied. The pandera
check acts as a defensive gate.

**Relationship to silver**: Gold is a projection of silver with `loaded_at` appended. The
silver-to-gold step is a passthrough aggregation (silver already provides 1-row-per-key after
deduplication). This step exists as a distinct contract layer to support future gold-level
enrichment (e.g., currency conversion, material hierarchy joins) without changing silver.

---

## SQL Data Model

### `dbo.MaterialDim`

Reference table for polymer material master data.

| Column | SQL Type | Nullable | Constraints | Notes |
|--------|----------|----------|-------------|-------|
| `MaterialKey` | `INT IDENTITY(1,1)` | No | `PRIMARY KEY` | Surrogate key (Constitution IX: Key suffix) |
| `material_code` | `VARCHAR(50)` | No | `UNIQUE NOT NULL` | Business key from source CSV |
| `material_description` | `VARCHAR(255)` | Yes | — | Optional; populated via manual lookup or future source |
| `created_date` | `DATETIME2` | No | `DEFAULT GETDATE()` | Audit timestamp |

**Population strategy**: `03_LoadToWarehouse` performs an upsert into `MaterialDim` for any
`material_code` values in the gold DataFrame that do not yet exist, before loading
`PolymerPricingFact`. This ensures referential integrity without requiring manual master data
management for the initial implementation.

---

### `Reporting.PolymerPricingFact`

Daily polymer pricing fact table. Gold-layer target.

| Column | SQL Type | Nullable | Constraints | Notes |
|--------|----------|----------|-------------|-------|
| `PricingKey` | `INT IDENTITY(1,1)` | No | `PRIMARY KEY` | Surrogate key |
| `MaterialKey` | `INT` | No | `FOREIGN KEY → dbo.MaterialDim(MaterialKey)` | Resolved from `material_code` during load |
| `pricing_date` | `DATE` | No | `NOT NULL` | |
| `price_value` | `DECIMAL(18, 6)` | No | `NOT NULL` | 6 decimal places; covers micro-pricing precision |
| `unit_of_measure` | `VARCHAR(20)` | No | `NOT NULL` | E.g. `MT`, `KG`, `LB` |
| `currency_code` | `CHAR(3)` | No | `NOT NULL` | ISO 4217 (e.g. `USD`, `EUR`) |
| `source_file_name` | `VARCHAR(255)` | No | `NOT NULL` | Lineage traceability |
| `ingestion_timestamp` | `DATETIME2` | No | `NOT NULL` | From bronze metadata |
| `loaded_at` | `DATETIME2` | No | `DEFAULT GETDATE()` | Set by MERGE statement |
| *(unique constraint)* | — | — | `UNIQUE (MaterialKey, pricing_date)` | Enforces 1-row-per-material-per-date; enables upsert |

---

## Validation Rules Summary

| Rule | Layer | Enforcement |
|------|-------|-------------|
| Column presence (all 5 source columns) | Bronze | `BronzeSchema` |
| No null in mandatory fields | Silver | `SilverSchema` |
| Deduplication on (`material_code`, `pricing_date`) | Silver (pre-pandera step) | pandas `.drop_duplicates()` → logged |
| `price_value > 0` and `< 100,000` | Silver | `SilverSchema` |
| `currency_code` exactly 3 uppercase chars | Silver | `SilverSchema` regex check |
| `pricing_date` not in future | Silver | `SilverSchema` custom check |
| Uniqueness on (`material_code`, `pricing_date`) | Gold | `GoldSchema` (defensive) |
| Referential integrity (`MaterialKey` → `MaterialDim`) | SQL | `FK_PolymerPricingFact_MaterialKey` constraint |
| No duplicate rows in fact table | SQL | `UQ_PolymerPricingFact_MaterialDate` constraint + MERGE |

---

## State Transitions

```
Source CSV (landing/)
    |
    | [01_IngestData] Read CSV → append metadata
    ▼
Bronze CSV  (data/bronze/CodePolymer_Pricing/PolymerPricingBronze_yyyyMMdd.csv)
    |                  [IMMUTABLE — never overwritten]
    | [01_IngestData] Deduplicate → BronzeSchema validate → SilverSchema validate
    ▼
Silver Parquet  (data/silver/CodePolymer_Pricing/PolymerPricingSilver_yyyyMMdd.parquet)
    |
    | [02_TransformData] Append loaded_at → GoldSchema validate
    ▼
Gold Parquet  (data/gold/CodePolymer_Pricing/PolymerPricingGold_yyyyMMdd.parquet)
    |
    | [03_LoadToWarehouse] Upsert MaterialDim → T-SQL MERGE
    ▼
Reporting.PolymerPricingFact  (Azure SQL Server)
```
