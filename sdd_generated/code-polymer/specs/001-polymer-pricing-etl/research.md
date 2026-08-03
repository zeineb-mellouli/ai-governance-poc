# Research: Polymer Pricing ETL Pipeline

**Branch**: `001-polymer-pricing-etl` | **Phase 0** | **Date**: 2026-07-13

All `NEEDS CLARIFICATION` items from the Technical Context are resolved below.
Each entry records: Decision, Rationale, and Alternatives Considered.

---

## 1. Pandera Schema Approach

**Decision**: Use class-based `pandera.SchemaModel` (declarative API) for all three layer
schemas, defined in `pipeline/schemas/pricing_schema.py` as three classes: `BronzeSchema`,
`SilverSchema`, `GoldSchema`.

**Rationale**:
- `SchemaModel` provides IDE type-checking and autocomplete; schemas are Python classes that
  are version-controllable and self-documenting.
- Pandera raises `SchemaError` on validation failure, which is caught, logged with a structured
  error entry, and re-raised to halt the pipeline at the failing layer (Constitution II).
- Three schema classes mirror the three medallion layers, making the validation gate explicit
  and independently testable.

**Alternatives considered**:
- `Great Expectations`: powerful but heavyweight for a single-table pipeline; large dependency
  footprint. Rejected.
- Manual pandas `.isnull()` / `.duplicated()` checks: not schema-as-code, easy to omit a check,
  not version-controllable. Rejected.
- Imperative `DataFrameSchema`: equivalent capability but less readable than `SchemaModel` class
  syntax. Rejected in favour of `SchemaModel`.

---

## 2. SQLAlchemy + pyodbc Connection Pattern

**Decision**: Build the SQLAlchemy engine from environment variables using
`urllib.parse.quote_plus` to safely encode the password, avoiding issues with special characters.

```python
import os, urllib
from sqlalchemy import create_engine

driver  = "ODBC Driver 17 for SQL Server"
params  = urllib.parse.quote_plus(
    f"DRIVER={{{driver}}};"
    f"SERVER={os.environ['SQL_SERVER']};"
    f"DATABASE={os.environ['SQL_DATABASE']};"
    f"UID={os.environ['SQL_USERNAME']};"
    f"PWD={os.environ['SQL_PASSWORD']}"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)
```

**Rationale**: Reads all credentials from `os.environ` only (Constitution I). `quote_plus`
handles passwords containing `@`, `/`, `#` or other reserved chars. `fast_executemany=True`
improves bulk-insert throughput for the staging step in `03_LoadToWarehouse`.

**Alternatives considered**:
- Azure Managed Identity (`azure-identity`): the preferred production pattern for Azure-hosted
  services; deferred to v2 as it requires Azure RBAC configuration outside the pipeline scope.
- Direct pyodbc connection (without SQLAlchemy): acceptable but loses the DataFrame-native
  `to_sql()` integration. Rejected for consistency with pandas integration.
- Hardcoded connection string: prohibited by Constitution I.

---

## 3. Upsert (MERGE) Pattern for Azure SQL Server

**Decision**: Two-step load in `03_LoadToWarehouse`:
1. Write gold DataFrame to a per-run session-scoped temp table (`#StagingPolymerPricing`) via
   `pandas.DataFrame.to_sql(..., if_exists='replace')`.
2. Execute a T-SQL `MERGE` statement via `sqlalchemy.text()` to upsert from staging into
   `Reporting.PolymerPricingFact`.

```sql
MERGE Reporting.PolymerPricingFact AS target
USING #StagingPolymerPricing AS source
    ON target.MaterialKey = source.MaterialKey
   AND target.pricing_date = source.pricing_date
WHEN MATCHED THEN
    UPDATE SET
        target.price_value         = source.price_value,
        target.unit_of_measure     = source.unit_of_measure,
        target.currency_code       = source.currency_code,
        target.source_file_name    = source.source_file_name,
        target.ingestion_timestamp = source.ingestion_timestamp,
        target.loaded_at           = GETDATE()
WHEN NOT MATCHED BY TARGET THEN
    INSERT (MaterialKey, pricing_date, price_value, unit_of_measure,
            currency_code, source_file_name, ingestion_timestamp, loaded_at)
    VALUES (source.MaterialKey, source.pricing_date, source.price_value,
            source.unit_of_measure, source.currency_code, source.source_file_name,
            source.ingestion_timestamp, GETDATE());
```

**Rationale**: Native T-SQL `MERGE` is atomic (INSERT + UPDATE in one statement), avoids
locking the target table during DataFrame writes, and is idempotent — re-running for the same
batch produces the same target state (FR-011, SC-006).

**Alternatives considered**:
- `pandas.to_sql(if_exists='replace')` on target table directly: destroys all existing data on
  each run. Rejected.
- `pandas.to_sql(if_exists='append')` on target table: creates duplicates on re-run. Rejected.
- Row-by-row upsert: excessive round-trips for batch data; poor performance. Rejected.

---

## 4. File Naming: Date Suffix Convention for Scripts vs. Data Files

