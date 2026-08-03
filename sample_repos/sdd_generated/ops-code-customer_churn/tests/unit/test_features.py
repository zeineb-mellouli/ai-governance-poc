import numpy as np
import pandas as pd
import pytest

from src.CustomerChurn_Train.features import build_features


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "customer_id": ["C001", "C002", "C003"],
        "account_tenure_months": [12.0, 3.0, 24.0],
        "monthly_usage_hours": [8.5, 1.2, 20.0],
        "is_churned": [0, 1, 0],
        "validated_at": ["2026-07-14T10:00:00+00:00"] * 3,
        "batch_id": ["abc"] * 3,
    })


def test_feature_matrix_shape(sample_df):
    X, y = build_features(sample_df)
    assert X.shape == (3, 2)


def test_feature_column_order(sample_df):
    X, _ = build_features(sample_df)
    np.testing.assert_array_equal(
        X[:, 0], sample_df["account_tenure_months"].to_numpy()
    )
    np.testing.assert_array_equal(
        X[:, 1], sample_df["monthly_usage_hours"].to_numpy()
    )


def test_label_vector_equals_is_churned(sample_df):
    _, y = build_features(sample_df)
    np.testing.assert_array_equal(y, sample_df["is_churned"].to_numpy())


def test_row_counts_match(sample_df):
    X, y = build_features(sample_df)
    assert X.shape[0] == len(y) == len(sample_df)


def test_raises_on_missing_columns():
    df = pd.DataFrame({"customer_id": ["C001"], "account_tenure_months": [5.0]})
    with pytest.raises(ValueError, match="Missing required columns"):
        build_features(df)
