"""
01_IngestData.py
Ingests raw market rate CSV files, validates schema integrity and
basic data quality, then writes validated copies for the transform step.
"""

import logging
import os
import sys

import pandas as pd
import pandera as pa
from pandera import Column, DataFrameSchema, Check

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log"),
    ],
)
logger = logging.getLogger(__name__)

MARKET_RATE_SCHEMA = DataFrameSchema(
    {
        "product_key": Column(str, Check.str_length(min_value=1, max_value=20)),
        "market_date": Column(str, Check.str_matches(r"^\d{4}-\d{2}-\d{2}$")),
        "price_usd": Column(float, [Check.greater_than(0), Check.less_than(100_000)]),
        "volume_tonnes": Column(float, Check.greater_than(0)),
        "source_region": Column(
            str, Check.isin(["Europe", "Asia", "Americas", "Middle East"])
        ),
    }
)

SOURCE_FILES = [
    "EthanolMarketRate_20240701.csv",
    "PolymersMarketRate_20240701.csv",
]


def ingest_market_rate_file(file_path: str) -> pd.DataFrame:
    """Load and validate a single market rate CSV file.

    Raises ValueError if quality or schema checks fail.
    Returns a validated DataFrame ready for the transform step.
    """
    logger.info("Ingesting file: %s", file_path)

    df = pd.read_csv(file_path)
    logger.info("Loaded %d rows from %s", len(df), file_path)

    # Null check — no missing values permitted in source data
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.error("Null values detected in %s:\n%s", file_path, null_counts[null_counts > 0])
        raise ValueError(f"Null values in source file: {file_path}")

    # Duplicate check — each product_key must appear once per file
    n_dupes = df.duplicated(subset=["product_key"]).sum()
    if n_dupes > 0:
        logger.error("Found %d duplicate product_key rows in %s", n_dupes, file_path)
        raise ValueError(f"Duplicate product_key rows: {n_dupes}")

    # Out-of-range check on price
    if (df["price_usd"] <= 0).any():
        logger.error("Non-positive price_usd values found in %s", file_path)
        raise ValueError("price_usd contains zero or negative values")

    # Schema validation (types + value constraints)
    df = MARKET_RATE_SCHEMA.validate(df)
    logger.info("Schema and quality validation passed for %s", file_path)

    return df


def main() -> None:
    # Medallion: read from bronze (raw, immutable), write validated output to silver
    data_folder = os.environ.get("BRONZE_PATH", "bronze")
    validated_folder = os.environ.get("SILVER_PATH", "silver")
    os.makedirs(validated_folder, exist_ok=True)

    logger.info("[BRONZE → SILVER] Ingestion job starting — bronze: %s  silver: %s", data_folder, validated_folder)

    for filename in SOURCE_FILES:
        source_path = os.path.join(data_folder, filename)
        try:
            df = ingest_market_rate_file(source_path)
            out_path = os.path.join(validated_folder, filename)
            df.to_csv(out_path, index=False)
            logger.info("Validated file written: %s", out_path)
        except Exception as exc:
            logger.exception("Ingestion failed for %s: %s", filename, exc)
            raise

    logger.info("[BRONZE → SILVER] Ingestion job complete — %d files written to silver", len(SOURCE_FILES))


if __name__ == "__main__":
    main()
