---
description: "Task list for Customer Churn Prediction Pipeline"
---

# Tasks: Customer Churn Prediction Pipeline

**Input**: Design documents from `specs/001-churn-prediction-pipeline/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/pipeline-interface.md ✅ | quickstart.md ✅

**Tests**: Five test files added at user request (pytest is a pinned dependency;
plan.md reserved the paths). Unit tests are written before their corresponding
implementation task within each phase.

**Remediation applied** (from `/speckit-analyze`):
- H1/H2: exit-code tables in contracts corrected (idempotent re-runs exit 0)
- H3 + M2: ingest guards for schema mismatch and empty file added to T007; empty Bronze guard added to T010
- M1: `logger.exception` specified in T010 (validate) and T015 (predict)
- M3: `churn_prediction_key` stability caveat added to T015

**Organization**: Tasks are grouped by user story; unit tests precede their
implementation task within each phase.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US4)
- File paths are relative to the repository root

---

## Phase 1: Setup

**Purpose**: Project initialization — directory structure, dependencies, package
scaffolding, and the README required by NAM-5.

- [X] T001 Create directory structure: `data/bronze/`, `data/silver/`, `data/gold/`, `models/`, `logs/`, `mlruns/`, `src/utils/`, `src/CustomerChurn_Ingest/`, `src/CustomerChurn_Validate/`, `src/CustomerChurn_Train/`, `src/CustomerChurn_Predict/`, `tests/unit/`, `tests/integration/`
- [X] T002 Create `requirements.txt` with fully pinned versions: `pandas==2.2.2`, `pandera==0.19.2`, `scikit-learn==1.5.0`, `mlflow==2.13.0`, `joblib==1.4.2`, `numpy==1.26.4`, `pyarrow==16.1.0`, `pytest==8.2.0`
- [X] T003 [P] Create `README.md` at repo root covering: project purpose, medallion layer descriptions, Gold table grain statement ("one churn prediction per `customer_id` per `run_date`"), and pipeline invocation instructions
- [X] T004 [P] Create `__init__.py` files for all Python packages: `src/__init__.py`, `src/utils/__init__.py`, `src/CustomerChurn_Ingest/__init__.py`, `src/CustomerChurn_Validate/__init__.py`, `src/CustomerChurn_Train/__init__.py`, `src/CustomerChurn_Predict/__init__.py`

---

## Phase 2: Foundational

**Purpose**: Shared logging infrastructure that every pipeline stage depends on.

**⚠️ CRITICAL**: Phases 3–6 depend on this phase being complete.

- [X] T005 Create `src/utils/logging_config.py` — configure a logger factory that attaches a `FileHandler` writing to `logs/pipeline_<yyyyMMdd>.log` and a `StreamHandler` to stdout; format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`; log messages MUST contain only counts, IDs, file paths, and metric values — never raw customer field values

**Checkpoint**: Logging infrastructure ready — user story implementation can begin.

---

## Phase 3: User Story 1 — Bronze Ingestion (Priority: P1) 🎯 MVP

**Goal**: Ingest the landing CSV into an immutable Bronze Parquet file; schema and
empty-file validated before writing; all records preserved unaltered; idempotent.

**Independent Test**: Run `pytest tests/unit/test_ingest.py`; confirm all assertions
pass. Then run ingestion against `data/landing/CustomerChurn_20260714.csv` and confirm
`data/bronze/CustomerChurn_20260714.parquet` contains 30 rows with all original columns
plus `ingested_at` and `source_file`; confirm idempotent re-run adds zero rows.

### Tests for User Story 1 ⚠️ Write these BEFORE implementing T007

- [X] T006 [P] [US1] Write `tests/unit/test_ingest.py` — cover: (a) happy-path ingestion copies all rows and adds `ingested_at` + `source_file` columns; (b) idempotent re-run writes zero additional rows and logs WARNING; (c) missing source file exits 1; (d) empty CSV (header only) exits 0 with zero Bronze rows written and WARNING logged; (e) CSV with a missing required column exits 1 with an error message naming the missing column

### Implementation for User Story 1

- [X] T007 [US1] Implement `src/CustomerChurn_Ingest/ingest.py` (depends on T006 being written first):
  - CLI args: `--source-file` (required), `--bronze-dir` (default: `data/bronze`)
  - **Schema guard (FR-015 + H3)**: after reading the CSV, verify all seven expected columns are present; if any are missing or unexpected columns appear, call `logger.error` naming the offending columns and exit `1` without writing Bronze
  - **Empty-file guard (M2)**: if the landing CSV has zero data rows after the header, log `WARNING "Empty batch: zero records in <filename>, no Bronze written"` and exit `0`
  - Copy all columns to Bronze Parquet with two pipeline columns appended: `ingested_at` (UTC timestamp) and `source_file` (basename of `--source-file`)
  - Write to `data/bronze/CustomerChurn_<yyyyMMdd>.parquet` (date parsed from source filename)
  - **Idempotency guard**: if the Bronze file already exists for this date, log `WARNING` and exit `0` without writing
  - Use logger `customer_churn.ingest` (via `logging_config.py`); wrap top-level logic in `try/except`; call `logger.exception` on any unhandled failure before exiting `1`
  - Exit codes: `0` success or empty batch or idempotent re-run; `1` file not found, schema mismatch, or unexpected failure

