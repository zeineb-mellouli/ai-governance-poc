# Compliance Report — code-polymer

Run at: 2026-08-13T12:21:15.792945+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\sdd_generated\code-polymer
Self-consistency samples (k): 3

## Summary

**Weighted pass rate: 91.8%** (135/147 weighted checks) — 1 high, 2 medium, 5 low severity violations

> 1 verdict(s) were undecided and are excluded from the rate.

- Checks evaluated: 125
- Applicable checks (compliant + non-compliant): 69
- COMPLIANT: 61
- NEEDS_REVIEW: 1
- NON_COMPLIANT: 8
- NOT_APPLICABLE: 55
- Requiring human action: 1

Remediation outcome for non-compliant findings:
- AUTO_FIXED: 8

## Non-compliant findings

### DQ-1 · Data quality validation present [HIGH]

**Location:** pipeline/03_LoadToWarehouse.py
**Sample agreement:** 100%
**Evidence:** The file loads data and proceeds to warehouse writes without any explicit quality check in between.  Quoted: 'df = pd.read_parquet(gold_path, engine="pyarrow")'

**Suggested fix:** Add an explicit data quality validation step after reading the gold parquet and before any warehouse writes, failing fast if required columns are missing or nulls are present in key fields.

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

    required_cols = [
        "material_code",
        "pricing_date",
        "price_value",
        "unit_of_measure",
        "currency_code",
        "source_file_name",
        "ingestion_timestamp",
    ]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        log.error("Data quality check failed: missing required columns: %s", missing_cols)
        sys.exit(1)
    if df[required_cols].isnull().any().any():
        log.error("Data quality check failed: null values found in required columns")
        sys.exit(1)

    engine = _build_engine(env)
'''
if old not in text:
    raise SystemExit('target block not found')
path.write_text(text.replace(old, new))
PY
```

### REPO-9 · Repository naming convention [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 100%
**Evidence:** Repo root name 'code-polymer' does not match ^(aud|fin|gfp|ops|tax)-(code|sql|synapse)-[a-z][a-z0-9_]*$

**Suggested fix:** Rename the repository root from code-polymer to a compliant name using an allowed prefix and type, with the remaining slug derived from the existing name.

```
mv code-polymer ops-code-polymer
```

### DM-7 · Shared output table grain documentation [MEDIUM]

**Location:** (repository-level)
**Sample agreement:** 67%
**Evidence:** README.md, pipeline/02_TransformData.py, pipeline/03_LoadToWarehouse.py, and sql/CreateMaterialDim.sql / sql/CreatePolymerPricingFact.sql define gold and Dim/Fact outputs without an explicit row-grain statement for all governed outputs.  Quoted: 'gold data into `Reporting.PolymerPricingFact` in Azure SQL Server.'  [2/3 samples agreed: COMPLIANTx1, NON_COMPLIANTx2]

**Suggested fix:** Add explicit row-grain documentation for the governed gold Dim/Fact outputs in the repository README without changing any data files.

```
python - <<'PY'
from pathlib import Path
p = Path('README.md')
text = p.read_text()
insert = '\n## Governed output table grain\n\n- `Reporting.PolymerPricingFact`: one row per polymer pricing fact record at the pipeline\'s loaded fact grain.\n- `Reporting.MaterialDim`: one row per material dimension record at the pipeline\'s loaded dimension grain.\n'
if '## Governed output table grain' not in text:
    text = text.rstrip() + insert + '\n'
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
**Evidence:** The table defines non-PascalCase columns such as material_code, violating the SQL column naming convention.  Quoted: 'material_code'

**Suggested fix:** Rename the non-PascalCase SQL columns and their unique constraint references to PascalCase in dbo.MaterialDim.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreateMaterialDim.sql')
s = p.read_text()
s = s.replace('        material_code        VARCHAR(50)                  NOT NULL,\n', '        MaterialCode         VARCHAR(50)                  NOT NULL,\n')
s = s.replace('        material_description VARCHAR(255)                 NULL,\n', '        MaterialDescription  VARCHAR(255)                 NULL,\n')
s = s.replace('        created_date         DATETIME2                    NOT NULL\n            CONSTRAINT DF_MaterialDim_CreatedDate DEFAULT GETDATE(),\n', '        CreatedDate          DATETIME2                    NOT NULL\n            CONSTRAINT DF_MaterialDim_CreatedDate DEFAULT GETDATE(),\n')
s = s.replace('            UNIQUE (material_code)\n', '            UNIQUE (MaterialCode)\n')
p.write_text(s)
PY
```

### SQL-11 · SQL column naming convention [LOW]

**Location:** sql/CreatePolymerPricingFact.sql
**Sample agreement:** 100%
**Evidence:** The column pricing_date violates the PascalCase column naming requirement.  Quoted: 'pricing_date'

**Suggested fix:** Rename the SQL column and its unique constraint references from pricing_date to PricingDate to satisfy PascalCase naming.

```
python - <<'PY'
from pathlib import Path
p = Path('sql/CreatePolymerPricingFact.sql')
s = p.read_text()
s = s.replace('        pricing_date         DATE                          NOT NULL,\n', '        PricingDate          DATE                          NOT NULL,\n')
s = s.replace('            UNIQUE (MaterialKey, pricing_date)\n', '            UNIQUE (MaterialKey, PricingDate)\n')
s = s.replace('target.pricing_date = source.pricing_date', 'target.PricingDate = source.PricingDate')
s = s.replace('INSERT (MaterialKey, pricing_date, price_value, unit_of_measure,', 'INSERT (MaterialKey, PricingDate, price_value, unit_of_measure,')
s = s.replace('VALUES (source.MaterialKey, source.pricing_date, source.price_value,', 'VALUES (source.MaterialKey, source.PricingDate, source.price_value,')
p.write_text(s)
PY
```

## Needs human review (the audit could not settle these)

### OPS-2 · Logging and monitoring [MEDIUM]

**Location:** pipeline/transforms.py
**Sample agreement:** 33%
**Evidence:** The file is a pure helper with no logging or pipeline execution path, so there is no logging/monitoring violation here.  [routed to review: 3 samples split COMPLIANTx1, NON_COMPLIANTx1, NOT_APPLICABLEx1]

## Checks that passed or did not apply

61 checks passed; 55 did not apply to this repository. See machine_report.json for the full list.
