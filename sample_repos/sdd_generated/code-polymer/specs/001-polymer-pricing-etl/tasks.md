---
description: "Task list for Polymer Pricing ETL Pipeline implementation"
---

# Tasks: Polymer Pricing ETL Pipeline

**Input**: Design documents from `specs/001-polymer-pricing-etl/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅ | quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story this task belongs to — [US1], [US2], [US3]
- Exact file paths included in every task description

## Path Conventions

- Pipeline scripts: `pipeline/`
- Schemas module: `pipeline/schemas/`
- Utilities module: `pipeline/utils/`
- SQL DDL source: `sql/`
- Bronze layer: `data/bronze/CodePolymer_Pricing/`
- Silver layer: `data/silver/CodePolymer_Pricing/`
- Gold layer: `data/gold/CodePolymer_Pricing/`
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`

---

## Phase 1: Setup (Project Initialization)

**Purpose**: Create directory skeleton, CI/CD scaffold, and repo configuration files.
No pipeline logic yet — all tasks are independent and can run in parallel after T001.

- [X] T001 Create directory skeleton at repository root: `pipeline/`, `pipeline/schemas/`, `pipeline/utils/`, `sql/`, `data/landing/`, `data/bronze/CodePolymer_Pricing/`, `data/silver/CodePolymer_Pricing/`, `data/gold/CodePolymer_Pricing/`, `logs/`, `tests/unit/`, `tests/integration/`; add `.gitkeep` to each empty folder so Git tracks them

- [X] T002 [P] Create `requirements.txt` with exact pinned versions per Constitution VII — `pandas==2.2.3`, `pandera==0.20.4`, `sqlalchemy==2.0.36`, `pyodbc==5.1.0`, `pyarrow==16.1.0`, `python-dotenv==1.0.1`, `pytest==8.3.3`; no range specifiers (`>=`, `~=`) permitted

- [X] T003 [P] Create `.env.example` with stub values for all 9 required environment variables from `contracts/pipeline-contracts.md §6`: `SQL_SERVER`, `SQL_DATABASE`, `SQL_USERNAME`, `SQL_PASSWORD=<secret-never-commit>`, `LANDING_DIR`, `BRONZE_DIR`, `SILVER_DIR`, `GOLD_DIR`, `LOG_DIR`; add a comment block explaining each variable

- [X] T004 [P] Create `.gitignore` excluding: `data/landing/*`, `data/bronze/*`, `data/silver/*`, `data/gold/*`, `logs/*`, `.env`, `**/__pycache__/`, `**/*.pyc`, `**/*.parquet`; add negation rules `!data/**/.gitkeep` and `!logs/.gitkeep` to preserve tracked empty folders

- [X] T005 [P] Create `azure-pipelines.yml` — single `CI` job triggered on branches `master` and `develop`; steps: (1) `pip install -r requirements.txt`, (2) `flake8 pipeline/ tests/ --max-line-length=120`, (3) `pytest tests/unit/ -v`; integration tests excluded from CI (require live DB); annotate with a comment referencing the Constitution VIII PR reviewer policy that must be configured in Azure DevOps portal

- [X] T006 [P] Create `README.md` — sections: project overview, medallion architecture layers (bronze → silver → gold → SQL), required environment variables (reference `.env.example`), pipeline execution steps (`python pipeline/01_IngestData.py --date YYYYMMDD` → `02_TransformData` → `03_LoadToWarehouse`), Azure DevOps branch policy setup (enable "Require a minimum number of reviewers: 1" on `master` and `develop`), Constitution Principle X note on repo naming

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that every pipeline script and every test depends on.
All tasks in this phase are in different files and can run fully in parallel.

⚠️ **CRITICAL**: No user story work can begin until T007–T011 are complete.

- [X] T007 [P] Create `sql/CreateMaterialDim.sql` — idempotent DDL for `dbo.MaterialDim`: `IF NOT EXISTS` guard; columns: `MaterialKey INT IDENTITY(1,1) NOT NULL`, `material_code VARCHAR(50) NOT NULL`, `material_description VARCHAR(255) NULL`, `created_date DATETIME2 NOT NULL DEFAULT GETDATE()`; constraints: `PK_MaterialDim PRIMARY KEY (MaterialKey)`, `UQ_MaterialDim_MaterialCode UNIQUE (material_code)`; apply Constitution IX naming rules (PascalCase, Key suffix for PK, no type prefixes)

