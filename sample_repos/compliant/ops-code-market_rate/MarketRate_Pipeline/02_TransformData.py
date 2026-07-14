"""
02_TransformData.py
Transforms validated market rate data into the star-schema shape
expected by the warehouse load step.

Grain of output: one row per product_key per market_date.
"""

import logging
import os
import sys

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log"),
    ],
)
logger = logging.getLogger(__name__)

# Fixed seed for any stochastic operation (imputation, sampling)
np.random.seed(42)

APPROVED_REGIONS = {"Europe", "Asia", "Americas", "Middle East"}
SOURCE_FILES = [
    "EthanolMarketRate_20240701.csv",
    "PolymersMarketRate_20240701.csv",
]


def transform_to_fact_shape(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Convert a validated ingestion DataFrame to the warehouse fact shape.

    Grain: one row per product_key per market_date.
    Raises ValueError on grain violations or unknown region values.
    """
    logger.info("Transforming %d rows from %s", len(df), source_name)

    # Standardise date column
    df["market_date"] = pd.to_datetime(df["market_date"]).dt.date

    # Remove rows with unapproved regions — should never happen post-validation,
    # but defend in depth
    unknown_regions = df[~df["source_region"].isin(APPROVED_REGIONS)]
    if not unknown_regions.empty:
        logger.warning(
            "Dropping %d rows with unknown source_region values: %s",
            len(unknown_regions),
            unknown_regions["source_region"].unique().tolist(),
        )
        df = df[df["source_region"].isin(APPROVED_REGIONS)]

    # Grain check — each product_key must appear exactly once per market_date
    grain_dupes = df.duplicated(subset=["product_key", "market_date"]).sum()
    if grain_dupes > 0:
        logger.error(
            "Grain violation in %s: %d duplicate product_key/market_date rows",
            source_name,
            grain_dupes,
        )
        raise ValueError(f"Grain violation after transform: {grain_dupes} duplicates")

    logger.info("Transform complete — %d rows ready for load", len(df))
    return df


def main() -> None:
    # Medallion: read from silver (validated), write transformed output to gold
    validated_folder = os.environ.get("SILVER_PATH", "silver")
    transformed_folder = os.environ.get("GOLD_PATH", "gold")
    os.makedirs(transformed_folder, exist_ok=True)

    logger.info("[SILVER → GOLD] Transform job starting — silver: %s  gold: %s", validated_folder, transformed_folder)

    for filename in SOURCE_FILES:
        source_path = os.path.join(validated_folder, filename)
        try:
            df = pd.read_csv(source_path)
            df_out = transform_to_fact_shape(df, filename)
            out_path = os.path.join(transformed_folder, filename)
            df_out.to_csv(out_path, index=False)
            logger.info("Transformed file written: %s", out_path)
        except Exception as exc:
            logger.exception("Transform failed for %s: %s", filename, exc)
            raise

    logger.info("[SILVER → GOLD] Transform job complete")


if __name__ == "__main__":
    main()
