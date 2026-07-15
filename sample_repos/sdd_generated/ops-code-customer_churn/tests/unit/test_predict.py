import re

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from src.CustomerChurn_Predict.predict import predict

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


@pytest.fixture
def silver_file(tmp_path):
    df = pd.DataFrame({
        "customer_id": ["C001", "C002", "C003"],
        "account_tenure_months": [12.0, 3.0, 24.0],
        "monthly_usage_hours": [8.5, 1.2, 20.0],
        "is_churned": [0, 1, 0],
        "validated_at": ["2026-07-14T10:00:00+00:00"] * 3,
        "batch_id": ["abc123"] * 3,
    })
    path = tmp_path / "silver" / "CustomerChurn_20260714.parquet"
    path.parent.mkdir(parents=True)
    df.to_parquet(path, index=False)
    return path


@pytest.fixture
def model_file(tmp_path):
    X = np.array([[12.0, 8.5], [3.0, 1.2], [24.0, 20.0]])
    y = np.array([0, 1, 0])
    clf = RandomForestClassifier(random_state=42, n_estimators=10)
    clf.fit(X, y)
    path = tmp_path / "models" / "ChurnClassifier_20260714.joblib"
    path.parent.mkdir(parents=True)
    joblib.dump(clf, path)
    return path


@pytest.fixture
def gold_dir(tmp_path):
    d = tmp_path / "gold"
    d.mkdir()
    return d


def _load_gold(gold_dir):
    files = list(gold_dir.glob("*.parquet"))
    assert len(files) == 1, "Expected exactly one Gold Parquet file"
    return pd.read_parquet(files[0])


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_one_row_per_customer(silver_file, model_file, gold_dir):
    assert predict(str(silver_file), str(model_file), str(gold_dir)) == 0
    gold = _load_gold(gold_dir)
    assert len(gold) == 3
    assert gold["customer_id"].nunique() == 3


def test_churn_prediction_key_is_valid_uuid(silver_file, model_file, gold_dir):
    predict(str(silver_file), str(model_file), str(gold_dir))
    gold = _load_gold(gold_dir)
    assert gold["churn_prediction_key"].notna().all()
    for key in gold["churn_prediction_key"]:
        assert UUID_RE.match(str(key)), f"Not a valid UUID: {key}"


def test_is_churn_predicted_is_binary(silver_file, model_file, gold_dir):
    predict(str(silver_file), str(model_file), str(gold_dir))
    gold = _load_gold(gold_dir)
    assert gold["is_churn_predicted"].isin([0, 1]).all()


def test_churn_probability_in_unit_interval(silver_file, model_file, gold_dir):
    predict(str(silver_file), str(model_file), str(gold_dir))
    gold = _load_gold(gold_dir)
    assert gold["churn_probability"].between(0.0, 1.0).all()


# ---------------------------------------------------------------------------
# Idempotency guard
# ---------------------------------------------------------------------------

def test_idempotent_rerun_exits_0_without_overwriting(silver_file, model_file, gold_dir):
    predict(str(silver_file), str(model_file), str(gold_dir))
    gold_file = list(gold_dir.glob("*.parquet"))[0]
    mtime_before = gold_file.stat().st_mtime

    code = predict(str(silver_file), str(model_file), str(gold_dir))
    assert code == 0
    assert gold_file.stat().st_mtime == mtime_before


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_missing_silver_exits_1(model_file, gold_dir):
    assert predict("/nonexistent/silver.parquet", str(model_file), str(gold_dir)) == 1


def test_missing_model_exits_1(silver_file, gold_dir):
    assert predict(str(silver_file), "/nonexistent/model.joblib", str(gold_dir)) == 1
