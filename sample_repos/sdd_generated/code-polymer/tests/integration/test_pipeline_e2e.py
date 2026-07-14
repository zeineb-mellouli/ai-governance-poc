"""
tests/integration/test_pipeline_e2e.py
----------------------------------------
End-to-end integration tests for the full Polymer Pricing ETL pipeline.
Requires a live Azure SQL Server connection and all 9 env vars set.

Run with:
    pytest tests/integration/ -v -m integration

Skip in CI (no DB):
    pytest tests/unit/ -v -m "not integration"
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import sqlalchemy
import urllib.parse

# Mark all tests in this module as requiring a live DB
pytestmark = pytest.mark.integration

_REPO_ROOT = Path(__file__).parent.parent.parent
_DB_ENV_VARS = ("SQL_SERVER", "SQL_DATABASE", "SQL_USERNAME", "SQL_PASSWORD")


def _db_available() -> bool:
    return all(os.environ.get(v, "").strip() for v in _DB_ENV_VARS)


def _skip_if_no_db():
    if not _db_available():
        pytest.skip("Integration test skipped: Azure SQL env vars not set")


def _build_engine() -> sqlalchemy.engine.Engine:
    driver = "ODBC Driver 17 for SQL Server"
    odbc_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={os.environ['SQL_SERVER']};"
        f"DATABASE={os.environ['SQL_DATABASE']};"
        f"UID={os.environ['SQL_USERNAME']};"
        f"PWD={os.environ['SQL_PASSWORD']}"
    )
    params = urllib.parse.quote_plus(odbc_str)
    return sqlalchemy.create_engine(f"mssql+pyodbc:///?odbc_connect={params}")


def _run_script(script_name: str, date: str, env: dict) -> None:
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "pipeline" / script_name), "--date", date],
        env={**os.environ, **env, "PYTHONPATH": str(_REPO_ROOT)},
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{script_name} failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )


class TestPipelineE2E:
    @pytest.fixture(autouse=True)
    def require_db(self):
        _skip_if_no_db()

    def test_happy_path_loads_five_rows(self, sample_landing_csv, tmp_path):
        """Full pipeline run loads exactly 5 rows to PolymerPricingFact."""
        date = "20260713"
        env = {
            "LANDING_DIR": str(sample_landing_csv.parent),
            "BRONZE_DIR": str(tmp_path / "bronze"),
            "SILVER_DIR": str(tmp_path / "silver"),
            "GOLD_DIR": str(tmp_path / "gold"),
            "LOG_DIR": str(tmp_path / "logs"),
        }

        # Clean up any prior test data in the DB
        engine = _build_engine()
        with engine.begin() as conn:
            conn.execute(
                sqlalchemy.text(
                    "DELETE FROM Reporting.PolymerPricingFact "
                    "WHERE pricing_date = '2026-07-13'"
                )
            )

        _run_script("01_IngestData.py", date, env)
        _run_script("02_TransformData.py", date, env)
        _run_script("03_LoadToWarehouse.py", date, env)

        with engine.connect() as conn:
            count = conn.execute(
                sqlalchemy.text(
                    "SELECT COUNT(*) FROM Reporting.PolymerPricingFact "
                    "WHERE pricing_date = '2026-07-13'"
                )
            ).scalar()

        assert count == 5, f"Expected 5 rows, got {count}"

    def test_idempotency(self, sample_landing_csv, tmp_path):
        """Re-running the full pipeline for the same date does not increase row count."""
        date = "20260713"
        env = {
            "LANDING_DIR": str(sample_landing_csv.parent),
            "BRONZE_DIR": str(tmp_path / "bronze"),
            "SILVER_DIR": str(tmp_path / "silver"),
            "GOLD_DIR": str(tmp_path / "gold"),
            "LOG_DIR": str(tmp_path / "logs"),
        }

        # Run once (first run may or may not have data from previous test)
        _run_script("02_TransformData.py", date, env)
        _run_script("03_LoadToWarehouse.py", date, env)

        engine = _build_engine()
        with engine.connect() as conn:
            count_after_first = conn.execute(
                sqlalchemy.text(
                    "SELECT COUNT(*) FROM Reporting.PolymerPricingFact "
                    "WHERE pricing_date = '2026-07-13'"
                )
            ).scalar()

        # Re-run 02 and 03 (01 would skip due to bronze idempotency)
        _run_script("02_TransformData.py", date, env)
        _run_script("03_LoadToWarehouse.py", date, env)

        with engine.connect() as conn:
            count_after_second = conn.execute(
                sqlalchemy.text(
                    "SELECT COUNT(*) FROM Reporting.PolymerPricingFact "
                    "WHERE pricing_date = '2026-07-13'"
                )
            ).scalar()

        assert count_after_second == count_after_first, (
            f"Row count changed after re-run: {count_after_first} → {count_after_second}"
        )

    def test_no_duplicate_material_date_in_fact(self):
        """Fact table has no duplicate (MaterialKey, pricing_date) pairs."""
        engine = _build_engine()
        with engine.connect() as conn:
            dup_count = conn.execute(
                sqlalchemy.text(
                    "SELECT COUNT(*) FROM ("
                    "  SELECT MaterialKey, pricing_date, COUNT(*) AS n"
                    "  FROM Reporting.PolymerPricingFact"
                    "  GROUP BY MaterialKey, pricing_date"
                    "  HAVING COUNT(*) > 1"
                    ") AS duplicates"
                )
            ).scalar()
        assert dup_count == 0, f"Found {dup_count} duplicate (MaterialKey, pricing_date) pairs"

    def test_all_material_codes_in_dim(self):
        """Every material_code in PolymerPricingFact has a row in MaterialDim."""
        engine = _build_engine()
        with engine.connect() as conn:
            orphan_count = conn.execute(
                sqlalchemy.text(
                    "SELECT COUNT(*) FROM Reporting.PolymerPricingFact f "
                    "LEFT JOIN dbo.MaterialDim m ON f.MaterialKey = m.MaterialKey "
                    "WHERE m.MaterialKey IS NULL"
                )
            ).scalar()
        assert orphan_count == 0, (
            f"{orphan_count} rows in PolymerPricingFact have no matching MaterialDim entry"
        )
