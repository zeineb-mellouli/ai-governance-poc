"""Build the quarterly FX exposure report for the Treasury board pack."""

import logging
from pathlib import Path

import pandas as pd

Path("logs").mkdir(parents=True, exist_ok=True)
Path("gold").mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename="logs/report.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    positions = pd.read_csv("staging/FXPositionsProcessed_20240630.csv")

    report = (
        positions.groupby("currency_code")["notional_local"]
        .sum()
        .reset_index()
        .rename(columns={"notional_local": "total_exposure"})
    )

    report.to_csv("gold/QuarterlyFXExposureReport.csv", index=False)
    logger.info("Quarterly FX exposure report written for %d currencies", len(report))


if __name__ == "__main__":
    main()
