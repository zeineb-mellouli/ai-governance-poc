"""Bronze -> Silver: ingest market data and build the return features the vol model trains on."""

import logging
from pathlib import Path

import pandas as pd

Path("logs").mkdir(parents=True, exist_ok=True)
Path("silver").mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename="logs/ingest.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    market_data = pd.read_csv("bronze/MarketDataFeed_20240314.csv")

    assert market_data["price"].gt(0).all(), "non-positive price detected"
    assert not market_data.duplicated(subset=["instrument_id", "price_date"]).any(), "duplicate price rows"

    returns = market_data.sort_values("price_date").copy()
    returns["lagged_return_1d"] = returns.groupby("instrument_id")["price"].pct_change(1)
    returns["lagged_return_5d"] = returns.groupby("instrument_id")["price"].pct_change(5)
    returns["realized_vol_10d"] = returns.groupby("instrument_id")["lagged_return_1d"].transform(
        lambda s: s.rolling(3).std()
    )
    returns["realized_vol_1d_fwd"] = returns.groupby("instrument_id")["lagged_return_1d"].shift(-1)
    returns = returns.dropna()

    returns.to_csv("silver/InstrumentReturns_20240314.csv", index=False)
    logger.info("Ingested %d market data rows, %d feature rows", len(market_data), len(returns))


if __name__ == "__main__":
    main()
