"""
tests/conftest.py
------------------
Shared pytest fixtures for the Polymer Pricing ETL Pipeline test suite.
Available to all tests in tests/unit/ and tests/integration/.
"""

from pathlib import Path

import pandas as pd
import pytest


_HAPPY_PATH_ROWS = """\
material_code,pricing_date,price_value,unit_of_measure,currency_code
PE-HD-001,2026-07-13,1250.50,MT,USD
PP-HOM-002,2026-07-13,1180.00,MT,USD
PET-BG-003,2026-07-13,875.25,MT,EUR
PVC-SUS-004,2026-07-13,950.75,MT,USD
PA-6-005,2026-07-13,2400.00,MT,EUR
"""


@pytest.fixture()
def sample_landing_csv(tmp_path: Path) -> Path:
    """Write the 5-row happy-path source CSV to tmp_path and return its Path.

    File name matches the convention: PolymerPricing_yyyyMMdd.csv
    """
    csv_path = tmp_path / "PolymerPricing_20260713.csv"
    csv_path.write_text(_HAPPY_PATH_ROWS, encoding="utf-8")
    return csv_path


@pytest.fixture()
def sample_bronze_df() -> pd.DataFrame:
    """5-row DataFrame matching the bronze layer contract (7 columns).

    price_value is float64; pricing_date and ingestion_timestamp are str
    (as they are immediately after reading the source CSV and appending metadata).
    """
    return pd.DataFrame(
        {
            "material_code": [
                "PE-HD-001", "PP-HOM-002", "PET-BG-003", "PVC-SUS-004", "PA-6-005"
            ],
            "pricing_date": ["2026-07-13"] * 5,
            "price_value": [1250.50, 1180.00, 875.25, 950.75, 2400.00],
            "unit_of_measure": ["MT"] * 5,
            "currency_code": ["USD", "USD", "EUR", "USD", "EUR"],
            "source_file_name": ["PolymerPricing_20260713.csv"] * 5,
            "ingestion_timestamp": ["2026-07-13T06:00:00+00:00"] * 5,
        }
    )


@pytest.fixture()
def sample_silver_df() -> pd.DataFrame:
    """5-row DataFrame matching the silver layer contract (7 columns, typed dtypes).

    pricing_date and ingestion_timestamp are datetime64[ns] as required by
    SilverSchema and GoldSchema.
    """
    return pd.DataFrame(
        {
            "material_code": [
                "PE-HD-001", "PP-HOM-002", "PET-BG-003", "PVC-SUS-004", "PA-6-005"
            ],
            "pricing_date": pd.to_datetime(["2026-07-13"] * 5),
            "price_value": [1250.50, 1180.00, 875.25, 950.75, 2400.00],
            "unit_of_measure": ["MT"] * 5,
            "currency_code": ["USD", "USD", "EUR", "USD", "EUR"],
            "source_file_name": ["PolymerPricing_20260713.csv"] * 5,
            "ingestion_timestamp": pd.to_datetime(["2026-07-13T06:00:00"] * 5),
        }
    )