**Decision**: The `yyyyMMdd` date suffix (Constitution VI) applies to **data files only**,
not to pipeline script files.

| File type | Convention | Example |
|-----------|-----------|---------|
| Source CSV (landing) | `PascalCase_yyyyMMdd.csv` | `PolymerPricing_20260713.csv` |
| Bronze output (CSV) | `PascalCaseBronze_yyyyMMdd.csv` | `PolymerPricingBronze_20260713.csv` |
| Silver output (Parquet) | `PascalCaseSilver_yyyyMMdd.parquet` | `PolymerPricingSilver_20260713.parquet` |
| Gold output (Parquet) | `PascalCaseGold_yyyyMMdd.parquet` | `PolymerPricingGold_20260713.parquet` |
| Pipeline scripts | `PascalCase.py` (numbered prefix, no date) | `01_IngestData.py` |
| Log files | `PascalCase_yyyyMMdd.log` | `PipelineRun_20260713.log` |

**Rationale**: A script named `01_IngestData_20260713.py` would require creating a new file
every day, which is not the intent of a daily-scheduled batch job. The date-suffix convention
targets data deliverables whose content is date-specific, not code files whose behaviour is
static across runs.

---

## 5. Parquet vs. CSV for Intermediate Layers

**Decision**:
- **Bronze**: CSV — immutable copy of the exact source file format, human-readable for audit.
- **Silver** and **Gold**: Apache Parquet (via `pyarrow`).

**Rationale**: Parquet is columnar, typed, and compressed — reduces storage footprint and
preserves pandas dtype information (dates, floats) without round-trip string parsing. CSV for
bronze preserves the exact source format for full audit fidelity. `pandas 2.x` has native
Parquet read/write via `pyarrow` (pinned in `requirements.txt`).

**Alternatives considered**:
- All CSV layers: no dtype preservation; larger intermediate files; slower pandas reads on
  repeated processing. Rejected for silver/gold.
- All Parquet including bronze: changes the format of the immutable audit copy from the original
  source format. Rejected.

---

## 6. Acceptable Price Value Range

**Decision**: Validate `price_value` in `SilverSchema` as: `0.0 < price_value < 100_000.0`
(exclusive bounds).

**Rationale**: Commodity polymer market prices (polyethylene, polypropylene, PET, PVC, nylon)
currently trade in the approximate range of $500–$5,000 per metric tonne (USD). An upper bound
of $100,000 provides a large safety margin that accommodates exotic specialty polymers and future
price movements while still catching clearly erroneous data (negative values, zeros, or values
inflated by unit-of-measure errors such as reporting per-gram prices as per-tonne). This bound
should be reviewed annually against actual data distribution.

**Alternatives considered**:
- No upper bound: allows silent propagation of data entry errors into reporting. Rejected.
- Tight upper bound ($10,000): too close to real market peaks; would produce false rejections
  during commodity price spikes. Rejected.
- Configurable via env var: adds complexity for a value unlikely to change frequently; document
  as a `SilverSchema` constant that can be updated in code. Deferred.

---

## 7. Azure Pipelines CI/CD Configuration

**Decision**: `azure-pipelines.yml` triggers a build pipeline on pushes to `master` and
`develop` branches, running lint checks and the pytest suite. The minimum-1-reviewer PR policy
is enforced via **Azure DevOps Branch Policies** in the portal — not in YAML.

**Rationale**: Branch policies in Azure DevOps are server-side security controls that cannot be
bypassed by modifying the YAML file. The YAML handles automated build validation; the portal
handles the merge gate (approver count, build must succeed). Both together satisfy
Constitution VIII.

**Azure DevOps portal configuration required** (documented in `README.md`):
- `master` and `develop` branches: enable "Require a minimum number of reviewers" → 1
- "Check for linked work items": optional but recommended
- "Build validation": link to the `azure-pipelines.yml` pipeline

**Alternatives considered**:
- GitHub branch protection rules: equivalent for GitHub-hosted repos; not applicable here
  (Azure DevOps context).
- Pre-commit hooks only: client-side, bypassable with `--no-verify`. Insufficient as sole
  enforcement. Pre-commit hooks may be added as a developer convenience in addition to the
  portal policy.

---

## Summary of Resolved Items

| # | Item | Resolution |
|---|------|-----------|
| 1 | Pandera API style | `SchemaModel` class-based |
| 2 | Azure SQL connection | `os.environ` + `quote_plus` + SQLAlchemy 2.x |
| 3 | Upsert pattern | Temp-table staging + T-SQL `MERGE` |
| 4 | File naming for scripts | Date suffix on data files only; scripts use numbered CamelCase |
| 5 | Intermediate layer format | Bronze = CSV; Silver/Gold = Parquet |
| 6 | Price value range | `0 < price_value < 100,000` |
| 7 | PR reviewer enforcement | Azure DevOps Branch Policies (portal) + YAML build gate |

All `NEEDS CLARIFICATION` items resolved. Phase 1 design can proceed.
