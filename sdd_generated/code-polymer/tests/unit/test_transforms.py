"""
tests/unit/test_transforms.py
------------------------------
Unit tests for pipeline.transforms.add_loaded_at (T017).

Run with:
    pytest tests/unit/test_transforms.py -v
"""

import pandas as pd

from pipeline.schemas.pricing_schema import GoldSchema
from pipeline.transforms import add_loaded_at


class TestAddLoadedAt:
    def test_loaded_at_column_added(self, sample_silver_df):
        result = add_loaded_at(sample_silver_df)
        assert "loaded_at" in result.columns

    def test_loaded_at_dtype_is_datetime(self, sample_silver_df):
        result = add_loaded_at(sample_silver_df)
        assert pd.api.types.is_datetime64_any_dtype(result["loaded_at"])

    def test_row_count_unchanged(self, sample_silver_df):
        result = add_loaded_at(sample_silver_df)
        assert len(result) == len(sample_silver_df)

    def test_gold_schema_validates_output(self, sample_silver_df):
        result = add_loaded_at(sample_silver_df)
        GoldSchema.validate(result)  # must not raise

    def test_loaded_at_is_recent(self, sample_silver_df):
        before = pd.Timestamp.now(tz="UTC")
        result = add_loaded_at(sample_silver_df)
        after = pd.Timestamp.now(tz="UTC")
        assert (result["loaded_at"] >= before).all()
        assert (result["loaded_at"] <= after).all()

    def test_input_df_not_mutated(self, sample_silver_df):
        original_cols = set(sample_silver_df.columns)
        add_loaded_at(sample_silver_df)
        assert set(sample_silver_df.columns) == original_cols
        assert "loaded_at" not in sample_silver_df.columns
