# Compliance Report — ops-code-market_rate

Run at: 2026-08-03T13:25:56.126815+00:00
Repository path: C:\Users\CHMELLOULIZ\OneDrive - Tetra Pak\Desktop\ai-governance-poc\sample_repos\compliant\ops-code-market_rate

## Summary

- Total findings evaluated: 101
- COMPLIANT: 53
- NOT_APPLICABLE: 47
- NON_COMPLIANT: 1

## Non-compliant findings

### NAM-5 · File and folder naming convention [LOW]

**Location:** gold/PolymersMarketRate_2024-07-01.csv
**Confidence:** 0.98  |  **Risk score:** 0.98
**Evidence:** CSV header contains plural column names: "product_key,market_date,price_usd,volume_tonnes,source_region" (e.g. "volume_tonnes" and "source_region" are plural/compound forms rather than singular snake_case).

**Suggested fix:** Rename the CSV columns to singular snake_case to match the naming convention.

```
printf 'product_key,market_date,price_usd,volume_tonne,source_region\n' > gold/PolymersMarketRate_2024-07-01.csv
```

## Compliant checks

53 checks passed. See machine_report.json for the full list.
