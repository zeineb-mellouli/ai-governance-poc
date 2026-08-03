# Feature Specification: Customer Churn Prediction Pipeline

**Feature Branch**: `user-story/001-churn-prediction-pipeline`

**Created**: 2026-07-14

**Status**: Draft

**Input**: User description: "Build a customer churn prediction pipeline for
ops-code-customer_churn. Raw customer records land as CSV in data/landing/ …"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Bronze Ingestion (Priority: P1)

A data engineer triggers ingestion of the daily landing file. The raw records are
copied into a Bronze store exactly as received, without any transformation. Once
written, the Bronze copy is never modified or overwritten by any subsequent process.
The data engineer can verify that every record from the landing file is present and
unaltered in Bronze.

**Why this priority**: All downstream layers depend on a preserved, immutable source
of truth. Nothing else can run without Bronze being populated first.

**Independent Test**: Run ingestion against a sample landing file and confirm that
the Bronze output contains the same row count and column values as the source, and
that no subsequent pipeline step can alter the Bronze records.

**Acceptance Scenarios**:

1. **Given** a landing CSV with N customer records, **When** ingestion runs,
   **Then** Bronze contains exactly N records with all original columns and values
   intact.
2. **Given** a Bronze record that was already ingested, **When** any validation or
   transformation step runs, **Then** the Bronze record remains unchanged.
3. **Given** a landing file that has already been ingested, **When** ingestion is
   triggered again for the same file, **Then** duplicates are not written to Bronze
   (idempotent behaviour).

---

### User Story 2 - Silver Validation & De-identification (Priority: P2)

A data engineer promotes Bronze data to Silver. Before any record is written to
Silver, the system checks for missing required values, duplicate customer identifiers,
and nonsensical numeric values (negative tenure or negative usage hours). Records
failing validation are rejected and do not reach Silver. All direct personal
identifiers — full name, email address, and phone number — are removed or masked
before the Silver write so that no raw PII ever appears in the Silver store, in
application logs, or in any printed output. Only the customer identifier remains as
the linking key downstream.

**Why this priority**: Silver is the foundation for feature engineering and model
training. Polluted or PII-bearing data here cascades into every downstream artefact.

**Independent Test**: Provide a Bronze dataset containing rows with missing values,
duplicate IDs, negative numeric values, and valid rows; confirm that only the valid
rows reach Silver, all with PII columns absent, and that the rejected rows are
recorded in a validation report without exposing PII.

**Acceptance Scenarios**:

1. **Given** a Bronze record with a null required field, **When** Silver validation
   runs, **Then** the record is rejected and does not appear in Silver.
2. **Given** two Bronze records sharing the same customer identifier, **When** Silver
   validation runs, **Then** the duplicate is rejected and does not appear in Silver.
3. **Given** a Bronze record with a negative account tenure or negative usage hours,
   **When** Silver validation runs, **Then** the record is rejected.
4. **Given** a valid Bronze record containing a customer's name, email, and phone
   number, **When** it is written to Silver, **Then** the Silver record contains no
   recognisable name, email address, or phone number — only the customer identifier
   remains as an identifier.
5. **Given** any validation failure or successful write, **When** logs are inspected,
   **Then** no raw name, email, or phone number value appears in any log line or
   printed output.

---

### User Story 3 - Reproducible Model Training (Priority: P3)

A data scientist trains a binary churn classifier on the de-identified Silver data.
The training run can be reproduced exactly by any other team member using the same
data: dependency versions are locked, and all random operations use a fixed seed so
that results do not vary between runs. Training progress, start and end times, and
evaluation metrics (e.g., accuracy, precision, recall, AUC) are recorded in a
persistent log or experiment tracker — not only printed to a terminal — so that runs
can be compared and audited after the session ends.

**Why this priority**: Reproducibility and auditability are governance requirements;
an unreproducible model cannot be safely promoted to production.

**Independent Test**: Run training twice on the same Silver data snapshot and confirm
that evaluation metrics are identical across runs; inspect the persistent experiment
log to confirm start/end markers and metric values are present without executing any
model code.

