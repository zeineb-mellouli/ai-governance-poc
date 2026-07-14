"""
pipeline/02_TransformData.py
-----------------------------
Stage 2 of the Polymer Pricing ETL pipeline.

Reads the validated silver Parquet, appends a ``loaded_at`` UTC timestamp,
validates the gold schema, and writes the gold Parquet.

Usage:
    python pipeline/02_TransformData.py --date YYYYMMDD

Required environment variables (Constitution I):
    SILVER_DIR, GOLD_DIR, LOG_DIR

Medallion layers:
    Silver (read):  SILVER_DIR/CodePolymer_Pricing/PolymerPricingSilver_{date}.parquet
    Gold (written): GOLD_DIR/CodePolymer_Pricing/PolymerPricingGold_{date}.parquet
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandera as pa

from pipeline.schemas.pricing_schema import GoldSchema
from pipeline.transforms import add_loaded_at
from pipeline.utils.logging_config import get_logger

_REQUIRED_ENV_VARS = ("SILVER_DIR", "GOLD_DIR", "LOG_DIR")


def _validate_env() -> dict:
    missing = [v for v in _REQUIRED_ENV_VARS if not os.environ.get(v, "").strip()]
    if missing:
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.ERROR,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        )
        logging.getLogger("TransformData").error(
            "Missing required environment variables: %s", missing
        )
        sys.exit(1)
    return {v: os.environ[v].strip() for v in _REQUIRED_ENV_VARS}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Silver → Gold aggregation — Polymer Pricing ETL"
    )
    parser.add_argument(
        "--date", required=True, metavar="YYYYMMDD", help="Processing date"
    )
    args = parser.parse_args()
    date = args.date

    env = _validate_env()
    log = get_logger("TransformData", env["LOG_DIR"])

    silver_path = (
        Path(env["SILVER_DIR"])
        / "CodePolymer_Pricing"
        / f"PolymerPricingSilver_{date}.parquet"
    )
    gold_dir = Path(env["GOLD_DIR"]) / "CodePolymer_Pricing"
    gold_path = gold_dir / f"PolymerPricingGold_{date}.parquet"

    log.info("START date=%s", date)

    if not silver_path.exists():
        log.warning(
            "No silver file for %s; skipping gold transform: %s", date, silver_path
        )
        sys.exit(0)

    import pandas as pd  # noqa: PLC0415 — deferred to keep startup fast when skipping
    df = pd.read_parquet(silver_path, engine="pyarrow")
    log.info("Silver loaded: %d rows", len(df))

    df = add_loaded_at(df)

    try:
        GoldSchema.validate(df)
    except pa.errors.SchemaError as exc:
        log.error("Gold schema validation failed: %s", exc)
        sys.exit(1)

    gold_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(gold_path, engine="pyarrow", compression="snappy", index=False)
    log.info("END gold_rows=%d path=%s", len(df), gold_path)


if __name__ == "__main__":
    main()
