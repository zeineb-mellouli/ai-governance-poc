# Feature Specification: Polymer Pricing ETL Pipeline

**Feature Branch**: `001-polymer-pricing-etl`

**Created**: 2026-07-13

**Status**: Draft

**Input**: User description: "Build a Polymer Pricing ETL pipeline for the Finance team. The pipeline ingests daily polymer pricing CSV files into a bronze layer, validates and cleanses them into a silver layer using pandera, transforms to a gold layer with one row per material per pricing date, and loads the gold data into Azure SQL Server (Reporting.PolymerPricingFact). Must follow the medallion architecture constitution. No PII in the data. Credentials from environment variables only."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Daily Bronze Ingestion (Priority: P1)

A Finance team data engineer triggers the pipeline each morning after the daily polymer pricing
CSV file arrives in the landing zone. The pipeline reads the CSV and deposits it — completely
untransformed — into the bronze layer so that the raw source data is permanently preserved for
audit and reprocessing purposes.

**Why this priority**: Bronze ingestion is the mandatory entry point for all downstream processing.
Without immutable raw storage, no silver or gold layer can be produced. This is the foundational
MVP: even bronze-only delivery has value for audit/compliance purposes.

**Independent Test**: Run the pipeline with a sample CSV; confirm that a bronze layer store is
created containing the exact input rows with no modifications, that the source file is unchanged,
and that a structured log entry records the run start, end, and row count.

**Acceptance Scenarios**:

1. **Given** a valid polymer pricing CSV exists in the landing zone, **When** the ingestion
   pipeline runs, **Then** all rows are written unchanged to the bronze layer with ingestion
   timestamp and source file name recorded as metadata alongside each batch.
2. **Given** bronze data has already been ingested for a specific source file, **When** the
   pipeline runs again with the same file, **Then** no bronze records are overwritten; the run
   logs a warning and exits without error.
3. **Given** the CSV file contains zero data rows (empty file), **When** the pipeline runs,
   **Then** no bronze records are written and the run completes with a warning log entry.
4. **Given** the CSV file is malformed (missing mandatory headers or encoding error), **When** the
   pipeline runs, **Then** the run fails at the bronze stage with a structured error log entry and
   no partial data is written to any layer.

---

### User Story 2 - Silver Validation and Cleansing (Priority: P2)

Once new bronze data is available, a Finance data engineer runs the silver processing step. The
pipeline validates and cleanses the bronze data — enforcing nulls, deduplication, and price-range
rules — and produces a validated silver dataset alongside a logged quality report.

**Why this priority**: The silver layer is the trust boundary for the pipeline. All downstream
gold and reporting consumers depend on validated data. Silver processing must be independently
runnable against any bronze batch for re-processing or audit purposes.

**Independent Test**: Run the silver transformation step against a bronze dataset containing
intentionally dirty rows (nulls, duplicates, out-of-range prices); confirm that the silver layer
excludes those rows, that the rejection count and reasons are logged, and that all retained rows
pass every validation rule.

**Acceptance Scenarios**:

1. **Given** a bronze layer with complete and valid records, **When** the silver transformation
   runs, **Then** all records pass validation and are written to the silver layer with zero rows
   dropped.
2. **Given** bronze data containing rows with null values in mandatory fields (material code,
   pricing date, or price value), **When** the silver transformation runs, **Then** those rows are
   excluded from silver and their count and reason are written to the log.
3. **Given** bronze data containing duplicate records sharing the same material code and pricing
   date, **When** the silver transformation runs, **Then** only one record per material-date
   combination is retained in silver and the duplicate count is logged.
4. **Given** bronze data containing a price value outside the declared acceptable positive range,
   **When** the silver transformation runs, **Then** that row is excluded from silver and the
   rejection is logged with the offending value.
5. **Given** all bronze records for a batch fail validation, **When** the silver transformation
   runs, **Then** zero rows are written to silver; the run completes with a warning log (not an
   error) and gold processing is skipped for that batch.

---

### User Story 3 - Gold Aggregation and Reporting Load (Priority: P3)

Finance reporting analysts query the `Reporting.PolymerPricingFact` table to produce pricing
dashboards and variance reports. The gold pipeline ensures that this table always contains exactly
one authoritative price record per material per calendar day, refreshed by each daily run without
accumulating duplicates.

**Why this priority**: This is the consumer-facing deliverable. Analysts require correct,
deduplicated data in the reporting system. This story completes the end-to-end pipeline value and
is the primary business outcome the Finance team can measure.

**Independent Test**: Run the full pipeline end-to-end with a known silver dataset; query
`Reporting.PolymerPricingFact` and confirm exactly one row per material per pricing date with
values matching expectations; re-run the pipeline and confirm row counts are unchanged.

**Acceptance Scenarios**:

1. **Given** a clean silver layer, **When** the gold transformation runs, **Then** exactly one
   record per material code per pricing date is produced and loaded into
   `Reporting.PolymerPricingFact`.
2. **Given** a pricing record for a material-date combination already exists in the reporting
   table from a prior run, **When** an updated file for the same date is processed, **Then** the
   existing record is updated (upserted), not duplicated.
3. **Given** a database connectivity failure during the gold load step, **When** the pipeline
   encounters the error, **Then** the run fails with a structured error log entry; bronze and
   silver data remain intact and the pipeline is idempotent on retry.
