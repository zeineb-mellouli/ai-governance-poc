# Implementation Plan: Polymer Pricing ETL Pipeline

**Branch**: `001-polymer-pricing-etl` | **Date**: 2026-07-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-polymer-pricing-etl/spec.md`

## Summary

Three-stage daily batch ETL pipeline for the Finance team. `01_IngestData` reads source polymer
pricing CSV files, writes an immutable bronze copy, validates and cleanses to silver via pandera.
`02_TransformData` aggregates silver to exactly one record per material per pricing date in gold.
`03_LoadToWarehouse` upserts gold records into `Reporting.PolymerPricingFact` in Azure SQL Server
via a MERGE statement. All credentials from `os.environ`. File-based Python logging throughout.
Azure Pipelines CI/CD on `master`/`develop` with 1-reviewer PR policy.

## Technical Context

**Language/Version**: Python 3.11

**Primary Dependencies**: pandas 2.2.3, pandera 0.20.4, sqlalchemy 2.0.36, pyodbc 5.1.0,
pyarrow 16.1.0 (Parquet support), python-dotenv 1.0.1, pytest 8.3.3

**Storage**:
- Local filesystem: `data/bronze/` (CSV), `data/silver/` (Parquet), `data/gold/` (Parquet)
- Azure SQL Server: `Reporting.PolymerPricingFact` (gold target), `dbo.MaterialDim` (reference)

**Testing**: pytest 8.3.3

**Target Platform**: Windows/Linux server; Azure Pipelines for CI/CD

**Project Type**: Batch data pipeline (ETL)

**Performance Goals**: Process a daily polymer pricing CSV (≤ 10,000 rows) end-to-end in
under 5 minutes

**Constraints**:
- No PII anywhere in the pipeline (Constitution V)
- All credentials exclusively from `os.environ` (Constitution I)
- Bronze layer immutable — transform code must never overwrite (Constitution III)
- Pandera validation mandatory before every layer write (Constitution II)
- Python `logging` with `FileHandler` only — no `print()` for operational output (Constitution IV)
- All dependencies pinned to exact versions in `requirements.txt` (Constitution VII)
- No stochastic operations → `np.random.seed()` not required

**Scale/Scope**: Single source CSV per day, one Fact + one Dim SQL target, three pipeline
stages, Finance data engineering team (small)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase-0 Check

| # | Principle | Status | Evidence |
|---|-----------|--------|----------|
| I | Security First | ✅ PASS | Credentials read from `os.environ` in all scripts; `.env.example` committed (not `.env`); no secrets in any committed file |
| II | Data Quality Gate | ✅ PASS | Pandera validation in `01_IngestData` (before silver write) and `02_TransformData` (before gold write) |
| III | Medallion Architecture | ✅ PASS | Bronze never overwritten; separate scripts per layer; silver only from bronze; gold only from silver; no layer skipping |
| IV | Observability | ✅ PASS | Shared `logging_config.py` with `FileHandler`; START/END/record-count/ERROR entries in all three scripts |
| V | Privacy by Default | ✅ PASS | Source data is commodity pricing only — no PII fields exist; confirmed in spec Assumptions |
| VI | File Naming | ✅ PASS | Data files: `PolymerPricing_yyyyMMdd.csv` / `PolymerPricingBronze_yyyyMMdd.csv` etc.; folders: `CodePolymer_Pricing`; CSV columns: snake_case |
| VII | Reproducibility | ✅ PASS | All deps pinned in `requirements.txt`; no stochastic operations |
| VIII | Git Workflow | ✅ PASS | `azure-pipelines.yml` triggers on `master`/`develop`; PR reviewer policy documented (Azure DevOps portal) |
| IX | SQL Naming | ✅ PASS | `PolymerPricingFact`, `MaterialDim` (PascalCase + Fact/Dim suffix); `PricingKey`, `MaterialKey` (Key suffix for PK/FK); no type prefixes |
| X | Repository Naming | ⚠️ NOTE | Pre-existing repo name `code-polymer` lacks dept prefix (constitution pattern: `fin-code-polymer_pricing`). Non-blocking; requires coordinated repo rename outside this feature's scope. |

**Pre-Phase-0 Gate**: ✅ PASS (one noted pre-existing deviation on Principle X; non-blocking).

### Post-Phase-1 Re-check

| # | Principle | Status | Design Evidence |
|---|-----------|--------|-----------------|
| I | Security First | ✅ PASS | Connection factory pattern in `research.md` §2 uses `os.environ` exclusively; no secrets in DDL or contracts |
| II | Data Quality Gate | ✅ PASS | `BronzeSchema`, `SilverSchema`, `GoldSchema` defined in `data-model.md`; validation gates in `contracts/pipeline-contracts.md` |
| III | Medallion Architecture | ✅ PASS | Bronze CSV → Silver Parquet → Gold Parquet → SQL; three separate scripts; immutability enforced by file-path conventions |
| IV | Observability | ✅ PASS | `logging_config.py` centralises `FileHandler` setup; all scripts import it; quickstart confirms log output requirement |
| V | Privacy by Default | ✅ PASS | No PII columns in any layer schema (`data-model.md`); SQL DDL contains no PII-capable columns |
| VI | File Naming | ✅ PASS | All file names confirmed in `contracts/pipeline-contracts.md`; folder `CodePolymer_Pricing` in all layer paths; snake_case column names throughout |
| VII | Reproducibility | ✅ PASS | `requirements.txt` will pin all 7 dependencies; no stochastic steps in any script |
| VIII | Git Workflow | ✅ PASS | `azure-pipelines.yml` branch triggers and PR build-validation gate; min-1-reviewer documented in README |
| IX | SQL Naming | ✅ PASS | DDL in `contracts/sql-ddl.sql` confirms all naming rules |
| X | Repository Naming | ⚠️ NOTE | Same pre-existing deviation; unchanged |

**Post-Phase-1 Gate**: ✅ PASS (same deviation noted; non-blocking).

## Project Structure

### Documentation (this feature)

```text
specs/001-polymer-pricing-etl/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── pipeline-contracts.md   # Layer data schemas + env var contract
│   └── sql-ddl.sql             # DDL for MaterialDim and PolymerPricingFact
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
pipeline/
├── 01_IngestData.py            # Bronze ingestion + Silver validation (pandera)
├── 02_TransformData.py         # Silver → Gold aggregation
├── 03_LoadToWarehouse.py       # Gold → Reporting.PolymerPricingFact upsert
├── schemas/
│   └── pricing_schema.py       # BronzeSchema, SilverSchema, GoldSchema (pandera SchemaModel)
└── utils/
    └── logging_config.py       # Shared FileHandler logging factory

sql/
├── CreatePolymerPricingFact.sql    # DDL: Reporting.PolymerPricingFact
└── CreateMaterialDim.sql           # DDL: dbo.MaterialDim

data/
├── landing/                        # Source CSV drop location (gitignored)
├── bronze/
│   └── CodePolymer_Pricing/        # Immutable raw CSV copies
├── silver/
│   └── CodePolymer_Pricing/        # Validated Parquet files
└── gold/
    └── CodePolymer_Pricing/        # Aggregated Parquet files

logs/                               # Pipeline log files (gitignored)

tests/
├── unit/                           # Schema validation, transform logic
└── integration/                    # End-to-end pipeline + DB round-trip

azure-pipelines.yml
requirements.txt
.env.example
README.md
```

**Structure Decision**: Single-project layout. Pipeline scripts are numbered for execution order
per user specification. Layer data folders follow `CodePolymer_Pricing` naming (Constitution VI).
No web, API, or mobile components. Schemas and utilities extracted to sub-modules to keep
pipeline scripts focused on orchestration logic only.

## Complexity Tracking

No constitution violations requiring justification. The one noted deviation (Principle X repo
name) is a pre-existing constraint that predates this feature and requires no complexity
trade-off within this implementation.