**Acceptance Scenarios**:

1. **Given** a fixed Silver dataset, **When** training is run twice with the same
   configuration, **Then** all evaluation metrics are identical across both runs.
2. **Given** a completed training run, **When** the persistent log or experiment
   tracker is queried after the session has ended, **Then** start time, end time,
   and evaluation metrics (accuracy, precision, recall, AUC) are all present.
3. **Given** a training run that encounters an error mid-execution, **When** logs are
   inspected, **Then** the error is recorded with a meaningful message in the
   persistent store — not silently swallowed.
4. **Given** the project's dependency manifest, **When** a new environment is built
   from it, **Then** the exact same package versions are installed with no version
   ambiguity.

---

### User Story 4 - Gold Prediction Publishing (Priority: P4)

A data engineer or automated scheduler publishes churn predictions to a Gold
reporting table intended for the customer success team. The table has one row per
customer identifier (no duplicates), each row carries a stable synthetic key
alongside the customer identifier, and the grain is documented so any consumer knows
what one row represents. The customer success team can query the table to identify
customers predicted to churn and take proactive action.

**Why this priority**: Gold is the end-consumer deliverable. It depends on all prior
layers being correct and is the value delivered to the business.

**Independent Test**: After a full pipeline run, query the Gold table and confirm
that every customer identifier from the Silver layer appears exactly once, that a
stable key column exists on every row, and that the prediction column is populated
with a binary churn indicator.

**Acceptance Scenarios**:

1. **Given** a completed model training run and a Silver dataset with M valid
   customers, **When** predictions are published to Gold, **Then** the Gold table
   contains exactly M rows, one per unique customer identifier.
2. **Given** the Gold table, **When** it is inspected, **Then** every row has a
   non-null stable synthetic key distinct from the customer identifier.
3. **Given** the Gold table's documentation (schema description or README), **When**
   a new consumer reads it, **Then** they can determine what one row represents
   (grain: one prediction per customer per pipeline run date) without asking the
   pipeline author.
4. **Given** the pipeline is run again on a new day's data, **When** Gold is updated,
   **Then** the previous day's predictions remain accessible (or the run date is
   included so history is retained).

---

### Edge Cases

- What happens when the landing file is empty or contains only a header row?
- What happens when all records in a Bronze batch fail Silver validation (zero valid
  rows written to Silver)?
- What happens when a customer identifier appears in Gold predictions but was absent
  from a previous Gold run (new customer)?
- How does the system behave when a landing file arrives with a column schema
  different from the expected shape?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST copy each landing CSV file into a Bronze store with
  all original columns and values preserved, without transformation.
- **FR-002**: The Bronze store MUST be append-only; no transformation or load step
  MUST ever modify or delete a Bronze record after ingestion.
- **FR-003**: Before writing any record to Silver, the system MUST reject records
  with missing required fields (`customer_id`, `account_tenure_months`,
  `monthly_usage_hours`, `is_churned`).
- **FR-004**: Before writing any record to Silver, the system MUST reject records
  where `customer_id` is duplicated within the batch.
- **FR-005**: Before writing any record to Silver, the system MUST reject records
  where `account_tenure_months` or `monthly_usage_hours` is negative.
- **FR-006**: The system MUST remove or irreversibly mask `full_name`, `email`, and
  `phone_number` before any record is written to Silver; these values MUST NOT appear
  in Silver data, application logs, or console output at any stage of processing.
- **FR-007**: The training step MUST use a fixed, explicitly set random seed so that
  results are identical across runs on the same data.
- **FR-008**: All project dependencies MUST be declared with pinned version numbers
  in a dependency manifest file; floating or unpinned versions are not permitted.
- **FR-009**: The training step MUST log a start marker, an end marker, and all
  evaluation metrics (accuracy, precision, recall, and AUC-ROC) to a persistent
  store that survives session termination.
- **FR-010**: Any exception during pipeline execution MUST be recorded in the
  persistent log with a meaningful error message; silent error suppression is not
  permitted.