**Checkpoint**: Bronze ingestion independently functional. Fixture produces 30-row
Bronze file. Re-run is a no-op. Empty file and bad schema produce correct log entries.

---

## Phase 4: User Story 2 — Silver Validation & De-identification (Priority: P2)

**Goal**: Validate Bronze records against the quality gate; write only accepted,
PII-free records to Silver; produce a PII-free rejection report.

**Independent Test**: Run `pytest tests/unit/test_validate.py`; confirm all assertions
pass. Then run validation against the Bronze fixture; confirm Silver has 25 rows with
no PII columns; confirm ValidationReport shows 25 accepted / 5 rejected with correct
reasons; confirm log file grep finds no raw customer field values.

### Tests for User Story 2 ⚠️ Write these BEFORE implementing T009–T010

- [X] T008 [P] [US2] Write `tests/unit/test_validate.py` — cover: (a) PII columns (`full_name`, `email`, `phone_number`) absent from Silver output; (b) records with missing required fields rejected; (c) all occurrences of a duplicated `customer_id` rejected; (d) records with negative `account_tenure_months` or `monthly_usage_hours` rejected; (e) ValidationReport JSON has correct `accepted_count`/`rejected_count` with no raw field values in `rejections` entries; (f) exit code `3` when all records rejected; (g) empty Bronze file (zero rows) exits `0` with zero Silver rows written and WARNING logged

### Implementation for User Story 2

- [X] T009 [P] [US2] Define the Silver pandera schema in `src/CustomerChurn_Validate/schema.py`:
  - `customer_id`: `str`, not nullable
  - `account_tenure_months`: `float`, not nullable, `>= 0.0`
  - `monthly_usage_hours`: `float`, not nullable, `>= 0.0`
  - `is_churned`: `int`, not nullable, in `{0, 1}`
  - Note: uniqueness across the batch is checked separately in `validate.py` (pandera does not handle cross-row deduplication); this schema validates per-row constraints only
- [X] T010 [US2] Implement `src/CustomerChurn_Validate/validate.py` (depends on T008 written first, T009 complete):
  - CLI args: `--bronze-file` (required), `--silver-dir` (default: `data/silver`)
  - **Empty-Bronze guard (M2)**: if Bronze Parquet has zero rows, log `WARNING "Empty Bronze batch: zero records, no Silver written"` and exit `0`
  - Read Bronze Parquet; immediately drop `full_name`, `email`, `phone_number` before any processing or logging call
  - Identify all `customer_id` values appearing more than once; mark every occurrence rejected with reason `duplicate_customer_id`
  - Apply the pandera schema from `schema.py` to remaining records; collect per-row rejection reasons: `missing_required_field:<col>` or `out_of_range:<col><0`
  - Write accepted records to `data/silver/CustomerChurn_<yyyyMMdd>.parquet` with added `validated_at` (UTC) and `batch_id` (UUID) columns
  - Write `data/silver/ValidationReport_<yyyyMMdd>.json` with `batch_id`, `source_file`, `validated_at`, `total_records`, `accepted_count`, `rejected_count`, `rejections` (each entry: `row_index` int + `reason` string — no field values)
  - Use logger `customer_churn.validate`; log `INFO` stage markers and counts; `WARNING` per rejection category; wrap top-level logic in `try/except` and call `logger.exception` on any unhandled failure before exiting `1` **(M1 fix)**; never log raw field values
  - Exit codes: `0` ≥1 record accepted or empty Bronze; `1` Bronze file not found or unexpected failure; `3` all records rejected

**Checkpoint**: Silver validation independently functional. Fixture produces 25-row
Silver, 5-rejection report, zero PII in logs.

---

## Phase 5: User Story 3 — Reproducible Model Training (Priority: P3)

**Goal**: Train a `RandomForestClassifier` on Silver data with a fixed random seed;
log metrics to MLflow; results bit-for-bit identical across runs on the same data.

**Independent Test**: Run `pytest tests/unit/test_features.py`; confirm all assertions
pass. Then run training twice with `--random-seed 42`; query `mlruns/` and confirm
metric values are identical across both runs.

### Tests for User Story 3 ⚠️ Write these BEFORE implementing T012–T013

