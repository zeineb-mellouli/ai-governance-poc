import json
from pathlib import Path

import pandas as pd
import pytest

from src.CustomerChurn_Validate.validate import validate

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID = [
    {"customer_id": "C001", "full_name": "Alice Smith", "email": "alice@example.com",
     "phone_number": "555-0001", "account_tenure_months": 12.0,
     "monthly_usage_hours": 8.5, "is_churned": 0},
    {"customer_id": "C002", "full_name": "Bob Jones", "email": "bob@example.com",
     "phone_number": "555-0002", "account_tenure_months": 3.0,
     "monthly_usage_hours": 1.2, "is_churned": 1},
    {"customer_id": "C003", "full_name": "Carol Lee", "email": "carol@example.com",
     "phone_number": "555-0003", "account_tenure_months": 24.0,
     "monthly_usage_hours": 20.0, "is_churned": 0},
]

INVALID = [
    # Duplicate customer_id — both occurrences must be rejected
    {"customer_id": "C004", "full_name": "Dan Brown", "email": "dan@example.com",
     "phone_number": "555-0004", "account_tenure_months": 5.0,
     "monthly_usage_hours": 3.0, "is_churned": 0},
    {"customer_id": "C004", "full_name": "Dan Brown", "email": "dan@example.com",
     "phone_number": "555-0004", "account_tenure_months": 5.0,
     "monthly_usage_hours": 3.0, "is_churned": 0},
    # Negative account_tenure_months
    {"customer_id": "C005", "full_name": "Eve White", "email": "eve@example.com",
     "phone_number": "555-0005", "account_tenure_months": -1.0,
     "monthly_usage_hours": 5.0, "is_churned": 0},
    # Negative monthly_usage_hours
    {"customer_id": "C006", "full_name": "Frank Green", "email": "frank@example.com",
     "phone_number": "555-0006", "account_tenure_months": 10.0,
     "monthly_usage_hours": -3.0, "is_churned": 1},
    # Missing required field (account_tenure_months is None)
    {"customer_id": "C007", "full_name": "Grace Hill", "email": "grace@example.com",
     "phone_number": "555-0007", "account_tenure_months": None,
     "monthly_usage_hours": 7.0, "is_churned": 0},
]


def _make_bronze(tmp_path, records):
    df = pd.DataFrame(records)
    df["ingested_at"] = "2026-07-14T10:00:00+00:00"
    df["source_file"] = "CustomerChurn_20260714.parquet"
    bronze = tmp_path / "bronze" / "CustomerChurn_20260714.parquet"
    bronze.parent.mkdir(parents=True)
    df.to_parquet(bronze, index=False)
    return bronze


@pytest.fixture
def bronze_file(tmp_path):
    return _make_bronze(tmp_path, VALID + INVALID)


@pytest.fixture
def silver_dir(tmp_path):
    d = tmp_path / "silver"
    d.mkdir()
    return d


# ---------------------------------------------------------------------------
# PII removal
# ---------------------------------------------------------------------------

def test_pii_columns_absent_from_silver(bronze_file, silver_dir):
    assert validate(str(bronze_file), str(silver_dir)) == 0
    silver = pd.read_parquet(silver_dir / "CustomerChurn_20260714.parquet")
    for col in ("full_name", "email", "phone_number"):
        assert col not in silver.columns, f"{col} must not appear in Silver"


# ---------------------------------------------------------------------------
# Accepted records
# ---------------------------------------------------------------------------

def test_only_valid_records_reach_silver(bronze_file, silver_dir):
    validate(str(bronze_file), str(silver_dir))
    silver = pd.read_parquet(silver_dir / "CustomerChurn_20260714.parquet")
    assert len(silver) == len(VALID)
    assert set(silver["customer_id"]) == {"C001", "C002", "C003"}


# ---------------------------------------------------------------------------
# Rejection rules
# ---------------------------------------------------------------------------

def test_all_occurrences_of_duplicate_id_rejected(bronze_file, silver_dir):
    validate(str(bronze_file), str(silver_dir))
    silver = pd.read_parquet(silver_dir / "CustomerChurn_20260714.parquet")
    assert "C004" not in silver["customer_id"].values


def test_negative_tenure_rejected(bronze_file, silver_dir):
    validate(str(bronze_file), str(silver_dir))
    silver = pd.read_parquet(silver_dir / "CustomerChurn_20260714.parquet")
    assert "C005" not in silver["customer_id"].values


def test_negative_usage_rejected(bronze_file, silver_dir):
    validate(str(bronze_file), str(silver_dir))
    silver = pd.read_parquet(silver_dir / "CustomerChurn_20260714.parquet")
    assert "C006" not in silver["customer_id"].values


def test_missing_required_field_rejected(bronze_file, silver_dir):
    validate(str(bronze_file), str(silver_dir))
    silver = pd.read_parquet(silver_dir / "CustomerChurn_20260714.parquet")
    assert "C007" not in silver["customer_id"].values


# ---------------------------------------------------------------------------
# ValidationReport
# ---------------------------------------------------------------------------

def test_report_counts_are_correct(bronze_file, silver_dir):
    validate(str(bronze_file), str(silver_dir))
    report = json.loads((silver_dir / "ValidationReport_20260714.json").read_text())
    assert report["total_records"] == len(VALID) + len(INVALID)
    assert report["accepted_count"] == len(VALID)
    assert report["rejected_count"] == len(INVALID)


def test_report_contains_no_pii_values(bronze_file, silver_dir):
    validate(str(bronze_file), str(silver_dir))
    report_text = (silver_dir / "ValidationReport_20260714.json").read_text()
    for pii in ("alice", "bob", "carol", "dan", "eve", "frank", "grace",
                "example.com", "555-"):
        assert pii not in report_text.lower(), f"PII value '{pii}' found in report"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_all_rejected_exits_3_and_no_silver_written(tmp_path):
    bronze = _make_bronze(tmp_path, [
        {"customer_id": "X001", "full_name": "A", "email": "a@b.com",
         "phone_number": "555-9999", "account_tenure_months": -1.0,
         "monthly_usage_hours": 5.0, "is_churned": 0},
    ])
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()

    assert validate(str(bronze), str(silver_dir)) == 3
    assert not (silver_dir / "CustomerChurn_20260714.parquet").exists()
    assert (silver_dir / "ValidationReport_20260714.json").exists()


def test_empty_bronze_exits_0_and_no_silver_written(tmp_path):
    df = pd.DataFrame(columns=[
        "customer_id", "full_name", "email", "phone_number",
        "account_tenure_months", "monthly_usage_hours", "is_churned",
        "ingested_at", "source_file",
    ])
    bronze = tmp_path / "CustomerChurn_20260714.parquet"
    df.to_parquet(bronze, index=False)
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()

    assert validate(str(bronze), str(silver_dir)) == 0
    assert not (silver_dir / "CustomerChurn_20260714.parquet").exists()


def test_bronze_not_found_exits_1(tmp_path):
    silver_dir = tmp_path / "silver"
    silver_dir.mkdir()
    assert validate("/nonexistent/CustomerChurn_20260714.parquet", str(silver_dir)) == 1