- [X] T008 [P] Create `sql/CreatePolymerPricingFact.sql` — idempotent DDL for `Reporting.PolymerPricingFact`: `IF NOT EXISTS` guard for `Reporting` schema; `IF NOT EXISTS` guard for table; columns: `PricingKey INT IDENTITY(1,1) NOT NULL`, `MaterialKey INT NOT NULL`, `pricing_date DATE NOT NULL`, `price_value DECIMAL(18,6) NOT NULL`, `unit_of_measure VARCHAR(20) NOT NULL`, `currency_code CHAR(3) NOT NULL`, `source_file_name VARCHAR(255) NOT NULL`, `ingestion_timestamp DATETIME2 NOT NULL`, `loaded_at DATETIME2 NOT NULL DEFAULT GETDATE()`; constraints: `PK_PolymerPricingFact`, `FK_PolymerPricingFact_MaterialKey REFERENCES dbo.MaterialDim(MaterialKey)`, `UQ_PolymerPricingFact_MaterialDate UNIQUE (MaterialKey, pricing_date)`; include MERGE template as a commented reference block (from `contracts/sql-ddl.sql`)

- [X] T009 [P] Create `pipeline/utils/logging_config.py` — single public function `get_logger(name: str, log_dir: str) -> logging.Logger`: creates `log_dir` if it does not exist; attaches one `logging.FileHandler` writing to `{log_dir}/PipelineRun_{yyyyMMdd}.log` at `INFO` level with format `%(asctime)s | %(name)s | %(levelname)s | %(message)s`; no `StreamHandler` (Constitution IV: file-based logging only; no console output); returns configured logger

- [X] T010 [P] Create `pipeline/schemas/pricing_schema.py` — three `pandera.DataFrameModel` subclasses per `data-model.md` validation rules:
  - `BronzeSchema`: fields `material_code: Series[str]`, `pricing_date: Series[str]`, `price_value: Series[float]`, `unit_of_measure: Series[str]`, `currency_code: Series[str]`, `source_file_name: Series[str]`, `ingestion_timestamp: Series[str]`; all `nullable=False`
  - `SilverSchema`: fields `material_code: Series[str]` (not empty string), `pricing_date: Series[pd.Timestamp]`, `price_value: Series[float]` (annotated with `pa.Field(gt=0.0, lt=100_000.0)`), `unit_of_measure: Series[str]`, `currency_code: Series[str]` (annotated with `pa.Field(str_matches=r"^[A-Z]{3}$")`), `source_file_name: Series[str]`, `ingestion_timestamp: Series[pd.Timestamp]`; all `nullable=False`; add `@pa.dataframe_check` for `pricing_date` not in future
  - `GoldSchema(SilverSchema)`: inherits SilverSchema; adds `loaded_at: Series[pd.Timestamp]` (`nullable=False`); adds `class Config: unique = ["material_code", "pricing_date"]`

- [X] T011 [P] Create `tests/conftest.py` — shared pytest fixtures: `sample_landing_csv(tmp_path)` fixture that writes a 5-row happy-path CSV (`PE-HD-001`, `PP-HOM-002`, `PET-BG-003`, `PVC-SUS-004`, `PA-6-005` each priced `2026-07-13`) to `tmp_path/PolymerPricing_20260713.csv` and returns the path; `sample_bronze_df()` fixture returning a 5-row DataFrame with all 7 bronze columns including `source_file_name` and `ingestion_timestamp`; `sample_silver_df()` fixture returning a 5-row DataFrame with all 7 silver columns with correct dtypes (`pricing_date` as `datetime64[ns]`, `ingestion_timestamp` as `datetime64[ns]`)

**Checkpoint**: T007–T011 complete → user story implementation can begin in parallel.

---

## Phase 3: User Story 1 — Daily Bronze Ingestion (Priority: P1) 🎯 MVP

**Goal**: Finance data engineer runs `pipeline/01_IngestData.py --date YYYYMMDD` and gets an
immutable bronze CSV at `data/bronze/CodePolymer_Pricing/PolymerPricingBronze_{date}.csv` with
`source_file_name` and `ingestion_timestamp` appended. Re-running the same date logs a WARNING
and does not overwrite.

**Independent test**: Place `PolymerPricing_20260713.csv` (Scenario 1 CSV from `quickstart.md`)
in `data/landing/`; run `python pipeline/01_IngestData.py --date 20260713`; assert
`PolymerPricingBronze_20260713.csv` exists with 5 rows and 7 columns; confirm log file contains
START and END entries; re-run and confirm WARNING is logged with no file change.

**Test criteria**:
- Bronze CSV present with all source rows + `source_file_name` + `ingestion_timestamp`
- Source CSV unchanged after ingestion
- Log shows `START` with source path, row count at bronze write, and `END`
- Re-run for same date: WARNING logged, bronze file unchanged, exit code 0

