"""
pipeline/transforms.py
------------------------
Pure-function transforms for the Polymer Pricing ETL pipeline.
Extracted here so they can be independently unit-tested without
importing the numbered pipeline scripts directly.
"""

import pandas as pd


def add_loaded_at(df: pd.DataFrame) -> pd.DataFrame:
    """Append a ``loaded_at`` UTC timestamp column for the gold layer.

    Does not mutate the input DataFrame.

    Args:
        df: Silver-layer DataFrame (validated by SilverSchema).

    Returns:
        New DataFrame with an additional ``loaded_at`` column of dtype
        ``datetime64[ns]``.
    """
    out = df.copy()
    out["loaded_at"] = pd.Timestamp.now(tz="UTC")
    return out
