import numpy as np
import pandas as pd


def build_features(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Extract feature matrix X and label vector y from a Silver DataFrame.

    Feature columns (in order):
      - account_tenure_months
      - monthly_usage_hours

    Label:
      - is_churned (binary: 0 or 1)

    Returns:
        X: np.ndarray of shape (n, 2)
        y: np.ndarray of shape (n,)

    Raises:
        ValueError: if any required column is absent from df.
    """
    required = {"account_tenure_months", "monthly_usage_hours", "is_churned"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns for feature engineering: {sorted(missing)}"
        )

    X = df[["account_tenure_months", "monthly_usage_hours"]].to_numpy(dtype=float)
    y = df["is_churned"].to_numpy(dtype=int)
    return X, y
