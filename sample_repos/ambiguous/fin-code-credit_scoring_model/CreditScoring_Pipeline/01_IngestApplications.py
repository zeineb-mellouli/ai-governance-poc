"""Bronze -> Silver: ingest and validate raw credit applications."""

import logging

import pandas as pd

logging.basicConfig(filename="logs/ingest.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    applications = pd.read_csv("bronze/CreditApplications_20240901.csv")

    assert applications["annual_income"].ge(0).all(), "negative annual_income"
    assert not applications.duplicated(subset=["application_id"]).any(), "duplicate application rows"
    assert applications["defaulted"].isin([0, 1]).all(), "defaulted must be 0 or 1"

    applications.to_csv("silver/CreditApplications_validated_20240901.csv", index=False)
    logger.info("Ingested and validated %d credit applications", len(applications))


if __name__ == "__main__":
    main()
