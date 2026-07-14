"""
pipeline/schemas/pricing_schema.py
------------------------------------
Pandera DataFrameModel schemas for all three medallion layers.

Constitution II: Validate for nulls, duplicates, and out-of-range values
before every layer write. Use pandera.

Layer → Schema mapping:
  Bronze (raw CSV)      → BronzeSchema
  Silver (validated)    → SilverSchema
  Gold   (aggregated)   → GoldSchema  (inherits SilverSchema + adds loaded_at)
"""

import pandas as pd
import pandera as pa
from pandera.typing import Series


class BronzeSchema(pa.DataFrameModel):
    """Validates the raw bronze CSV immediately after metadata columns are appended.

    Checks column presence and nullability only — no range or format rules.
    Bronze preserves raw source data with maximum fidelity.
    """

    material_code: Series[str] = pa.Field(nullable=False)
    pricing_date: Series[str] = pa.Field(nullable=False)
    price_value: Series[float] = pa.Field(nullable=False)
    unit_of_measure: Series[str] = pa.Field(nullable=False)
    currency_code: Series[str] = pa.Field(nullable=False)
    source_file_name: Series[str] = pa.Field(nullable=False)
    ingestion_timestamp: Series[str] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = False


class SilverSchema(pa.DataFrameModel):
    """Validates cleansed, type-coerced silver data.

    Enforces:
    - No nulls in any mandatory field
    - price_value strictly between 0 and 100,000
    - currency_code exactly 3 uppercase alphabetic characters (ISO 4217)
    - pricing_date not in the future
    """

    material_code: Series[str] = pa.Field(nullable=False)
    pricing_date: Series[pd.Timestamp] = pa.Field(nullable=False)
    price_value: Series[float] = pa.Field(gt=0.0, lt=100_000.0, nullable=False)
    unit_of_measure: Series[str] = pa.Field(nullable=False)
    currency_code: Series[str] = pa.Field(
        str_matches=r"^[A-Z]{3}$", nullable=False
    )
    source_file_name: Series[str] = pa.Field(nullable=False)
    ingestion_timestamp: Series[pd.Timestamp] = pa.Field(nullable=False)

    class Config:
        strict = True
        coerce = True  # Coerce dtypes (e.g., str → datetime) as a safety net

    @pa.dataframe_check
    @classmethod
    def pricing_date_not_future(cls, df: pd.DataFrame) -> Series[bool]:
        """Reject rows where pricing_date is strictly after today."""
        today = pd.Timestamp.now().normalize()
        return df["pricing_date"] <= today


class GoldSchema(SilverSchema):
    """Validates aggregated gold data.

    Inherits all SilverSchema constraints and additionally:
    - Requires a loaded_at timestamp column
    - Enforces uniqueness on (material_code, pricing_date)
    """

    loaded_at: Series[pd.Timestamp] = pa.Field(nullable=False)

    class Config(SilverSchema.Config):
        unique = ["material_code", "pricing_date"]
