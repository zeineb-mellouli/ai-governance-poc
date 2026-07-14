"""
pipeline/01_IngestData.py
--------------------------
Stage 1 of the Polymer Pricing ETL pipeline.

Reads a daily polymer pricing CSV from the landing zone, writes an
immutable copy to the bronze layer (Constitution III), then validates
and cleanses the data into the silver layer using pandera (Constitution II).

Usage:
    python pipeline/01_IngestData.py --date YYYYMMDD

Required environment variables (Constitution I):
    LANDING_DIR, BRONZE_DIR, SILVER_DIR, LOG_DIR

Medallion layers written:
    Bronze: BRONZE_DIR/CodePolymer_Pricing/PolymerPricingBronze_{date}.csv
    Silver: SILVER_DIR/CodePolymer_Pricing/PolymerPricingSilver_{date}.parquet
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure repo root is on sys.path when the script is run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import pandera as pa

from pipeline.schemas.pricing_schema import BronzeSchema, SilverSchema
from pipeline.utils.logging_config import get_logger

_REQUIRED_ENV_VARS = ("LANDING_DIR", "BRONZE_DIR", "SILVER_DIR", "LOG_DIR")


def _validate_env() -> dict:
    """Assert all required env vars are present; exit(1) if not."""
    missing = [v for v in _REQUIRED_ENV_VARS if not os.environ.get(v, "").strip()]
    if missing:
        # Logger not yet initialised — use basicConfig to write to stderr
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.ERROR,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        )
        logging.getLogger("IngestData").error(
            "Missing required environment variables: %s", missing
        )
        sys.exit(1)
    return {v: os.environ[v].strip() for v in _REQUIRED_ENV_VARS}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bronze ingestion + Silver validation — Polymer Pricing ETL"
    )
    parser.add_argument(
        "--date", required=True, metavar="YYYYMMDD", help="Processing date"
    )
    args = parser.parse_args()
    date = args.date

    env = _validate_env()
    log = get_logger("IngestData", env["LOG_DIR"])

    source_path = Path(env["LANDING_DIR"]) / f"PolymerPricing_{date}.csv"
    bronze_dir = Path(env["BRONZE_DIR"]) / "CodePolymer_Pricing"
    silver_dir = Path(env["SILVER_DIR"]) / "CodePolymer_Pricing"
    bronze_path = bronze_dir / f"PolymerPricingBronze_{date}.csv"
    silver_path = silver_dir / f"PolymerPricingSilver_{date}.parquet"

    log.info("START date=%s source=%s", date, source_path)

    # ── BRONZE STEP ──────────────────────────────────────────────────────────

    # Idempotency: skip if bronze already written for this date
    if bronze_path.exists():
        log.warning(
            "Bronze already exists for %s — skipping ingest: %s", date, bronze_path
        )
        sys.exit(0)

    # Read source CSV (all columns as str to preserve raw values)
    try:
        df = pd.read_csv(source_path, dtype=str, encoding="utf-8")
    except FileNotFoundError:
        log.error("Source file not found: %s", source_path)
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        log.error("Failed to read source file %s: %s", source_path, exc)
        sys.exit(1)

    if df.empty:
        log.warning(
            "Source file has 0 data rows for date %s; skipping all layer writes", date
        )
        sys.exit(0)

    # Append metadata columns (Constitution VI: bronze stores original + metadata)
    df = df.copy()
    df["source_file_name"] = source_path.name
    df["ingestion_timestamp"] = pd.Timestamp.now(tz="UTC").isoformat()

    # Coerce price_value to float; non-numeric values become NaN (caught by schema)
    df["price_value"] = pd.to_numeric(df["price_value"], errors="coerce")

    # Validate bronze schema (column presence + nullability)
    try:
        BronzeSchema.validate(df)
    except pa.errors.SchemaError as exc:
        log.error("Bronze schema validation failed: %s", exc)
        sys.exit(1)

    # Write immutable bronze CSV (Constitution III: never overwritten by transform)
    bronze_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(bronze_path, index=False, encoding="utf-8")
    log.info("Bronze written: bronze_rows=%d path=%s", len(df), bronze_path)

    # ── SILVER STEP ──────────────────────────────────────────────────────────

    # Deduplicate on business key before validation
    n_before_dedup = len(df)
    df = df.drop_duplicates(subset=["material_code", "pricing_date"], keep="first")
    n_dropped = n_before_dedup - len(df)
    if n_dropped > 0:
        log.warning(
            "Dropped %d duplicate rows on (material_code, pricing_date)", n_dropped
        )

    # Cast to typed dtypes required by SilverSchema
    df = df.copy()
    df["pricing_date"] = pd.to_datetime(df["pricing_date"], errors="coerce")
    df["ingestion_timestamp"] = pd.to_datetime(df["ingestion_timestamp"], errors="coerce")

    # Silver validation: lazy=True collects all failures before raising
    try:
        SilverSchema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as exc:
        # Extract failing row indices and drop them; log summary
        failure_idx = set(
            exc.failure_cases["index"].dropna().astype(int).tolist()
        )
        n_before_excl = len(df)
        df = df.drop(index=list(failure_idx), errors="ignore")
        n_excluded = n_before_excl - len(df)
        check_summary = (
            exc.failure_cases[["column", "check"]]
            .drop_duplicates()
            .to_dict("records")
        )
        log.warning(
            "Excluded %d rows from silver (validation failures): %s",
            n_excluded,
            check_summary,
        )
    except pa.errors.SchemaError as exc:
        log.error("Silver schema error: %s", exc)
        sys.exit(1)

    df = df.reset_index(drop=True)

    if df.empty:
        log.warning(
            "Zero valid rows for %s after silver validation; skipping silver write",
            date,
        )
        sys.exit(0)

    # Write silver Parquet
    silver_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(silver_path, engine="pyarrow", compression="snappy", index=False)
    log.info("END silver_rows=%d path=%s", len(df), silver_path)


if __name__ == "__main__":
    main()
