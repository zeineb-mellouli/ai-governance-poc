import pandera as pa
from pandera import Column, DataFrameSchema

# Silver layer schema — validated after PII columns have been dropped.
# Uniqueness of customer_id within a batch is enforced separately in
# validate.py (pandera does not handle cross-row deduplication).
SILVER_SCHEMA = DataFrameSchema(
    {
        "customer_id": Column(str, nullable=False),
        "account_tenure_months": Column(
            float,
            pa.Check(lambda s: s >= 0.0, element_wise=True, error="account_tenure_months must be >= 0"),
            nullable=False,
        ),
        "monthly_usage_hours": Column(
            float,
            pa.Check(lambda s: s >= 0.0, element_wise=True, error="monthly_usage_hours must be >= 0"),
            nullable=False,
        ),
        "is_churned": Column(
            int,
            pa.Check(lambda s: s.isin([0, 1]), error="is_churned must be 0 or 1"),
            nullable=False,
        ),
    },
    strict=False,  # allow pipeline-added columns (validated_at, batch_id)
)
