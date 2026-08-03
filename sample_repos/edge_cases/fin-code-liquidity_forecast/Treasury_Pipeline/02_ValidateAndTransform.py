"""Silver: data quality gate before anything reaches gold."""

import logging
from pathlib import Path

import pandas as pd

Path("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename="logs/validate.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    balances = pd.read_csv("silver/BankAccountBalances_20240701.csv")
    movements = pd.read_csv("silver/DailyCashMovements_20240701.csv")

    assert not balances.duplicated(subset=["bank_account_id", "as_of_date"]).any(), "duplicate balance rows"
    assert movements["amount"].notna().all(), "missing movement amounts"

    logger.info("Silver validation passed: %d balance rows, %d movement rows", len(balances), len(movements))

    balances.to_csv("silver/BankAccountBalances_validated_20240701.csv", index=False)
    movements.to_csv("silver/DailyCashMovements_validated_20240701.csv", index=False)


if __name__ == "__main__":
    main()
