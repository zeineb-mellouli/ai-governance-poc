"""
Grain: one churn prediction per customer_id per run_date.

churn_prediction_key is assigned once when the Gold file is written and is
stable for the lifetime of that file. It is not deterministically reproducible
from input data — if a Gold file is deleted and regenerated, new UUIDs are
assigned. Stability is guaranteed by the idempotency guard below.
"""
import argparse
import sys
import uuid
from datetime import date
from pathlib import Path

import joblib
import pandas as pd

from src.utils.logging_config import get_logger

logger = get_logger("customer_churn.predict")

FEATURE_COLS = ["account_tenure_months", "monthly_usage_hours"]


def predict(
    silver_file: str,
    model_file: str,
    gold_dir: str = "data/gold",
) -> int:
    """
    Generate churn predictions from a Silver file and publish to Gold.

    Exit codes:
      0 — success, or idempotent re-run (Gold already exists)
      1 — Silver or model file not found, or unexpected failure
    """
    logger.info(
        "Stage start: prediction | silver=%s | model=%s", silver_file, model_file
    )
    try:
        silver_path = Path(silver_file)
        model_path = Path(model_file)

        if not silver_path.exists():
            logger.error("Silver file not found: %s", silver_file)
            return 1
        if not model_path.exists():
            logger.error("Model file not found: %s", model_file)
            return 1

        run_date = date.today()
        date_str = run_date.strftime("%Y%m%d")
        Path(gold_dir).mkdir(parents=True, exist_ok=True)
        gold_path = Path(gold_dir) / f"CustomerChurnPrediction_{date_str}.parquet"

        # Idempotency guard (M3: key stability guaranteed here)
        if gold_path.exists():
            logger.warning(
                "Gold file already exists for %s — skipping prediction", date_str
            )
            logger.info("Stage end: prediction | idempotent=True")
            return 0

        silver = pd.read_parquet(silver_file)
        clf = joblib.load(model_file)

        X = silver[FEATURE_COLS].to_numpy(dtype=float)
        is_churn_predicted = clf.predict(X).astype(int)
        churn_probability = clf.predict_proba(X)[:, 1]

        gold = pd.DataFrame({
            "churn_prediction_key": [str(uuid.uuid4()) for _ in range(len(silver))],
            "customer_id": silver["customer_id"].values,
            "is_churn_predicted": is_churn_predicted,
            "churn_probability": churn_probability,
            "run_date": run_date,
            "model_version": model_path.name,
        })

        gold.to_parquet(gold_path, index=False)
        logger.info(
            "Stage end: prediction | predictions_written=%d | output=%s",
            len(gold),
            gold_path,
        )
        return 0

    except Exception:
        logger.exception("Unexpected failure in prediction stage")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish churn predictions to Gold")
    parser.add_argument("--silver-file", required=True)
    parser.add_argument("--model-file", required=True)
    parser.add_argument("--gold-dir", default="data/gold")
    args = parser.parse_args()
    sys.exit(predict(args.silver_file, args.model_file, args.gold_dir))


if __name__ == "__main__":
    main()
