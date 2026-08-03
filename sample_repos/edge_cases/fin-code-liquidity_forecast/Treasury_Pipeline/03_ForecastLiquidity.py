"""Silver -> Gold: project each bank account's balance forward 30 days."""

import logging

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

logging.basicConfig(filename="logs/forecast.log", level=logging.INFO)
logger = logging.getLogger(__name__)

RANDOM_STATE = 42


def main() -> None:
    np.random.seed(RANDOM_STATE)
    movements = pd.read_csv("silver/DailyCashMovements_validated_20240701.csv")

    X = movements[["amount"]].shift(1).fillna(0).values
    y = movements["amount"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=RANDOM_STATE)
    model = LinearRegression()
    model.fit(X_train, y_train)
    logger.info("Model trained, R^2=%.3f", model.score(X_test, y_test))

    forecast = (
        movements.groupby("bank_account_id")["amount"]
        .agg(avg_daily_net_flow="mean")
        .reset_index()
    )
    forecast["projected_balance_30d"] = forecast["avg_daily_net_flow"] * 30
    forecast.to_csv("gold/LiquidityForecast_20240701.csv", index=False)
    logger.info("Gold forecast written: %d accounts", len(forecast))


if __name__ == "__main__":
    main()
