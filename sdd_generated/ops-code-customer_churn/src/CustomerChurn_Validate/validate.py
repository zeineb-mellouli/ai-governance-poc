import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.utils.logging_config import get_logger

PII_COLUMNS = ["full_name", "email", "phone_number"]
REQUIRED_COLUMNS = ["customer_id", "account_tenure_months", "monthly_usage_hours", "is_churned"]

logger = get_logger("customer_churn.validate")


def validate(bronze_file: str, silver_dir: str = "data/silver") -> int:
    """
    Validate and de-identify Bronze records, writing accepted rows to Silver.

    Exit codes:
      0 — success (≥1 record accepted), or empty Bronze (no-op)
      1 — Bronze file not found or unexpected failure
      3 — all records rejected; Silver not written
    """
    logger.info("Stage start: validation | source=%s", bronze_file)
    try:
        bronze_path = Path(bronze_file)
        if not bronze_path.exists():
            logger.error("Bronze file not found: %s", bronze_file)
            return 1

        df = pd.read_parquet(bronze_file)

        # Empty-Bronze guard (M2)
        if len(df) == 0:
            logger.warning("Empty Bronze batch: zero records, no Silver written")
            logger.info("Stage end: validation | records_written=0")
            return 0

        total = len(df)
        batch_id = str(uuid.uuid4())
        date_str = bronze_path.stem.split("_")[-1]

        # Drop PII immediately — before any further processing or logging (FR-006)
        df = df.drop(columns=PII_COLUMNS, errors="ignore").copy()

        # Coerce types for consistent comparisons
        df["account_tenure_months"] = pd.to_numeric(
            df["account_tenure_months"], errors="coerce"
        )
        df["monthly_usage_hours"] = pd.to_numeric(
            df["monthly_usage_hours"], errors="coerce"
        )
        df["is_churned"] = pd.to_numeric(df["is_churned"], errors="coerce")

        rejections: list[dict] = []

        # 1. Reject all occurrences of duplicated customer_id (FR-004)
        dup_mask = df["customer_id"].duplicated(keep=False)
        for idx in df.index[dup_mask]:
            rejections.append({"row_index": int(idx), "reason": "duplicate_customer_id"})

        # 2. Per-row validation on non-duplicate records
        for idx, row in df[~dup_mask].iterrows():
            reason = None
            for col in REQUIRED_COLUMNS:
                if pd.isna(row.get(col)):
                    reason = f"missing_required_field:{col}"
                    break
            if reason is None:
                if row["account_tenure_months"] < 0:
                    reason = "out_of_range:account_tenure_months<0"
                elif row["monthly_usage_hours"] < 0:
                    reason = "out_of_range:monthly_usage_hours<0"
                elif int(row["is_churned"]) not in (0, 1):
                    reason = "invalid_value:is_churned"
            if reason:
                rejections.append({"row_index": int(idx), "reason": reason})

        rejected_indices = {r["row_index"] for r in rejections}
        accepted = df[~df.index.isin(rejected_indices)].copy()
        accepted_count = len(accepted)
        rejected_count = len(rejections)

        # Log counts only — never log field values (PII-4)
        logger.info(
            "Validation complete | total=%d | accepted=%d | rejected=%d | batch=%s",
            total, accepted_count, rejected_count, batch_id,
        )
        for category in ("duplicate_customer_id", "missing_required_field",
                         "out_of_range", "invalid_value"):
            n = sum(1 for r in rejections if category in r["reason"])
            if n:
                logger.warning("Rejected %d record(s) | category=%s", n, category)

        Path(silver_dir).mkdir(parents=True, exist_ok=True)
        report = {
            "batch_id": batch_id,
            "source_file": bronze_path.name,
            "validated_at": datetime.now(timezone.utc).isoformat(),
            "total_records": total,
            "accepted_count": accepted_count,
            "rejected_count": rejected_count,
            "rejections": rejections,
        }
        report_path = Path(silver_dir) / f"ValidationReport_{date_str}.json"
        report_path.write_text(json.dumps(report, indent=2))

        if accepted_count == 0:
            logger.error(
                "All %d records rejected — no Silver written | report=%s",
                total, report_path,
            )
            return 3

        now = datetime.now(timezone.utc).isoformat()
        accepted = accepted.reset_index(drop=True)
        accepted["validated_at"] = now
        accepted["batch_id"] = batch_id

        silver_path = Path(silver_dir) / f"CustomerChurn_{date_str}.parquet"
        accepted.to_parquet(silver_path, index=False)
        logger.info(
            "Stage end: validation | output=%s | report=%s", silver_path, report_path
        )
        return 0

    except Exception:
        logger.exception("Unexpected failure in validation stage")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Bronze and write Silver")
    parser.add_argument("--bronze-file", required=True)
    parser.add_argument("--silver-dir", default="data/silver")
    args = parser.parse_args()
    sys.exit(validate(args.bronze_file, args.silver_dir))


if __name__ == "__main__":
    main()
