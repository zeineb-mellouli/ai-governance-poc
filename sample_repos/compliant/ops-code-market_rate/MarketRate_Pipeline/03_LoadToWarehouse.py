"""
03_LoadToWarehouse.py
Loads transformed market rate data into the SQL Server warehouse.
All credentials are read exclusively from environment variables —
no literal values appear in this file.

Target table : Reporting.EthanolMarketRateFact
Grain        : One row per product_key per market_date.
"""

import logging
import os
import sys

import pandas as pd
import sqlalchemy as sa

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log"),
    ],
)
logger = logging.getLogger(__name__)

TARGET_SCHEMA = "Reporting"
TARGET_TABLE = "EthanolMarketRateFact"
FULL_TABLE = f"{TARGET_SCHEMA}.{TARGET_TABLE}"


def build_connection_string() -> str:
    """Construct the SQLAlchemy connection string from environment variables only.

    Raises KeyError if any required variable is absent.
    """
    server = os.environ["DB_SERVER"]
    database = os.environ["DB_NAME"]
    username = os.environ["DB_USERNAME"]
    password = os.environ["DB_PASSWORD"]
    return (
        f"mssql+pyodbc://{username}:{password}@{server}/{database}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
    )


def validate_before_load(df: pd.DataFrame) -> None:
    """Final quality gate before any rows reach the warehouse.

    Raises ValueError on null values or grain violations.
    """
    null_counts = df.isnull().sum()
    if null_counts.any():
        logger.error("Null values detected before load:\n%s", null_counts[null_counts > 0])
        raise ValueError("Null values detected in pre-load check")

    grain_dupes = df.duplicated(subset=["product_key", "market_date"]).sum()
    if grain_dupes > 0:
        logger.error("Grain violation before load: %d duplicate rows", grain_dupes)
        raise ValueError(f"Grain violation pre-load: {grain_dupes} duplicates")

    logger.info("Pre-load validation passed — %d rows ready", len(df))


def load_to_warehouse(df: pd.DataFrame, engine: sa.Engine) -> int:
    """Append validated rows to the fact table. Returns rows written."""
    df.to_sql(
        TARGET_TABLE,
        con=engine,
        schema=TARGET_SCHEMA,
        if_exists="append",
        index=False,
        method="multi",
    )
    logger.info("Loaded %d rows into %s", len(df), FULL_TABLE)
    return len(df)


def main() -> None:
    # Medallion: read from gold layer only — this script never touches bronze or silver
    transformed_folder = os.environ.get("GOLD_PATH", "gold")
    source_file = os.path.join(transformed_folder, "EthanolMarketRate_20240701.csv")

    logger.info("[GOLD → Warehouse] Load job starting — gold: %s  target: %s", source_file, FULL_TABLE)

    try:
        df = pd.read_csv(source_file)
        validate_before_load(df)
        engine = sa.create_engine(build_connection_string())
        n_rows = load_to_warehouse(df, engine)
        logger.info("[GOLD → Warehouse] Load job complete — %d rows written to %s", n_rows, FULL_TABLE)
    except KeyError as exc:
        logger.error("Missing required environment variable: %s", exc)
        raise
    except Exception as exc:
        logger.exception("Load job failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