- [X] T011 [P] [US3] Write `tests/unit/test_features.py` — cover: (a) `build_features()` returns feature matrix `X` with columns `account_tenure_months` and `monthly_usage_hours` in that order; (b) label vector `y` equals the `is_churned` column; (c) `X` and `y` have equal row count; (d) function raises a descriptive error when required columns are absent from the input DataFrame

### Implementation for User Story 3

- [X] T012 [P] [US3] Implement feature engineering in `src/CustomerChurn_Train/features.py`:
  - Function `build_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]` returning feature matrix `X` (columns: `account_tenure_months`, `monthly_usage_hours`) and label vector `y` (`is_churned`)
  - No stochastic operations in this file
- [X] T013 [US3] Implement model training in `src/CustomerChurn_Train/train.py` (depends on T011 written first, T012 complete):
  - CLI args: `--silver-dir` (required), `--model-dir` (default: `models`), `--random-seed` (default: `42`), `--test-split` (default: `0.2`)
  - Load all `*.parquet` files from `--silver-dir`; concatenate into one DataFrame
  - Call `features.build_features()` to get `X`, `y`
  - Split with `train_test_split(random_state=seed)` and train `RandomForestClassifier(random_state=seed)`
  - Compute `accuracy`, `precision`, `recall`, `auc_roc` on the held-out test set
  - Set `mlflow.set_tracking_uri("mlruns")`; log params (`random_seed`, `test_split`), metrics, and the model artifact path
  - Save model to `models/ChurnClassifier_<yyyyMMdd>.joblib` via `joblib.dump`
  - Use logger `customer_churn.train`; log `INFO` stage start, training start, each metric value, stage end; wrap top-level logic in `try/except` and call `logger.exception` on any unhandled failure
  - Exit codes: `0` success; `1` no Silver Parquet files found; `4` MLflow logging failure

**Checkpoint**: Training independently functional. Two runs on the same Silver snapshot
produce identical MLflow metric values. `mlruns/` is queryable after session ends.

---

## Phase 6: User Story 4 — Gold Prediction Publishing (Priority: P4)

**Goal**: Publish one churn prediction row per customer to a Gold Parquet file with a
UUID surrogate key and documented grain; history retained across runs by date partitioning.

**Independent Test**: Run `pytest tests/unit/test_predict.py`; confirm all assertions
pass. Then run prediction against the Silver fixture and trained model; confirm Gold has
25 rows, one per unique `customer_id`, all with non-null `churn_prediction_key`.

### Tests for User Story 4 ⚠️ Write these BEFORE implementing T015

- [X] T014 [P] [US4] Write `tests/unit/test_predict.py` — cover: (a) Gold output has one row per unique `customer_id` from the Silver input; (b) every `churn_prediction_key` is a valid UUID string and non-null; (c) `is_churn_predicted` is in `{0, 1}` for every row; (d) `churn_probability` is between 0.0 and 1.0 for every row; (e) idempotency guard: if Gold file exists, stage exits `0` and logs WARNING without overwriting

### Implementation for User Story 4

