import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.CustomerChurn_Ingest.ingest import ingest
from src.CustomerChurn_Predict.predict import predict
from src.CustomerChurn_Train.train import train
from src.CustomerChurn_Validate.validate import validate
from src.utils.logging_config import get_logger

logger = get_logger("customer_churn.pipeline")


def run_pipeline(args) -> int:
    """
    Chain all four pipeline stages in order: ingest → validate → train → predict.
    Aborts and logs the failing stage on any non-zero exit code.
    """
    logger.info("Pipeline start | source=%s", args.source_file)

    src_path = Path(args.source_file)
    date_str = src_path.stem.split("_")[-1]  # e.g. "20260714"
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    stages = [
        (
            "ingestion",
            lambda: ingest(args.source_file, args.bronze_dir),
        ),
        (
            "validation",
            lambda: validate(
                str(Path(args.bronze_dir) / f"CustomerChurn_{date_str}.parquet"),
                args.silver_dir,
            ),
        ),
        (
            "training",
            lambda: train(
                args.silver_dir,
                args.model_dir,
                args.random_seed,
                args.test_split,
            ),
        ),
        (
            "prediction",
            lambda: predict(
                str(Path(args.silver_dir) / f"CustomerChurn_{date_str}.parquet"),
                str(Path(args.model_dir) / f"ChurnClassifier_{today_str}.joblib"),
                args.gold_dir,
            ),
        ),
    ]

    for stage_name, stage_fn in stages:
        logger.info("Starting stage: %s", stage_name)
        code = stage_fn()
        if code != 0:
            logger.error(
                "Pipeline aborted at stage: %s | exit_code=%d", stage_name, code
            )
            return code

    logger.info("Pipeline complete")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Full customer churn prediction pipeline")
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--bronze-dir", default="data/bronze")
    parser.add_argument("--silver-dir", default="data/silver")
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--gold-dir", default="data/gold")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--test-split", type=float, default=0.2)
    args = parser.parse_args()
    sys.exit(run_pipeline(args))


if __name__ == "__main__":
    main()
