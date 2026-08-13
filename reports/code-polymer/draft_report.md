# Compliance Report — code-polymer

Run at: 2026-08-11T12:44:37.971375+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\code-polymer
Self-consistency samples (k): 1
> At k=1 no disagreement is measurable, so every confidence is 1.0 and the remediation confidence gate does not fire.

## Summary

**Weighted pass rate: 91.1%** (144/158 weighted checks) — 1 high, 3 medium, 5 low severity violations

- Checks evaluated: 125
- Applicable checks (compliant + non-compliant): 74
- COMPLIANT: 65
- NON_COMPLIANT: 9
- NOT_APPLICABLE: 51
- Requiring human action: 0

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 9

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** pipeline/03_LoadToWarehouse.py
**Sample agreement:** 100%
**Evidence:** The file loads data and sends it onward without any explicit quality validation first.  Quoted: 'df = pd.read_parquet(gold_path, engine="pyarrow")'

**Suggested fix:** Add an explicit pre-load data quality validation step before reading and loading the gold parquet file.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/03_LoadToWarehouse.py')
text = path.read_text()
old = '    df = pd.read_parquet(gold_path, engine="pyarrow")\n    log.info("Gold loaded: %d rows", len(df))\n'
new = '''    df = pd.read_parquet(gold_path, engine="pyarrow")
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
        log.error("Data quality validation failed; missing columns: %s", missing_cols)
        sys.exit(1)
    if df.empty:
        log.error("Data quality validation failed; gold file contains no rows")
        sys.exit(1)
    log.info("Gold loaded: %d rows", len(df))
'''
if old not in text:
    raise SystemExit('target snippet not found')
path.write_text(text.replace(old, new))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'code-polymer' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from code-polymer to a compliant name using an allowed prefix and type while preserving the existing suffix as the repository identifier.

```
mv code-polymer aud-code-polymer
```

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** pipeline/schemas/pricing_schema.py
**Sample agreement:** 100%
**Evidence:** The file performs pipeline-related schema work without any logging or monitoring mechanism.  Quoted: 'import pandas as pd'

**Suggested fix:** Add a minimal logging mechanism to the pipeline schema module by importing logging and creating a module-level logger.

```
python - <<'PY'
from pathlib import Path
path = Path('pipeline/schemas/pricing_schema.py')
text = path.read_text()
old = 'import pandas as pd\nimport pandera as pa\n'
new = 'import logging\n\nimport pandas as pd\nimport pandera as pa\n'
if old not in text:
    raise SystemExit('expected import block not found')
text = text.replace(old, new, 1)
marker = 'from pandera.typing import Series\n\n\n'
insert = 'from pandera.typing import Series\n\n\nlogger = logging.getLogger(__name__)\n\n\n'
if marker not in text:
    raise SystemExit('expected insertion point not found')
text = text.replace(marker, insert, 1)
path.write_text(text)
PY
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** README.md and pipeline/02_TransformData.py document the gold output path, while sql/CreateMaterialDim.sql and sql/CreatePolymerPricingFact.sql define the data-model tables.  Quoted: 'Gold (written): GOLD_DIR/CodePolymer_Pricing/PolymerPricingGold_{date}.parquet'

**Suggested fix:** Update the repository documentation to include the shared output table grain for the gold data model tables referenced by the SQL definitions.

```
python - <<'PY'
from pathlib import Path
p = Path('README.md')
text = p.read_text()
needle = 'Gold (written): GOLD_DIR/CodePolymer_Pricing/PolymerPricingGold_{date}.parquet'
insert = needle + '\n\nShared output table grain:\n- CreateMaterialDim.sql: Material dimension table grain\n- CreatePolymerPricingFact.sql: polymer pricing fact table grain\n'
if needle in text and 'Shared output table grain:' not in text:
    text = text.replace(needle, insert)
    p.write_text(text)
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
**Evidence:** The table definition includes non-PascalCase column names, violating the column naming convention.  Quoted: 'material_code'

**Suggested fix:** Rename the non-PascalCase SQL columns in dbo.MaterialDim to PascalCase and update the unique constraint to match.

```
sed -i "s/material_code/MaterialCode/g; s/material_description/MaterialDescription/g; s/created_date/CreatedDate/g" sql/CreateMaterialDim.sql
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/CreatePolymerPricingFact.sql
**Sample agreement:** 100%
**Evidence:** The file contains a non-PascalCase column name, pricing_date.  Quoted: 'pricing_date         DATE                          NOT NULL,'

**Suggested fix:** Rename the non-PascalCase SQL column pricing_date to PricingDate and update its unique constraint and MERGE references accordingly.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreatePolymerPricingFact.sql')
s = p.read_text()
s = s.replace('        pricing_date         DATE                          NOT NULL,\n', '        PricingDate          DATE                          NOT NULL,\n')
s = s.replace('        CONSTRAINT UQ_PolymerPricingFact_MaterialDate\n            UNIQUE (MaterialKey, pricing_date)\n', '        CONSTRAINT UQ_PolymerPricingFact_MaterialDate\n            UNIQUE (MaterialKey, PricingDate)\n')
s = s.replace('target.pricing_date = source.pricing_date', 'target.PricingDate = source.PricingDate')
s = s.replace('(MaterialKey, pricing_date, price_value, unit_of_measure,\n', '(MaterialKey, PricingDate, price_value, unit_of_measure,\n')
s = s.replace('source.MaterialKey, source.pricing_date, source.price_value,\n', 'source.MaterialKey, source.PricingDate, source.price_value,\n')
p.write_text(s)
PY
```

## Checks that passed or did not apply

65 checks passed; 51 did not apply to this repository. See machine_report.json for the full list.
