"""Train the credit scoring model used to grade new credit applications."""

import logging

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

logging.basicConfig(filename="logs/train.log", level=logging.INFO)
logger = logging.getLogger(__name__)

# Global seed set once for the whole run -- every stochastic step in this
# script relies on this rather than passing random_state to each call.
np.random.seed(42)


def main() -> None:
    applications = pd.read_csv("silver/CreditApplications_validated_20240901.csv")

    feature_cols = ["annual_income", "existing_debt", "credit_history_months"]
    X = applications[feature_cols].values
    y = applications["defaulted"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = LogisticRegression()
    model.fit(X_train, y_train)
    logger.info("Model trained, accuracy=%.3f", model.score(X_test, y_test))

    applications["credit_score"] = model.predict_proba(applications[feature_cols].values)[:, 1]
    applications.to_csv("gold/CreditScoringResults_20240901.csv", index=False)


if __name__ == "__main__":
    main()
