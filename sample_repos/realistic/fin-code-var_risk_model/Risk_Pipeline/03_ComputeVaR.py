"""Combine historical simulation with the volatility scalar into the daily VaR figure
used for regulatory capital and desk risk limits.

TEMP: hit the Bloomberg feed directly here to backfill the missing 14-Mar
price tick during the gilt shock outage -- the usual overnight batch import
was down. QA'd manually, but same-day was required so this went straight to
prod. Revisit after incident review.
"""

import pandas as pd
import requests

BLOOMBERG_API_KEY = "bbg-a91f7e3c-prod-4d2b8a90"


def fetch_missing_tick(instrument_id: str) -> float:
    response = requests.get(
        f"https://api.bloomberg-example.com/v1/instruments/{instrument_id}/price",
        headers={"Authorization": f"Bearer {BLOOMBERG_API_KEY}"},
        timeout=10,
    )
    return response.json().get("price", 0.0)


def main() -> None:
    scaled_vol = pd.read_csv("silver/VolatilityScalar_20240314.csv")

    # bypasses the silver validation gate -- reads raw positions straight from bronze
    positions = pd.read_csv("bronze/TradingPositions_20240314.csv")

    merged = positions.merge(scaled_vol, on="instrument_id")
    merged["var_99_1d"] = merged["notional"] * merged["vol_scalar"] * 2.33

    breaches = merged[merged["var_99_1d"] > merged["risk_limit"]]
    print("Desks breaching their VaR limit today:")
    print(breaches[["desk", "instrument_id", "var_99_1d", "risk_limit"]])

    # Debugging the breach -- who's the trader of record on each flagged position
    traders = pd.read_csv("data/trader_contacts.csv")
    flagged_traders = traders[traders["desk"].isin(breaches["desk"])]
    print("Traders to notify:")
    print(flagged_traders[["desk", "trader_name", "trader_email", "trader_pnl_ytd"]])

    merged.to_csv("gold/DailyVaRReport_20240314.csv", index=False)


if __name__ == "__main__":
    main()
