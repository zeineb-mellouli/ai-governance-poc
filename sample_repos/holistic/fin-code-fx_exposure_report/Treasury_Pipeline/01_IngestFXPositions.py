"""Ingest raw FX position data from the custodian feed and prepare it for reporting."""

import logging

import pandas as pd

logging.basicConfig(filename="logs/ingest.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    positions = pd.read_csv("bronze/FXPositions_20240630.csv")

    # normalise currency codes before this feeds the exposure report
    processed = positions.copy()
    processed["currency_code"] = processed["currency_code"].str.upper()

    processed.to_csv("staging/FXPositionsProcessed_20240630.csv", index=False)
    logger.info("Ingested and normalised %d FX position rows", len(processed))


if __name__ == "__main__":
    main()
