# Compliance Report — code-polymer

Run at: 2026-08-10T13:29:56.821150+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\code-polymer
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 90.3%** (131/145 weighted checks) — 1 high, 3 medium, 5 low severity violations

- Checks evaluated: 125
- Applicable checks (compliant + non-compliant): 69
- COMPLIANT: 60
- NON_COMPLIANT: 9
- NOT_APPLICABLE: 56
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 9

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** pipeline/03_LoadToWarehouse.py
**Sample agreement:** 100%
**Evidence:** The file loads gold data and writes it onward without any explicit data quality validation step in between.  Quoted: 'df = pd.read_parquet(gold_path, engine="pyarrow")'

**Suggested fix:** Add an explicit data quality validation step after reading the gold parquet and before any warehouse writes, failing fast on missing required columns or null MaterialKey/material_code values.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/03_LoadToWarehouse.py')
text = path.read_text()
old = '''    df = pd.read_parquet(gold_path, engine="pyarrow")
    log.info("Gold loaded: %d rows", len(df))

    engine = _build_engine(env)
'''
new = '''    df = pd.read_parquet(gold_path, engine="pyarrow")
    log.info("Gold loaded: %d rows", len(df))

    required_cols = {
        "material_code",
        "pricing_date",
        "price_value",
        "unit_of_measure",
        "currency_code",
        "source_file_name",
        "ingestion_timestamp",
    }
    missing_cols = sorted(required_cols - set(df.columns))
    if missing_cols:
        log.error("Data quality validation failed: missing columns: %s", missing_cols)
        sys.exit(1)
    if df["material_code"].isna().any():
        log.error("Data quality validation failed: material_code contains null values")
        sys.exit(1)

    engine = _build_engine(env)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new, 1))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'code-polymer' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from code-polymer to a compliant name using an allowed prefix and type, but the exact target name cannot be derived from the evidence so a placeholder is required.

```
mv code-polymer <allowed-prefix>-code-<descriptive_name>
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** pipeline/schemas/pricing_schema.py
**Sample agreement:** 67%
**Evidence:** The file has no logging or monitoring mechanism, so it violates the logging and monitoring policy.  Quoted: 'import pandas as pd'  [2/3 samples agreed: NON_COMPLIANTx2, NOT_APPLICABLEx1]

**Suggested fix:** Add a minimal logging mechanism to the schema module by importing logging and creating a module logger.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/schemas/pricing_schema.py')
text = path.read_text()
text = text.replace('import pandas as pd\n', 'import logging\nimport pandas as pd\n', 1)
text = text.replace('from pandera.typing import Series\n\n\nclass BronzeSchema', 'from pandera.typing import Series\n\nlogger = logging.getLogger(__name__)\n\n\nclass BronzeSchema', 1)
path.write_text(text)
PY
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 67%
**Evidence:** README.md, pipeline/02_TransformData.py, pipeline/03_LoadToWarehouse.py, and sql/CreateMaterialDim.sql describe the gold/reporting outputs, but no visible file states the row grain for the reporting fact output.  Quoted: 'gold data into `Reporting.PolymerPricingFact` in Azure SQL Server.'  [2/3 samples agreed: COMPLIANTx1, NON_COMPLIANTx2]

**Suggested fix:** Add a visible row-grain statement for the reporting fact output in the repository README without changing any data files.

```
python - <<'PY'
from pathlib import Path
p = Path('README.md')
text = p.read_text()
needle = 'gold data into `Reporting.PolymerPricingFact` in Azure SQL Server.'
insert = needle + '\n\nRow grain: one row per polymer pricing observation at the reporting fact level (one record per unique reporting fact grain).'
if needle not in text:
    raise SystemExit('target text not found')
if 'Row grain:' in text:
    raise SystemExit('row grain already documented')
p.write_text(text.replace(needle, insert, 1))
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

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/CreateMaterialDim.sql
**Sample agreement:** 100%
**Evidence:** The file contains non-PascalCase column names, violating the SQL column naming convention.  Quoted: 'material_code'

**Suggested fix:** Rename the non-PascalCase SQL columns and their unique constraint reference to PascalCase in dbo.MaterialDim.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreateMaterialDim.sql')
s = p.read_text()
s = s.replace('        material_code        VARCHAR(50)                  NOT NULL,\n', '        MaterialCode         VARCHAR(50)                  NOT NULL,\n')
s = s.replace('        material_description VARCHAR(255)                 NULL,\n', '        MaterialDescription  VARCHAR(255)                 NULL,\n')
s = s.replace('        created_date         DATETIME2                    NOT NULL\n', '        CreatedDate          DATETIME2                    NOT NULL\n')
s = s.replace('            CONSTRAINT DF_MaterialDim_CreatedDate DEFAULT GETDATE(),\n', '            CONSTRAINT DF_MaterialDim_CreatedDate DEFAULT GETDATE(),\n')
s = s.replace('            UNIQUE (material_code)\n', '            UNIQUE (MaterialCode)\n')
p.write_text(s)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/CreatePolymerPricingFact.sql
**Sample agreement:** 100%
**Evidence:** The file contains a column named pricing_date, which is not PascalCase.  Quoted: 'pricing_date         DATE                          NOT NULL,'

**Suggested fix:** Rename the non-PascalCase SQL column pricing_date to PricingDate and update its unique constraint and documented MERGE references accordingly.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreatePolymerPricingFact.sql')
text = p.read_text()
text = text.replace('        pricing_date         DATE                          NOT NULL,\n', '        PricingDate          DATE                          NOT NULL,\n')
text = text.replace('        CONSTRAINT UQ_PolymerPricingFact_MaterialDate\n            UNIQUE (MaterialKey, pricing_date)\n', '        CONSTRAINT UQ_PolymerPricingFact_MaterialDate\n            UNIQUE (MaterialKey, PricingDate)\n')
text = text.replace('target.pricing_date = source.pricing_date', 'target.PricingDate = source.PricingDate')
text = text.replace('(MaterialKey, pricing_date, price_value, unit_of_measure,\n', '(MaterialKey, PricingDate, price_value, unit_of_measure,\n')
text = text.replace('VALUES (source.MaterialKey, source.pricing_date, source.price_value,\n', 'VALUES (source.MaterialKey, source.PricingDate, source.price_value,\n')
text = text.replace('source.pricing_date', 'source.PricingDate')
p.write_text(text)
PY
```

## Checks that passed or did not apply

60 checks passed; 56 did not apply to this repository. See machine_report.json for the full list.