- [X] T012 [P] [US1] Create `tests/unit/test_schemas.py` — BronzeSchema unit tests: (a) `sample_bronze_df` fixture passes `BronzeSchema.validate()` without error; (b) a 5-column DataFrame missing `source_file_name` raises `pandera.errors.SchemaError`; (c) a row with `material_code=None` raises `SchemaError`; (d) a row with `price_value="not-a-number"` raises `SchemaError`

- [X] T013 [US1] Implement bronze ingestion in `pipeline/01_IngestData.py` — `argparse` `--date YYYYMMDD`; read `LANDING_DIR`, `BRONZE_DIR`, `SILVER_DIR`, `LOG_DIR` from `os.environ` — raise `EnvironmentError` + log `ERROR` on any missing variable; call `get_logger("IngestData", LOG_DIR)`; log `INFO "START date={date} source={path}"`; check if `BRONZE_DIR/CodePolymer_Pricing/PolymerPricingBronze_{date}.csv` already exists → log `WARNING "bronze already exists for {date}, skipping"` + `sys.exit(0)`; read CSV from `LANDING_DIR/PolymerPricing_{date}.csv` (UTF-8); handle `FileNotFoundError` → `ERROR` log + `sys.exit(1)`; handle zero-row file → `WARNING "empty source file for {date}"` + `sys.exit(0)`; append `source_file_name` (basename) and `ingestion_timestamp` (UTC ISO 8601 string) columns; validate with `BronzeSchema.validate(df)` → `ERROR` log + `sys.exit(1)` on `SchemaError`; write to `BRONZE_DIR/CodePolymer_Pricing/PolymerPricingBronze_{date}.csv` (UTF-8, no index); log `INFO "END bronze_rows={n}"`

---

## Phase 4: User Story 2 — Silver Validation and Cleansing (Priority: P2)

**Goal**: Immediately after writing bronze, `01_IngestData.py` continues into the silver step:
deduplicates on `(material_code, pricing_date)`, applies `SilverSchema` validation (dropping
invalid rows), and writes `PolymerPricingSilver_{date}.parquet` to
`data/silver/CodePolymer_Pricing/`. All rejections and dropped duplicates are logged at WARNING
with counts and reasons.

**Independent test**: Use Scenario 3 CSV from `quickstart.md` (5 rows: 1 null material_code,
1 price > 100,000, 1 duplicate); run `python pipeline/01_IngestData.py --date 20260714`; assert
silver Parquet has 2 rows; assert log shows 1 null rejection, 1 range rejection, 1 duplicate
dropped.

**Test criteria**:
- Silver Parquet contains only rows passing all `SilverSchema` rules
- Rejection count per rule logged at WARNING level
- Zero valid rows after cleaning → WARNING only, no error, no Parquet written
- `SilverSchema.validate()` on every written silver file raises no error

- [X] T014 [P] [US2] Add SilverSchema unit tests to `tests/unit/test_schemas.py` — assert row with `material_code=None` is excluded from silver; assert `price_value=150_000.0` raises `SchemaError`; assert `currency_code="US"` (2-char) raises `SchemaError`; assert two rows sharing same `(material_code, pricing_date)` are deduplicated to 1 via `drop_duplicates` before validation; assert `sample_silver_df` fixture passes `SilverSchema.validate()` without error

- [X] T015 [US2] Add silver validation step to `pipeline/01_IngestData.py` — after bronze write: (1) `df.drop_duplicates(subset=["material_code", "pricing_date"], keep="first", inplace=False)`; log `WARNING "dropped {n} duplicate rows"` if `n > 0`; (2) call `SilverSchema.validate(df, lazy=True)` to collect all failures; on `SchemaErrors` exception, extract `failure_cases`, drop invalid row indices, log `WARNING "excluded {n} rows: {summary}"`; (3) if `len(df) == 0`, log `WARNING "zero valid rows for {date}; skipping silver write"` + `sys.exit(0)`; (4) cast `pricing_date` to `datetime64[ns]` and `ingestion_timestamp` to `datetime64[ns]`; write to `SILVER_DIR/CodePolymer_Pricing/PolymerPricingSilver_{date}.parquet` (engine=`pyarrow`, compression=`snappy`, index=False); log `INFO "END silver_rows={n}"`

---

## Phase 5: User Story 3 — Gold Aggregation and Reporting Load (Priority: P3)

