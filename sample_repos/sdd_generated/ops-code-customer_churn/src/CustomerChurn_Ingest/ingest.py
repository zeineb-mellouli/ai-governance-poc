import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.utils.logging_config import get_logger

EXPECTED_COLUMNS = {
    "customer_id", "full_name", "email", "phone_number",
    "account_tenure_months", "monthly_usage_hours", "is_churned",
}

logger = get_logger("customer_churn.ingest")


def _date_from_filename(name: str) -> str:
    """Extract yyyyMMdd suffix from e.g. 'CustomerChurn_20260714.csv'."""
    return Path(name).stem.split("_")[-1]


def ingest(source_file: str, bronze_dir: str = "data/bronze") -> int:
    """
    Copy a landing CSV into the Bronze Parquet store.

    Exit codes:
      0 — success, or empty batch (no-op), or idempotent re-run
      1 — file not found, schema mismatch, or unexpected failure
    """
    logger.info("Stage start: ingestion | source=%s", source_file)
    try:
        src_path = Path(source_file)
        if not src_path.exists():
            logger.error("Source file not found: %s", source_file)
            return 1

        try:
            df = pd.read_csv(source_file)
        except Exception:
            logger.exception("Failed to read source file: %s", source_file)
            return 1

        # Schema guard (FR-015 / H3)
        actual = set(df.columns)
        missing = EXPECTED_COLUMNS - actual
        unexpected = actual - EXPECTED_COLUMNS
        if missing or unexpected:
            logger.error(
                "Column schema mismatch | missing=%s | unexpected=%s",
                sorted(missing),
                sorted(unexpected),
            )
            return 1

        # Empty-file guard (M2)
        if len(df) == 0:
            logger.warning(
                "Empty batch: zero records in %s, no Bronze written", src_path.name
            )
            logger.info("Stage end: ingestion | records_written=0")
            return 0

        date_str = _date_from_filename(src_path.name)
        Path(bronze_dir).mkdir(parents=True, exist_ok=True)
        bronze_path = Path(bronze_dir) / f"CustomerChurn_{date_str}.parquet"

        # Idempotency guard
        if bronze_path.exists():
            logger.warning(
                "Bronze file already exists for %s — skipping ingestion", date_str
            )
            logger.info("Stage end: ingestion | idempotent=True")
            return 0

        df = df.copy()
        df["ingested_at"] = datetime.now(timezone.utc).isoformat()
        df["source_file"] = src_path.name
        df.to_parquet(bronze_path, index=False)

        logger.info(
            "Stage end: ingestion | records_written=%d | output=%s",
            len(df),
            bronze_path,
        )
        return 0

    except Exception:
        logger.exception("Unexpected failure in ingestion stage")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest landing CSV to Bronze")
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--bronze-dir", default="data/bronze")
    args = parser.parse_args()
    sys.exit(ingest(args.source_file, args.bronze_dir))


if __name__ == "__main__":
    main()
