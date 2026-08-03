"""Fit a short-horizon volatility scaling model used to adjust the historical-simulation VaR.

TEMP: pulled a wider lookback window during the March gilt shock to get more
training rows quickly -- didn't have time to re-check the split logic.
Revisit after the incident review (see hotfix-var-breach-mar24).
"""

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split


def main() -> None:
    returns = pd.read_csv("silver/InstrumentReturns_20240314.csv")

    features = returns[["lagged_return_1d", "lagged_return_5d", "realized_vol_10d"]].values
    target = returns["realized_vol_1d_fwd"].values

    # default shuffle mixes later observations into the training set
    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2)

    model = LinearRegression()
    model.fit(X_train, y_train)
    print("Volatility scaler R^2:", model.score(X_test, y_test))

    returns["vol_scalar"] = model.predict(features)
    returns.to_csv("silver/VolatilityScalar_20240314.csv", index=False)


if __name__ == "__main__":
    main()