4. **Given** the gold pipeline completes successfully, **When** the run ends, **Then** the log
   records the total records loaded, the target table, and the run completion timestamp.

---

### Edge Cases

- What happens when the environment variable for the database connection string is absent or
  empty? The pipeline fails at startup with a clear error log entry before reading any data.
- What happens when the landing zone contains no new file for today's run? The pipeline logs a
  warning and exits cleanly without writing to any layer.
- What happens when all bronze records for a batch are duplicates? Silver receives zero rows after
  deduplication; the run completes with a warning; gold processing is skipped for that batch.
- What happens when a partial run fails mid-pipeline (bronze written, silver fails)? Bronze data
  remains intact; silver and gold are not written; the pipeline can be safely retried from the
  silver step without re-ingesting bronze.
- What happens when the source CSV column names deviate from the expected schema? The validation
  step fails at silver with a structured schema-mismatch error log entry.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The pipeline MUST ingest daily polymer pricing CSV files into the bronze layer
  without any transformation, preserving all source rows exactly as received.
- **FR-002**: The pipeline MUST record the source file name and ingestion timestamp as batch
  metadata alongside every bronze write; these metadata fields MUST NOT alter the source file.
- **FR-003**: Bronze layer data MUST NEVER be overwritten or deleted by any transform code; the
  bronze layer is immutable once written (Constitution III).
- **FR-004**: The pipeline MUST validate bronze data using a **pandera** schema before writing to
  the silver layer (Constitution II). The schema MUST enforce:
  - No null values in mandatory fields: `material_code`, `pricing_date`, `price_value`,
    `unit_of_measure`, `currency_code`.
  - No duplicate records on the composite business key: `material_code` + `pricing_date`.
  - All `price_value` fields within the declared acceptable positive numeric range.
- **FR-005**: Records failing silver validation MUST be excluded from the silver layer; their
  count and rejection reason MUST be written to the pipeline log file.
- **FR-006**: The silver-to-gold transformation MUST produce exactly one record per
  `material_code` per `pricing_date`.
- **FR-007**: The pipeline MUST load gold records into `Reporting.PolymerPricingFact` using an
  upsert keyed on (`material_code`, `pricing_date`), ensuring no duplicate rows accumulate across
  multiple pipeline runs.
- **FR-008**: All database connection strings and credentials MUST be read exclusively from
  environment variables (Constitution I); no credential value may appear in source code,
  configuration files committed to version control, or log output.
- **FR-009**: The pipeline MUST write all operational messages to a structured log file using
  file-based logging (Constitution IV). Mandatory log entries per run: run start (with source
  file name and run date), record counts at each layer boundary, validation rejection counts, and
  run end or error. No operational messages may be emitted via standard output.
- **FR-010**: No PII (names, email addresses, phone numbers, or any personal identifier) may
  appear in any layer output, log entry, or database record at any pipeline stage (Constitution V).
- **FR-011**: The pipeline MUST be idempotent: re-running the pipeline for the same source file
  MUST produce the same data state in all layers and in the reporting database without increasing
  record counts.

### Key Entities

- **PolymerPricingRecord**: A single daily price entry for a polymer material.
  - Mandatory attributes: `material_code`, `pricing_date`, `price_value`, `unit_of_measure`,
    `currency_code`.
  - Metadata attributes (bronze only): `source_file_name`, `ingestion_timestamp`.
  - No PII attributes permitted.
- **Material**: A distinct polymer product identified by `material_code`. Contains no personal
  data.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Finance analysts can access current polymer pricing data in the reporting table
  within 24 hours of the source CSV file being deposited in the landing zone.
- **SC-002**: Zero records with null mandatory fields, out-of-range prices, or duplicate
  material-date keys ever reach the silver or gold layers.
- **SC-003**: `Reporting.PolymerPricingFact` contains exactly one record per material per
  calendar day at all times, regardless of how many times the pipeline has been run for that day.
- **SC-004**: A failed pipeline run produces a log file entry identifying the failure stage,
  root cause, and affected record count within the same run execution — no secondary investigation
  required to determine what failed.
- **SC-005**: Credential rotation requires zero code changes; only environment variable values
  need to be updated.
- **SC-006**: Re-running the pipeline for a date already processed produces the same final data
  state, with no net increase in record counts in any layer or in the reporting table.

---

## Assumptions

- Source CSV files are delivered to a designated landing folder daily and named following the
  project CamelCase date-suffix convention (e.g., `PolymerPricing_20260713.csv`) per Constitution
  Principle VI.
- Source CSV files contain no PII fields; all data is pricing and material reference data only.
- The `Reporting.PolymerPricingFact` table in Azure SQL Server is provisioned and accessible
  before the first pipeline run; this pipeline handles data load only, not DDL (table creation or
  schema migration).
- The acceptable `price_value` range (minimum and maximum bounds) is a positive numeric range for
  commodity polymer pricing; exact bounds will be confirmed and encoded in the pandera schema
  during planning.
- The pipeline runs in a scheduled daily batch context, not as a real-time or event-driven
  streaming service.
- All required environment variable names (database credentials, landing zone path, log directory)
  will be documented in the implementation plan and in a `.env.example` file committed to the
  repository.
- The deduplication business key for the gold layer is the composite of `material_code` +
  `pricing_date`.
- Dependencies will be pinned to exact versions in `requirements.txt` per Constitution
  Principle VII.
