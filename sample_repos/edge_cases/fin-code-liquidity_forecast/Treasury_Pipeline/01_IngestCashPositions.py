"""Bronze -> Silver: load raw bank balances and cash movements, do not mutate bronze."""

import logging

import pandas as pd

logging.basicConfig(filename="logs/ingest.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting ingest run")
    try:
        balances = pd.read_csv("bronze/BankAccountBalances_20240701.csv")
        movements = pd.read_csv("bronze/DailyCashMovements_2024-07-01.csv")

        balances.to_csv("silver/BankAccountBalances_20240701.csv", index=False)
        movements.to_csv("silver/DailyCashMovements_20240701.csv", index=False)
        logger.info("Ingest run complete: %d balance rows, %d movement rows", len(balances), len(movements))
    except Exception:
        logger.exception("Ingest run failed")
        raise


if __name__ == "__main__":
    main()
