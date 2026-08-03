"""Check upcoming regulatory filing deadlines and flag anything within its notice window."""

import logging
from datetime import date
from pathlib import Path

import pandas as pd

Path("logs").mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename="logs/deadline_check.log", level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    deadlines = pd.read_csv("data/RegulatoryFilingDeadlines_20240901.csv", parse_dates=["deadline_date"])

    assert deadlines["deadline_date"].notna().all(), "missing deadline_date values"
    assert not deadlines.duplicated(subset=["filing_id"]).any(), "duplicate filing_id rows"

    today = pd.Timestamp(date.today())
    deadlines["days_until_due"] = (deadlines["deadline_date"] - today).dt.days
    due_soon = deadlines[deadlines["days_until_due"] <= deadlines["days_notice_required"]]

    logger.info("%d filings due within their notice window", len(due_soon))
    due_soon.to_csv("data/UpcomingFilingAlerts_20240901.csv", index=False)


if __name__ == "__main__":
    main()
