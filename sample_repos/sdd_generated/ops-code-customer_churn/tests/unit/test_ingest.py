import pandas as pd
import pytest

from src.CustomerChurn_Ingest.ingest import ingest

VALID_CSV = (
    "customer_id,full_name,email,phone_number,"
    "account_tenure_months,monthly_usage_hours,is_churned\n"
    "C001,Alice Smith,alice@example.com,555-0001,12.0,8.5,0\n"
    "C002,Bob Jones,bob@example.com,555-0002,3.0,1.2,1\n"
)

HEADER_ONLY_CSV = (
    "customer_id,full_name,email,phone_number,"
    "account_tenure_months,monthly_usage_hours,is_churned\n"
)

WRONG_SCHEMA_CSV = "id,name,email\nC001,Alice,alice@example.com\n"


@pytest.fixture
def dirs(tmp_path):
    landing = tmp_path / "landing"
    landing.mkdir()
    bronze = tmp_path / "bronze"
    bronze.mkdir()
    return landing, bronze


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_copies_all_rows_and_adds_metadata(dirs):
    landing, bronze = dirs
    csv = landing / "CustomerChurn_20260714.csv"
    csv.write_text(VALID_CSV)

    assert ingest(str(csv), str(bronze)) == 0

    parquet = bronze / "CustomerChurn_20260714.parquet"
    assert parquet.exists()
    df = pd.read_parquet(parquet)
    assert len(df) == 2
    assert "ingested_at" in df.columns
    assert "source_file" in df.columns
    assert df["source_file"].iloc[0] == "CustomerChurn_20260714.csv"
    # PII retained in Bronze (source of truth)
    assert "full_name" in df.columns
    assert "email" in df.columns


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------

def test_idempotent_rerun_writes_no_additional_rows(dirs):
    landing, bronze = dirs
    csv = landing / "CustomerChurn_20260714.csv"
    csv.write_text(VALID_CSV)

    ingest(str(csv), str(bronze))
    code = ingest(str(csv), str(bronze))

    assert code == 0
    df = pd.read_parquet(bronze / "CustomerChurn_20260714.parquet")
    assert len(df) == 2  # still 2, not 4


# ---------------------------------------------------------------------------
# Error paths (exit 1)
# ---------------------------------------------------------------------------

def test_missing_source_file_exits_1(dirs):
    _, bronze = dirs
    assert ingest("/nonexistent/CustomerChurn_20260714.csv", str(bronze)) == 1


def test_wrong_column_schema_exits_1_and_writes_no_bronze(dirs):
    landing, bronze = dirs
    csv = landing / "CustomerChurn_20260714.csv"
    csv.write_text(WRONG_SCHEMA_CSV)

    assert ingest(str(csv), str(bronze)) == 1
    assert not (bronze / "CustomerChurn_20260714.parquet").exists()


# ---------------------------------------------------------------------------
# Empty-file guard (M2) — exit 0, zero records written
# ---------------------------------------------------------------------------

def test_empty_csv_exits_0_and_writes_no_bronze(dirs):
    landing, bronze = dirs
    csv = landing / "CustomerChurn_20260714.csv"
    csv.write_text(HEADER_ONLY_CSV)

    assert ingest(str(csv), str(bronze)) == 0
    assert not (bronze / "CustomerChurn_20260714.parquet").exists()
