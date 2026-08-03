"""
tests/unit/test_schemas.py
---------------------------
Unit tests for BronzeSchema, SilverSchema, and GoldSchema.
Covers T012 (Bronze), T014 (Silver), T016 (Gold).

Run with:
    pytest tests/unit/test_schemas.py -v
"""

import pandas as pd
import pandera as pa
import pytest

from pipeline.schemas.pricing_schema import BronzeSchema, GoldSchema, SilverSchema


# ── BronzeSchema (T012) ───────────────────────────────────────────────────────


class TestBronzeSchema:
    def test_valid_bronze_df_passes(self, sample_bronze_df):
        BronzeSchema.validate(sample_bronze_df)

    def test_missing_source_file_name_raises(self, sample_bronze_df):
        df = sample_bronze_df.drop(columns=["source_file_name"])
        with pytest.raises(pa.errors.SchemaError):
            BronzeSchema.validate(df)

    def test_missing_ingestion_timestamp_raises(self, sample_bronze_df):
        df = sample_bronze_df.drop(columns=["ingestion_timestamp"])
        with pytest.raises(pa.errors.SchemaError):
            BronzeSchema.validate(df)

    def test_null_material_code_raises(self, sample_bronze_df):
        df = sample_bronze_df.copy()
        df.loc[0, "material_code"] = None
        with pytest.raises(pa.errors.SchemaError):
            BronzeSchema.validate(df)

    def test_nonnumeric_price_value_raises(self, sample_bronze_df):
        df = sample_bronze_df.copy().astype(object)
        df.loc[0, "price_value"] = "not-a-number"
        with pytest.raises(pa.errors.SchemaError):
            BronzeSchema.validate(df)

    def test_extra_column_raises_in_strict_mode(self, sample_bronze_df):
        df = sample_bronze_df.copy()
        df["extra_col"] = "x"
        with pytest.raises((pa.errors.SchemaError, pa.errors.SchemaErrors)):
            BronzeSchema.validate(df)


# ── SilverSchema (T014) ───────────────────────────────────────────────────────


class TestSilverSchema:
    def test_valid_silver_df_passes(self, sample_silver_df):
        SilverSchema.validate(sample_silver_df)

    def test_null_material_code_raises(self, sample_silver_df):
        df = sample_silver_df.copy()
        df.loc[0, "material_code"] = None
        with pytest.raises(pa.errors.SchemaError):
            SilverSchema.validate(df)

    def test_price_above_limit_raises(self, sample_silver_df):
        df = sample_silver_df.copy()
        df.loc[0, "price_value"] = 150_000.0
        with pytest.raises(pa.errors.SchemaError):
            SilverSchema.validate(df)

    def test_zero_price_raises(self, sample_silver_df):
        df = sample_silver_df.copy()
        df.loc[0, "price_value"] = 0.0
        with pytest.raises(pa.errors.SchemaError):
            SilverSchema.validate(df)

    def test_negative_price_raises(self, sample_silver_df):
        df = sample_silver_df.copy()
        df.loc[0, "price_value"] = -10.0
        with pytest.raises(pa.errors.SchemaError):
            SilverSchema.validate(df)

    def test_two_char_currency_code_raises(self, sample_silver_df):
        df = sample_silver_df.copy()
        df.loc[0, "currency_code"] = "US"
        with pytest.raises(pa.errors.SchemaError):
            SilverSchema.validate(df)

    def test_lowercase_currency_code_raises(self, sample_silver_df):
        df = sample_silver_df.copy()
        df.loc[0, "currency_code"] = "usd"
        with pytest.raises(pa.errors.SchemaError):
            SilverSchema.validate(df)

    def test_deduplication_before_validation(self, sample_silver_df):
        """After drop_duplicates on (material_code, pricing_date), schema passes."""
        duplicate = sample_silver_df.iloc[[0]].copy()
        df = pd.concat([sample_silver_df, duplicate], ignore_index=True)
        assert len(df) == 6
        deduped = df.drop_duplicates(subset=["material_code", "pricing_date"], keep="first")
        assert len(deduped) == 5
        SilverSchema.validate(deduped)

    def test_nat_pricing_date_raises(self, sample_silver_df):
        df = sample_silver_df.copy()
        df.loc[0, "pricing_date"] = pd.NaT
        with pytest.raises(pa.errors.SchemaError):
            SilverSchema.validate(df)


# ── GoldSchema (T016) ─────────────────────────────────────────────────────────


class TestGoldSchema:
    def _with_loaded_at(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["loaded_at"] = pd.Timestamp.now(tz="UTC")
        return out

    def test_valid_gold_df_passes(self, sample_silver_df):
        GoldSchema.validate(self._with_loaded_at(sample_silver_df))

    def test_missing_loaded_at_raises(self, sample_silver_df):
        with pytest.raises(pa.errors.SchemaError):
            GoldSchema.validate(sample_silver_df)

    def test_null_loaded_at_raises(self, sample_silver_df):
        df = self._with_loaded_at(sample_silver_df)
        df["loaded_at"] = df["loaded_at"].astype(object)
        df.loc[0, "loaded_at"] = None
        with pytest.raises(pa.errors.SchemaError):
            GoldSchema.validate(df)

    def test_duplicate_material_date_raises(self, sample_silver_df):
        df = self._with_loaded_at(sample_silver_df)
        dup = df.iloc[[0]].copy()
        df = pd.concat([df, dup], ignore_index=True)
        with pytest.raises(pa.errors.SchemaError):
            GoldSchema.validate(df)

    def test_silver_constraints_inherited(self, sample_silver_df):
        """GoldSchema still rejects out-of-range prices."""
        df = self._with_loaded_at(sample_silver_df)
        df.loc[0, "price_value"] = 200_000.0
        with pytest.raises(pa.errors.SchemaError):
            GoldSchema.validate(df)