**Goal**: Finance reporting analysts query `Reporting.PolymerPricingFact` and see exactly one
record per material per pricing date; re-running the pipeline for the same date produces the
same row count (MERGE upsert, not re-insert).

**Independent test**: Run Scenario 1 full pipeline from `quickstart.md`; query
`SELECT COUNT(*) FROM Reporting.PolymerPricingFact WHERE pricing_date = '2026-07-13'` → 5;
re-run all three scripts; assert count still 5.

**Test criteria**:
- `Reporting.PolymerPricingFact` has exactly 1 row per `(MaterialKey, pricing_date)`
- `dbo.MaterialDim` contains an entry for every `material_code` in the gold file
- Re-running pipeline → row count unchanged (MERGE confirmed idempotent)
- No PII in any SQL column; log shows START, rows loaded, END

- [X] T016 [P] [US3] Add GoldSchema unit tests to `tests/unit/test_schemas.py` — assert DataFrame missing `loaded_at` column raises `SchemaError`; assert DataFrame with `loaded_at=None` raises `SchemaError`; assert DataFrame with two rows sharing same `(material_code, pricing_date)` raises `SchemaError` from uniqueness check; assert `sample_silver_df` extended with a `loaded_at` column passes `GoldSchema.validate()`

- [X] T017 [P] [US3] Create `tests/unit/test_transforms.py` — unit tests for the silver-to-gold `loaded_at` transform: given a silver DataFrame, assert the transform produces a new DataFrame with a `loaded_at` column of dtype `datetime64[ns]`; assert output row count equals input row count; assert `GoldSchema.validate(output)` passes without error; assert all `loaded_at` values are within 2 seconds of `pd.Timestamp.utcnow()`

- [X] T018 [P] [US3] Implement `pipeline/02_TransformData.py` — `argparse` `--date YYYYMMDD`; load `SILVER_DIR`, `GOLD_DIR`, `LOG_DIR` from `os.environ` — `EnvironmentError` + ERROR log on missing var; initialize logger; log `INFO "START date={date}"`; check for `SILVER_DIR/CodePolymer_Pricing/PolymerPricingSilver_{date}.parquet` existence → `WARNING "no silver file for {date}; skipping"` + `sys.exit(0)` if absent; read Parquet; append `loaded_at = pd.Timestamp.utcnow()` column; run `GoldSchema.validate(df)` → ERROR log + `sys.exit(1)` on failure; write to `GOLD_DIR/CodePolymer_Pricing/PolymerPricingGold_{date}.parquet` (snappy, no index); log `INFO "END gold_rows={n}"`

- [X] T019 [US3] Implement `pipeline/03_LoadToWarehouse.py` — `argparse` `--date YYYYMMDD`; load all 9 env vars from `os.environ` at startup and validate all are non-empty — `EnvironmentError` + ERROR log on any missing var (Constitution I); initialize logger; log `INFO "START date={date}"`; read `GOLD_DIR/CodePolymer_Pricing/PolymerPricingGold_{date}.parquet`; build SQLAlchemy engine using `urllib.parse.quote_plus` pattern from `research.md §2` (`mssql+pyodbc:///?odbc_connect={params}`); within a single `engine.begin()` transaction: (a) INSERT `material_code` values not yet in `dbo.MaterialDim` via `INSERT INTO dbo.MaterialDim (material_code) SELECT DISTINCT material_code FROM ... WHERE NOT EXISTS (...)`; (b) SELECT `MaterialKey` for each `material_code` and merge into DataFrame; (c) write resolved DataFrame (all gold columns + `MaterialKey`) to session temp table `#StagingPolymerPricing` via `df.to_sql("#StagingPolymerPricing", con, if_exists="replace", index=False)`; (d) execute MERGE T-SQL from `contracts/sql-ddl.sql` MERGE template via `sqlalchemy.text()`; catch `exc.SQLAlchemyError` → ERROR log with exception message + `sys.exit(1)`; log `INFO "END rows_loaded={n}"`

- [X] T020 [US3] Create `tests/integration/test_pipeline_e2e.py` — mark with `@pytest.mark.integration`; skip if any of `SQL_SERVER`, `SQL_DATABASE`, `SQL_USERNAME`, `SQL_PASSWORD` env vars are unset (`pytest.skip`); use `sample_landing_csv(tmp_path)` fixture to seed landing zone; run `01_IngestData.py`, `02_TransformData.py`, `03_LoadToWarehouse.py` sequentially via `subprocess.run([sys.executable, ...], check=True)`; connect via SQLAlchemy and assert: (a) `SELECT COUNT(*) FROM Reporting.PolymerPricingFact WHERE pricing_date = '2026-07-13'` = 5; (b) re-run all scripts; assert count still 5 (idempotency); (c) assert no duplicate `(MaterialKey, pricing_date)` pairs in fact table; (d) assert all 5 `material_code` values have a row in `dbo.MaterialDim`