- [X] T015 [US4] Implement `src/CustomerChurn_Predict/predict.py` (depends on T014 written first):
  - CLI args: `--silver-file` (required), `--model-file` (required), `--gold-dir` (default: `data/gold`)
  - Load Silver Parquet and the joblib model
  - Call `model.predict()` for `is_churn_predicted` and `model.predict_proba()[:,1]` for `churn_probability`
  - Assign a UUID `churn_prediction_key` to every row using `str(uuid.uuid4())`
  - **Key stability note (M3)**: this UUID is random per run; stability is guaranteed only by the idempotency guard below — if the Gold file is deleted and regenerated, new UUIDs are assigned
  - Add `run_date` (today's date) and `model_version` (basename of `--model-file`)
  - Output columns (in order): `churn_prediction_key`, `customer_id`, `is_churn_predicted`, `churn_probability`, `run_date`, `model_version`
  - Include module-level docstring: "Grain: one churn prediction per customer_id per run_date. churn_prediction_key is assigned once at write time and is stable for the lifetime of this Gold file."
  - Write to `data/gold/CustomerChurnPrediction_<yyyyMMdd>.parquet`
  - **Idempotency guard**: if Gold file for this date exists, log `WARNING` and exit `0`
  - Use logger `customer_churn.predict`; log `INFO` stage markers and prediction count; wrap top-level logic in `try/except` and call `logger.exception` on any unhandled failure before exiting `1` **(M1 fix)**
  - Exit codes: `0` success or idempotent re-run; `1` Silver or model file not found or unexpected failure

**Checkpoint**: All four user stories independently functional. Full pipeline produces
Bronze 30 rows → Silver 25 rows → Gold 25 rows.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Full pipeline runner, end-to-end integration test, and quickstart validation.

- [X] T016 [P] Create `src/pipeline.py` — CLI runner that chains all four stages in order (`ingest` → `validate` → `train` → `predict`); accepts the union of all stage args plus `--random-seed`; aborts and logs the failing stage name on any non-zero exit code; uses logger `customer_churn.pipeline`
- [X] T017 [P] Write `tests/integration/test_pipeline_e2e.py` — end-to-end test against `data/landing/CustomerChurn_20260714.csv`: (a) run full pipeline via `src/pipeline.py`; (b) assert Bronze has 30 rows; (c) assert Silver has 25 rows with no PII columns; (d) assert Gold has 25 rows with no nulls in `churn_prediction_key`; (e) scan `logs/pipeline_<today>.log` for PII patterns (names, `@example.com`, `555-01`) — assert zero matches; (f) run training a second time with same seed and assert MLflow metric values are identical across the two runs
- [X] T018 Run quickstart.md end-to-end validation manually against `data/landing/CustomerChurn_20260714.csv`; confirm all assertions in Steps 2–5 pass (Bronze 30, Silver 25, Gold 25, zero PII in logs, two training runs produce identical metrics)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T003 and T004 are parallel
- **Foundational (Phase 2)**: Depends on Phase 1 — T005 needs directories from T001
- **US1 Bronze (Phase 3)**: Depends on Phase 2; T006 (test) and implementation T007 sequential within phase
- **US2 Silver (Phase 4)**: Depends on Phase 3 (Bronze output as test fixture); T008 (test) parallel with T009 (schema); T010 depends on both
- **US3 Training (Phase 5)**: Depends on Phase 4 (Silver output as training data); T011 (test) and T012 (features) parallel; T013 depends on both
- **US4 Gold (Phase 6)**: Depends on Phase 5 (trained model); T014 (test) written before T015 (impl)
- **Polish (Phase 7)**: Depends on Phases 3–6; T016 and T017 are parallel; T018 depends on T017

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no story dependencies
- **US2 (P2)**: Can start after US1 (needs Bronze fixture)
- **US3 (P3)**: Can start after US2 (needs Silver data)
- **US4 (P4)**: Can start after US3 (needs trained model)

### Within Each User Story

- Write tests first, ensure they compile (and ideally fail) before implementing
- Models / schemas before services
- Commit after each phase checkpoint using `feat:` prefix (GIT-8)

### Parallel Opportunities

- T003 (README) ‖ T004 (__init__.py files) within Phase 1
- T008 (validate test) ‖ T009 (schema) within Phase 4 start
- T011 (features test) ‖ T012 (features impl) within Phase 5 start
- T016 (pipeline runner) ‖ T017 (integration test) within Phase 7

---

## Parallel Execution Examples

### Phase 4 (Silver)

```
Parallel start:
  Task T008: "Write tests/unit/test_validate.py"
  Task T009: "Define Silver pandera schema in src/CustomerChurn_Validate/schema.py"
Then sequential:
  Task T010: "Implement src/CustomerChurn_Validate/validate.py"
```

### Phase 5 (Training)

```
Parallel start:
  Task T011: "Write tests/unit/test_features.py"
  Task T012: "Implement feature engineering in src/CustomerChurn_Train/features.py"
Then sequential:
  Task T013: "Implement model training in src/CustomerChurn_Train/train.py"
```

### Phase 7 (Polish)

```
Parallel:
  Task T016: "Create src/pipeline.py"
  Task T017: "Write tests/integration/test_pipeline_e2e.py"
Then sequential:
  Task T018: "Run quickstart.md end-to-end validation"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T004)
2. Complete Phase 2: Foundational (T005)
3. Write T006 tests, implement T007 Bronze ingestion
4. **STOP AND VALIDATE**: `pytest tests/unit/test_ingest.py` passes; fixture produces 30-row Bronze; idempotent re-run confirmed
5. Proceed to Phase 4 when ready

### Incremental Delivery

1. Setup + Foundational → infrastructure ready
2. US1 Bronze → immutable source of truth ✓
3. US2 Silver → clean, PII-free training data ✓
4. US3 Training → reproducible model with persistent log ✓
5. US4 Gold → business-ready predictions ✓
6. Polish → full pipeline runner + integration test + manual quickstart validation ✓

---

## Notes

- `[P]` tasks target different files with no incomplete-task dependencies
- `[Story]` label maps each task to a user story for traceability back to spec.md
- All four stages share `src/utils/logging_config.py` — implement T005 before any stage code
- PII constraint: drop `full_name`, `email`, `phone_number` **before** any log call in T010, not after
- `churn_prediction_key` stability: guaranteed only by the idempotency guard; see T015 and data-model.md §Gold for the full caveat
- Commit after each phase checkpoint using `feat:` prefix per GIT-8
- Fixture file: `data/landing/CustomerChurn_20260714.csv` (30 rows: 25 valid + 5 invalid)