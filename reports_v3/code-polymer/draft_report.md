# Compliance Report — code-polymer

Run at: 2026-08-10T09:15:07.816960+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\code-polymer
Self-consistency samples (k): 3

## Summary

**Grade: FAIL** — severity-weighted pass rate 95.1% (252/265 weighted checks)

> 1 HIGH-severity violation(s) cap the grade at FAIL.

- Checks evaluated: 187
- Applicable checks (compliant + non-compliant): 129
- COMPLIANT: 120
- NON_COMPLIANT: 9
- NOT_APPLICABLE: 58
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 9

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** pipeline/03_LoadToWarehouse.py
**Sample agreement:** 100%
**Evidence:** The file loads data and proceeds to warehouse staging and MERGE operations without any explicit quality validation first.  Quoted: 'df = pd.read_parquet(gold_path, engine="pyarrow")'

**Suggested fix:** Add an explicit pre-load data quality validation step before any staging or MERGE operations in pipeline/03_LoadToWarehouse.py.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/03_LoadToWarehouse.py')
text = path.read_text()
old = '    df = pd.read_parquet(gold_path, engine="pyarrow")\n    log.info("Gold loaded: %d rows", len(df))\n\n    engine = _build_engine(env)\n'
new = '    df = pd.read_parquet(gold_path, engine="pyarrow")\n    log.info("Gold loaded: %d rows", len(df))\n\n    required_cols = [\n        "material_code",\n        "pricing_date",\n        "price_value",\n        "unit_of_measure",\n        "currency_code",\n        "source_file_name",\n        "ingestion_timestamp",\n    ]\n    missing_cols = [c for c in required_cols if c not in df.columns]\n    if missing_cols:\n        log.error("Data quality validation failed; missing columns: %s", missing_cols)\n        sys.exit(1)\n    if df[required_cols].isna().any().any():\n        log.error("Data quality validation failed; null values present in required columns")\n        sys.exit(1)\n\n    engine = _build_engine(env)\n'
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'code-polymer' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from code-polymer to a compliant name using an allowed prefix and type, but the exact new name cannot be determined from the evidence so a placeholder is left for manual selection.

```
mv code-polymer <allowed-prefix>-code-<name>
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** pipeline/schemas/pricing_schema.py
**Sample agreement:** 67%
**Evidence:** The pipeline module has no logging or monitoring implementation, so it violates the logging requirement.  Quoted: 'import pandas as pd'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Add minimal logging to the pricing schema module to satisfy the logging requirement without changing schema behavior.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/schemas/pricing_schema.py')
text = path.read_text()
needle = 'import pandas as pd\n'
insert = 'import logging\n\nlogger = logging.getLogger(__name__)\n\n'
if insert not in text:
    text = text.replace(needle, needle + insert)
    path.write_text(text)
PY
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline/transforms.py
**Sample agreement:** 100%
**Evidence:** file name stem 'transforms' is not CamelCase

**Suggested fix:** Rename to 'pipeline/Transforms.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'transforms' must be updated to 'Transforms' in the same change.

```
git mv pipeline/transforms.py pipeline/Transforms.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline/schemas/pricing_schema.py
**Sample agreement:** 100%
**Evidence:** file name stem 'pricing_schema' is not CamelCase

**Suggested fix:** Rename to 'pipeline/schemas/PricingSchema.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'pricing_schema' must be updated to 'PricingSchema' in the same change.

```
git mv pipeline/schemas/pricing_schema.py pipeline/schemas/PricingSchema.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** pipeline/utils/logging_config.py
**Sample agreement:** 100%
**Evidence:** file name stem 'logging_config' is not CamelCase

**Suggested fix:** Rename to 'pipeline/utils/LoggingConfig.py' to satisfy the NAM-5 naming grammar. This renames a Python module, so every import of 'logging_config' must be updated to 'LoggingConfig' in the same change.

```
git mv pipeline/utils/logging_config.py pipeline/utils/LoggingConfig.py
```

### NAM-5 · File and folder naming convention [LOW]

**Location:** specs/001-polymer-pricing-etl/contracts/sql-ddl.sql
**Sample agreement:** 100%
**Evidence:** file name stem 'sql-ddl' is not CamelCase

**Suggested fix:** Rename to 'specs/001-polymer-pricing-etl/contracts/SqlDdl.sql' to satisfy the NAM-5 naming grammar.

```
git mv specs/001-polymer-pricing-etl/contracts/sql-ddl.sql specs/001-polymer-pricing-etl/contracts/SqlDdl.sql
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/CreateMaterialDim.sql
**Sample agreement:** 100%
**Evidence:** The table defines non-PascalCase columns, including a date/time column named created_date without a qualifying business-event name.  Quoted: 'material_code        VARCHAR(50)                  NOT NULL,\n        material_description VARCHAR(255)                 NULL,\n        created_date         DATETIME2                    NOT NULL'

**Suggested fix:** Rename the non-PascalCase columns in dbo.MaterialDim to PascalCase and qualify the datetime column as a business event timestamp.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreateMaterialDim.sql')
s = p.read_text()
s = s.replace('        material_code        VARCHAR(50)                  NOT NULL,\n', '        MaterialCode         VARCHAR(50)                  NOT NULL,\n')
s = s.replace('        material_description VARCHAR(255)                 NULL,\n', '        MaterialDescription  VARCHAR(255)                 NULL,\n')
s = s.replace('        created_date         DATETIME2                    NOT NULL\n            CONSTRAINT DF_MaterialDim_CreatedDate DEFAULT GETDATE(),\n', '        CreatedAt            DATETIME2                    NOT NULL\n            CONSTRAINT DF_MaterialDim_CreatedAt DEFAULT GETDATE(),\n')
s = s.replace('            UNIQUE (material_code)\n', '            UNIQUE (MaterialCode)\n')
p.write_text(s)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/CreatePolymerPricingFact.sql
**Sample agreement:** 67%
**Evidence:** The column pricing_date is not in PascalCase, so the file violates the SQL column naming convention.  Quoted: 'pricing_date'  [2/3 samples agreed: COMPLIANTx1, NON_COMPLIANTx2]

**Suggested fix:** Rename the non-PascalCase SQL column pricing_date to PricingDate and update the unique constraint and documented MERGE references accordingly.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreatePolymerPricingFact.sql')
s = p.read_text()
s = s.replace('        pricing_date         DATE                          NOT NULL,\n', '        PricingDate          DATE                          NOT NULL,\n')
s = s.replace('        CONSTRAINT UQ_PolymerPricingFact_MaterialDate\n            UNIQUE (MaterialKey, pricing_date)\n', '        CONSTRAINT UQ_PolymerPricingFact_MaterialDate\n            UNIQUE (MaterialKey, PricingDate)\n')
s = s.replace('target.pricing_date', 'target.PricingDate')
s = s.replace('source.pricing_date', 'source.PricingDate')
s = s.replace('INSERT (MaterialKey, pricing_date, price_value, unit_of_measure,\n', 'INSERT (MaterialKey, PricingDate, price_value, unit_of_measure,\n')
p.write_text(s)
PY
```

## Checks that passed or did not apply

120 checks passed; 58 did not apply to this repository. See machine_report.json for the full list.
