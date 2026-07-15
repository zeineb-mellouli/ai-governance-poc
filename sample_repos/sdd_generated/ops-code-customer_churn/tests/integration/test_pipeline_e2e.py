"""
End-to-end integration test using the project fixture file.

Requires:
    data/landing/CustomerChurn_20260714.csv  (30 rows: 25 valid + 5 invalid)

Run from repo root:
    pytest tests/integration/
"""
import re
from datetime import datetime
from pathlib import Path

import mlflow
import pandas as pd
import pytest

from src.CustomerChurn_Ingest.ingest import ingest
from src.CustomerChurn_Validate.validate import validate
from src.CustomerChurn_Train.train import train
from src.CustomerChurn_Predict.predict import predict

FIXTURE = "data/landing/CustomerChurn_20260714.csv"
FIXTURE_DATE = "20260714"
RANDOM_SEED = 42

PII_PATTERN = re.compile(
    r"(jordan|priya|marcus|sofia|kwame|elin|ravi|nora|tomas|aisha|"
    r"alex|dana|sam|@example\.com|555-01)",
    re.IGNORECASE,
)


@pytest.fixture(scope="module")
def pipeline_outputs(tmp_path_factory):
    """Run the full pipeline once per test module; return output paths."""
    if not Path(FIXTURE).exists():
        pytest.skip(f"Fixture file not found: {FIXTURE}")

    tmp = tmp_path_factory.mktemp("e2e")
    bronze_dir = str(tmp / "bronze")
    silver_dir = str(tmp / "silver")
    model_dir = str(tmp / "models")
    gold_dir = str(tmp / "gold")
    log_dir = str(tmp / "logs")

    for d in (bronze_dir, silver_dir, model_dir, gold_dir, log_dir):
        Path(d).mkdir(parents=True, exist_ok=True)

    mlflow_dir = str(tmp / "mlruns")
    mlflow.set_tracking_uri(mlflow_dir)

    assert ingest(FIXTURE, bronze_dir) == 0
    assert validate(
        f"{bronze_dir}/CustomerChurn_{FIXTURE_DATE}.parquet", silver_dir
    ) == 0
    assert train(silver_dir, model_dir, RANDOM_SEED) == 0

    today = datetime.now().strftime("%Y%m%d")
    assert predict(
        f"{silver_dir}/CustomerChurn_{FIXTURE_DATE}.parquet",
        f"{model_dir}/ChurnClassifier_{today}.joblib",
        gold_dir,
    ) == 0

    return {
        "bronze_dir": Path(bronze_dir),
        "silver_dir": Path(silver_dir),
        "model_dir": Path(model_dir),
        "gold_dir": Path(gold_dir),
        "log_dir": Path(log_dir),
        "mlruns_dir": mlflow_dir,
        "today": today,
    }


# ---------------------------------------------------------------------------
# Bronze
# ---------------------------------------------------------------------------

def test_bronze_has_30_rows(pipeline_outputs):
    df = pd.read_parquet(
        pipeline_outputs["bronze_dir"] / f"CustomerChurn_{FIXTURE_DATE}.parquet"
    )
    assert len(df) == 30


# ---------------------------------------------------------------------------
# Silver
# ---------------------------------------------------------------------------

def test_silver_has_25_rows(pipeline_outputs):
    df = pd.read_parquet(
        pipeline_outputs["silver_dir"] / f"CustomerChurn_{FIXTURE_DATE}.parquet"
    )
    assert len(df) == 25


def test_silver_contains_no_pii_columns(pipeline_outputs):
    df = pd.read_parquet(
        pipeline_outputs["silver_dir"] / f"CustomerChurn_{FIXTURE_DATE}.parquet"
    )
    for col in ("full_name", "email", "phone_number"):
        assert col not in df.columns, f"PII column '{col}' must not appear in Silver"


def test_invalid_customer_ids_absent_from_silver(pipeline_outputs):
    df = pd.read_parquet(
        pipeline_outputs["silver_dir"] / f"CustomerChurn_{FIXTURE_DATE}.parquet"
    )
    for bad_id in ("CUST-10026", "CUST-10027", "CUST-10028", "CUST-10029"):
        assert bad_id not in df["customer_id"].values


# ---------------------------------------------------------------------------
# Gold
# ---------------------------------------------------------------------------

def test_gold_has_25_rows(pipeline_outputs):
    today = pipeline_outputs["today"]
    df = pd.read_parquet(
        pipeline_outputs["gold_dir"] / f"CustomerChurnPrediction_{today}.parquet"
    )
    assert len(df) == 25


def test_gold_has_no_duplicate_customer_ids(pipeline_outputs):
    today = pipeline_outputs["today"]
    df = pd.read_parquet(
        pipeline_outputs["gold_dir"] / f"CustomerChurnPrediction_{today}.parquet"
    )
    assert df["customer_id"].nunique() == 25


def test_gold_prediction_keys_are_non_null_and_unique(pipeline_outputs):
    today = pipeline_outputs["today"]
    df = pd.read_parquet(
        pipeline_outputs["gold_dir"] / f"CustomerChurnPrediction_{today}.parquet"
    )
    assert df["churn_prediction_key"].notna().all()
    assert df["churn_prediction_key"].nunique() == 25


def test_gold_binary_predictions(pipeline_outputs):
    today = pipeline_outputs["today"]
    df = pd.read_parquet(
        pipeline_outputs["gold_dir"] / f"CustomerChurnPrediction_{today}.parquet"
    )
    assert df["is_churn_predicted"].isin([0, 1]).all()
    assert df["churn_probability"].between(0.0, 1.0).all()


# ---------------------------------------------------------------------------
# PII audit
# ---------------------------------------------------------------------------

def test_no_pii_in_log_files(pipeline_outputs):
    for log_file in pipeline_outputs["log_dir"].glob("*.log"):
        content = log_file.read_text()
        match = PII_PATTERN.search(content)
        assert match is None, (
            f"PII value {match.group()!r} found in {log_file.name}"
        )


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------

def test_two_training_runs_produce_identical_metrics(pipeline_outputs):
    mlflow.set_tracking_uri(pipeline_outputs["mlruns_dir"])

    # Run training a second time
    train(
        str(pipeline_outputs["silver_dir"]),
        str(pipeline_outputs["model_dir"]),
        RANDOM_SEED,
    )

    runs = mlflow.search_runs().sort_values("start_time").reset_index(drop=True)
    assert len(runs) >= 2, "Expected at least 2 MLflow runs"

    first = runs.iloc[-2]
    second = runs.iloc[-1]

    for metric in ("metrics.accuracy", "metrics.precision",
                   "metrics.recall", "metrics.auc_roc"):
        assert first[metric] == second[metric], (
            f"Metric {metric} differs across runs: {first[metric]} vs {second[metric]}"
        )