- **FR-011**: The Gold reporting table MUST contain exactly one row per
  `customer_id`, with a binary churn prediction.
- **FR-012**: Every row in the Gold table MUST carry a stable synthetic key column
  (distinct from `customer_id`) that uniquely identifies the prediction record.
- **FR-013**: The Gold table grain ("one churn prediction per customer per pipeline
  run date") MUST be documented in the project README or an inline schema comment.
- **FR-014**: The pipeline MUST log start and end markers for each major stage
  (ingestion, validation, training, prediction publishing) to a persistent log.
- **FR-015**: The ingestion stage MUST validate that the landing CSV contains all
  expected columns (`customer_id`, `full_name`, `email`, `phone_number`,
  `account_tenure_months`, `monthly_usage_hours`, `is_churned`) before writing
  to Bronze; if any required column is absent or the file has an unrecognised
  schema, the system MUST log a descriptive error naming the missing or unexpected
  columns and exit with code `1` without writing any Bronze records.

### Key Entities *(include if feature involves data)*

- **LandingFile**: Raw CSV drop containing customer records with columns
  `customer_id`, `full_name`, `email`, `phone_number`, `account_tenure_months`,
  `monthly_usage_hours`, `is_churned`. Source of truth; never modified.
- **BronzeRecord**: Immutable copy of a landing file row. Retains all original
  columns. Append-only.
- **SilverRecord**: Validated, de-identified customer record. Contains `customer_id`,
  `account_tenure_months`, `monthly_usage_hours`, `is_churned`. No PII columns.
- **ValidationReport**: Record of rejected rows per batch, capturing the rejection
  reason (missing field, duplicate ID, out-of-range value) without exposing PII.
- **TrainedModel**: Binary classifier artifact produced by a reproducible training
  run. Associated with an experiment log entry.
- **ExperimentLog**: Persistent record of a training run: start time, end time,
  random seed used, dependency versions snapshot, and evaluation metrics.
- **ChurnPrediction** (Gold): One row per customer per pipeline run date. Contains
  `customer_id`, a stable synthetic `ChurnPredictionKey`, `is_churn_predicted`
  (binary), and `RunDate`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of landing file records are present and unaltered in Bronze after
  ingestion; zero records are modified or deleted from Bronze by any downstream step.
- **SC-002**: Silver contains zero records with missing required fields, duplicate
  customer identifiers, or negative numeric values after validation.
- **SC-003**: Silver contains zero occurrences of raw `full_name`, `email`, or
  `phone_number` values; the same is true for all log files and console outputs
  produced during pipeline execution.
- **SC-004**: Two training runs on the same Silver snapshot produce evaluation
  metrics that are bit-for-bit identical.
- **SC-005**: Training evaluation metrics (accuracy, precision, recall, AUC-ROC) are
  queryable from the persistent experiment log without re-running the pipeline.
- **SC-006**: The Gold table contains exactly one row per customer identifier with
  no null synthetic keys and a documented grain statement accessible to a new
  consumer without contacting the pipeline author.
- **SC-007**: Any pipeline stage failure produces a logged error entry in the
  persistent store within the same run; zero silent failures.

## Assumptions

- The landing CSV schema is stable: columns are always `customer_id`, `full_name`,
  `email`, `phone_number`, `account_tenure_months`, `monthly_usage_hours`,
  `is_churned` in that order with those exact names.
- `customer_id` is a string or integer that uniquely identifies a customer within a
  given landing file batch; global uniqueness across batches is not required.
- `is_churned` is a binary label (0 or 1) with no missing values in production
  training data; historically labelled data is available for supervised training.
- The customer success team queries Gold data directly (e.g., via SQL or a BI tool);
  no separate API layer is in scope for this feature.
- Model retraining is triggered manually or on a schedule by a data engineer, not
  automatically in response to data drift; drift detection is out of scope for v1.
- Gold table history is retained by including a `RunDate` column rather than
  overwriting previous predictions; full SCD-style versioning is out of scope for v1.
- The persistent experiment log is a file-based log or an MLflow-compatible store
  available in the project environment; choice of specific tool is a planning
  decision.
