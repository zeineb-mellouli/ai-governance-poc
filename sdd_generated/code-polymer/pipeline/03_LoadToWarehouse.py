"""
pipeline/03_LoadToWarehouse.py
--------------------------------
Stage 3 of the Polymer Pricing ETL pipeline.

Reads the gold Parquet, upserts new material codes into ``dbo.MaterialDim``,
resolves ``MaterialKey``, and merges records into
``Reporting.PolymerPricingFact`` via an idempotent T-SQL MERGE statement.

Usage:
    python pipeline/03_LoadToWarehouse.py --date YYYYMMDD

Required environment variables (Constitution I):
    SQL_SERVER, SQL_DATABASE, SQL_USERNAME, SQL_PASSWORD,
    GOLD_DIR, LOG_DIR

SQL targets:
    dbo.MaterialDim                (upsert: new material codes only)
    Reporting.PolymerPricingFact   (MERGE on MaterialKey + pricing_date)
"""

import argparse
import logging
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import sqlalchemy
from sqlalchemy import exc as sa_exc
from sqlalchemy import text

from pipeline.utils.logging_config import get_logger

_REQUIRED_ENV_VARS = (
    "SQL_SERVER",
    "SQL_DATABASE",
    "SQL_USERNAME",
    "SQL_PASSWORD",
    "LANDING_DIR",
    "BRONZE_DIR",
    "SILVER_DIR",
    "GOLD_DIR",
    "LOG_DIR",
)

_MATERIAL_MERGE_SQL = text(
    """
    MERGE INTO dbo.MaterialDim AS target
    USING #StagingMaterials AS source
        ON target.material_code = source.material_code
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (material_code) VALUES (source.material_code);
    """
)

_FACT_MERGE_SQL = text(
    """
    MERGE Reporting.PolymerPricingFact AS target
    USING #StagingPolymerPricing AS source
        ON  target.MaterialKey  = source.MaterialKey
        AND target.pricing_date = source.pricing_date
    WHEN MATCHED THEN
        UPDATE SET
            target.price_value         = source.price_value,
            target.unit_of_measure     = source.unit_of_measure,
            target.currency_code       = source.currency_code,
            target.source_file_name    = source.source_file_name,
            target.ingestion_timestamp = source.ingestion_timestamp,
            target.loaded_at           = GETDATE()
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (
            MaterialKey, pricing_date, price_value, unit_of_measure,
            currency_code, source_file_name, ingestion_timestamp, loaded_at
        )
        VALUES (
            source.MaterialKey, source.pricing_date, source.price_value,
            source.unit_of_measure, source.currency_code,
            source.source_file_name, source.ingestion_timestamp, GETDATE()
        );
    """
)


def _validate_env() -> dict:
    missing = [v for v in _REQUIRED_ENV_VARS if not os.environ.get(v, "").strip()]
    if missing:
        logging.basicConfig(
            stream=sys.stderr,
            level=logging.ERROR,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        )
        logging.getLogger("LoadToWarehouse").error(
            "Missing required environment variables: %s", missing
        )
        sys.exit(1)
    return {v: os.environ[v].strip() for v in _REQUIRED_ENV_VARS}


def _build_engine(env: dict) -> sqlalchemy.engine.Engine:
    """Build SQLAlchemy engine from env vars (Constitution I: no hardcoded creds)."""
    driver = "ODBC Driver 17 for SQL Server"
    odbc_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={env['SQL_SERVER']};"
        f"DATABASE={env['SQL_DATABASE']};"
        f"UID={env['SQL_USERNAME']};"
        f"PWD={env['SQL_PASSWORD']}"
    )
    params = urllib.parse.quote_plus(odbc_str)
    return sqlalchemy.create_engine(
        f"mssql+pyodbc:///?odbc_connect={params}",
        fast_executemany=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Gold → Reporting.PolymerPricingFact warehouse load"
    )
    parser.add_argument(
        "--date", required=True, metavar="YYYYMMDD", help="Processing date"
    )
    args = parser.parse_args()
    date = args.date

    env = _validate_env()
    log = get_logger("LoadToWarehouse", env["LOG_DIR"])

    gold_path = (
        Path(env["GOLD_DIR"])
        / "CodePolymer_Pricing"
        / f"PolymerPricingGold_{date}.parquet"
    )

    log.info("START date=%s", date)

    if not gold_path.exists():
        log.warning("No gold file for %s; nothing to load: %s", date, gold_path)
        sys.exit(0)

    df = pd.read_parquet(gold_path, engine="pyarrow")
    log.info("Gold loaded: %d rows", len(df))

    engine = _build_engine(env)
    n_rows = 0

    try:
        with engine.begin() as conn:
            # 1. Upsert new material codes into MaterialDim
            material_codes = pd.DataFrame(
                {"material_code": df["material_code"].unique()}
            )
            material_codes.to_sql(
                "#StagingMaterials", conn, if_exists="replace", index=False
            )
            conn.execute(_MATERIAL_MERGE_SQL)
            log.info(
                "MaterialDim upsert complete: %d unique codes", len(material_codes)
            )

            # 2. Resolve MaterialKey for each row
            keys_df = pd.read_sql(
                "SELECT material_code, MaterialKey FROM dbo.MaterialDim", conn
            )
            df = df.merge(keys_df, on="material_code", how="left")

            # 3. Stage gold columns that map to fact table
            staging_cols = [
                "MaterialKey",
                "pricing_date",
                "price_value",
                "unit_of_measure",
                "currency_code",
                "source_file_name",
                "ingestion_timestamp",
            ]
            df[staging_cols].to_sql(
                "#StagingPolymerPricing", conn, if_exists="replace", index=False
            )

            # 4. Idempotent MERGE into PolymerPricingFact
            result = conn.execute(_FACT_MERGE_SQL)
            n_rows = result.rowcount

    except sa_exc.SQLAlchemyError as exc:
        log.error("Database error during warehouse load: %s", exc)
        sys.exit(1)

    log.info(
        "END rows_loaded=%d target=Reporting.PolymerPricingFact", n_rows
    )


if __name__ == "__main__":
    main()
