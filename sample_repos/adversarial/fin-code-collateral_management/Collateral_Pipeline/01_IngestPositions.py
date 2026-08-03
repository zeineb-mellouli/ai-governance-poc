"""Bronze -> Silver: ingest raw collateral positions, do not mutate bronze."""

import logging

import pandas as pd

logging.basicConfig(filename="logs/ingest.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    positions = pd.read_csv("bronze/CollateralPositions_20240815.csv")

    assert positions["required_collateral"].ge(0).all(), "negative required_collateral"
    assert not positions.duplicated(subset=["counterparty_id"]).any(), "duplicate counterparty rows"

    positions.to_csv("silver/CollateralPositions_validated_20240815.csv", index=False)
    logger.info("Ingested and validated %d collateral positions", len(positions))


if __name__ == "__main__":
    main()