---

## Final Phase: Polish and Cross-Cutting Concerns

**Purpose**: CI/CD quality gates, lint configuration, and quickstart sign-off.

- [X] T021 [P] Create `setup.cfg` at repository root — `[flake8]` section: `max-line-length = 120`, `extend-ignore = W503`; `[tool:pytest]` section: `markers = integration: marks tests that require a live Azure SQL connection (deselect with -m "not integration")`, `testpaths = tests`; confirm `flake8 pipeline/ tests/` exits with zero errors; confirm no `print(` calls exist in any `pipeline/*.py` file (Constitution IV audit)

- [ ] T022 Execute quickstart sign-off per `quickstart.md` — run all 5 validation scenarios (happy path, idempotency, validation rejection, missing credential, empty file); confirm all 10 checklist items in `quickstart.md` pass; document evidence (row count query outputs, log file excerpts) in the PR description before requesting review

---

## Dependencies

```
Phase 1: Setup (T001 → T002–T006 in parallel)
    └── Phase 2: Foundational (T007–T011 all in parallel)
            ├── Phase 3: US1 Bronze  ─ T012 [P] ┐ parallel
            │                          T013     ┘
            │       └── Phase 4: US2 Silver ─ T014 [P] ┐ parallel
            │                                  T015     ┘
            │               └── Phase 5: US3 Gold+Load
            │                       ├── T016 [P] ┐
            │                       ├── T017 [P] ├ parallel
            │                       ├── T018 [P] ┘
            │                       ├── T019 (after T018)
            │                       └── T020 (after T019)
            │                               └── Final Phase: Polish
            │                                       ├── T021 [P]
            │                                       └── T022 (after T021)
            └── T016, T017 may also start after T010 (schema defined)
```

**Key sequential constraints**:
- US1 must complete before US2 — both live in `pipeline/01_IngestData.py`
- US2 must complete before US3 — `02_TransformData` reads silver Parquet; `03_LoadToWarehouse` reads gold Parquet
- T019 (`03_LoadToWarehouse`) must complete before T020 (integration test)

---

## Parallel Execution Examples

### Phase 1 — after T001:
| Stream A | Stream B | Stream C | Stream D |
|----------|----------|----------|----------|
| T002 (requirements.txt) | T003 (.env.example) | T004 (.gitignore) | T005 (azure-pipelines.yml) |
| T006 (README.md) | | | |

### Phase 2 — all five in parallel:
| Stream A | Stream B | Stream C | Stream D | Stream E |
|----------|----------|----------|----------|----------|
| T007 (MaterialDim DDL) | T008 (PolymerPricingFact DDL) | T009 (logging_config.py) | T010 (pricing_schema.py) | T011 (conftest.py) |

### Phase 3 — two streams:
| Stream A | Stream B |
|----------|----------|
| T012 (test_schemas.py — bronze tests) | T013 (01_IngestData.py — bronze ingestion) |

### Phase 4 — two streams:
| Stream A | Stream B |
|----------|----------|
| T014 (add silver tests to test_schemas.py) | T015 (add silver step to 01_IngestData.py) |

### Phase 5 — three parallel then sequential:
| Stream A | Stream B | Stream C |
|----------|----------|----------|
| T016 (add gold tests to test_schemas.py) | T017 (test_transforms.py) | T018 (02_TransformData.py) |
| → T019 (03_LoadToWarehouse.py — after T018) | | |
| → T020 (integration test — after T019) | | |

---

## Implementation Strategy

**MVP — Phase 1 + 2 + Phase 3 only (T001–T013)**:
Delivers a working bronze ingestion pipeline with immutable raw storage, logger infrastructure,
and pandera schema foundation. Independently testable, compliant with Constitution I, III, IV,
VI, VII. Provides audit and lineage value even before silver/gold are built.

**Increment 2 — add Phase 4 (T014–T015)**:
Adds the silver validation trust boundary. Finance team can verify data quality and see
rejection counts without needing the SQL warehouse available.

**Increment 3 — add Phase 5 (T016–T020)**:
Completes the pipeline to `Reporting.PolymerPricingFact`. Delivers full business value for
analyst dashboards with idempotent daily refresh.

**Increment 4 — Final Phase (T021–T022)**:
Locks the implementation to CI/CD quality gates and constitution compliance for ongoing
operations.
