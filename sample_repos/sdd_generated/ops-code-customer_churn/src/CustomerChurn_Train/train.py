import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.CustomerChurn_Train.features import build_features
from src.utils.logging_config import get_logger

logger = get_logger("customer_churn.train")


def train(
    silver_dir: str,
    model_dir: str = "models",
    random_seed: int = 42,
    test_split: float = 0.2,
) -> int:
    """
    Train a RandomForestClassifier on Silver data and log metrics to MLflow.

    Exit codes:
      0 — success
      1 — no Silver Parquet files found or unexpected failure
      4 — MLflow logging failed (model saved but metrics not persisted)
    """
    logger.info(
        "Stage start: training | silver_dir=%s | random_seed=%d", silver_dir, random_seed
    )
    try:
        silver_files = [
            f for f in Path(silver_dir).glob("*.parquet")
            if "ValidationReport" not in f.name
        ]
        if not silver_files:
            logger.error("No Silver Parquet files found in %s", silver_dir)
            return 1

        dfs = [pd.read_parquet(f) for f in silver_files]
        df = pd.concat(dfs, ignore_index=True)
        logger.info(
            "Loaded %d records from %d Silver file(s)", len(df), len(silver_files)
        )

        X, y = build_features(df)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_split, random_state=random_seed
        )

        logger.info(
            "Training start | train_size=%d | test_size=%d", len(X_train), len(X_test)
        )
        clf = RandomForestClassifier(random_state=random_seed)
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        y_proba = clf.predict_proba(X_test)[:, 1]

        metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "auc_roc": float(roc_auc_score(y_test, y_proba)),
        }
        for k, v in metrics.items():
            logger.info("Metric | %s=%.4f", k, v)

        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        Path(model_dir).mkdir(parents=True, exist_ok=True)
        model_path = Path(model_dir) / f"ChurnClassifier_{date_str}.joblib"
        joblib.dump(clf, model_path)

        try:
            mlflow.set_tracking_uri("mlruns")
            with mlflow.start_run():
                mlflow.log_params(
                    {
                        "random_seed": random_seed,
                        "test_split": test_split,
                        "n_estimators": clf.n_estimators,
                        "silver_record_count": len(df),
                    }
                )
                mlflow.log_metrics(metrics)
                mlflow.log_param("model_path", str(model_path))
                mlflow.set_tags({"run_date": date_str, "silver_dir": silver_dir})
        except Exception:
            logger.exception(
                "MLflow logging failed — model saved but metrics not persisted"
            )
            return 4

        logger.info("Stage end: training | model=%s", model_path)
        return 0

    except Exception:
        logger.exception("Unexpected failure in training stage")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Train churn classifier")
    parser.add_argument("--silver-dir", required=True)
    parser.add_argument("--model-dir", default="models")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--test-split", type=float, default=0.2)
    args = parser.parse_args()
    sys.exit(train(args.silver_dir, args.model_dir, args.random_seed, args.test_split))


if __name__ == "__main__":
    main()
