-- =============================================================================
-- sql/CreatePolymerPricingFact.sql
-- Daily polymer pricing fact table in the Reporting schema.
-- Convention: PascalCase, Key suffix for PK/FK, Fact suffix (Constitution IX)
-- Idempotent: safe to run multiple times.
-- =============================================================================

-- Ensure the Reporting schema exists
IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = N'Reporting')
BEGIN
    EXEC(N'CREATE SCHEMA Reporting');
    PRINT 'Created schema Reporting';
END;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = N'Reporting' AND t.name = N'PolymerPricingFact'
)
BEGIN
    CREATE TABLE Reporting.PolymerPricingFact (
        PricingKey           INT            IDENTITY(1, 1) NOT NULL,
        MaterialKey          INT                           NOT NULL,
        pricing_date         DATE                          NOT NULL,
        price_value          DECIMAL(18, 6)                NOT NULL,
        unit_of_measure      VARCHAR(20)                   NOT NULL,
        currency_code        CHAR(3)                       NOT NULL,
        source_file_name     VARCHAR(255)                  NOT NULL,
        ingestion_timestamp  DATETIME2                     NOT NULL,
        loaded_at            DATETIME2                     NOT NULL
            CONSTRAINT DF_PolymerPricingFact_LoadedAt DEFAULT GETDATE(),

        CONSTRAINT PK_PolymerPricingFact
            PRIMARY KEY (PricingKey),

        CONSTRAINT FK_PolymerPricingFact_MaterialKey
            FOREIGN KEY (MaterialKey)
            REFERENCES dbo.MaterialDim (MaterialKey),

        -- Enforces one row per material per pricing date; also the MERGE join key
        CONSTRAINT UQ_PolymerPricingFact_MaterialDate
            UNIQUE (MaterialKey, pricing_date)
    );

    PRINT 'Created Reporting.PolymerPricingFact';
END
ELSE
BEGIN
    PRINT 'Reporting.PolymerPricingFact already exists — no changes made.';
END;
GO

-- =============================================================================
-- Reference: MERGE upsert template used by pipeline/03_LoadToWarehouse.py
-- (Shown here for documentation; executed dynamically via sqlalchemy.text())
-- =============================================================================
--
-- MERGE Reporting.PolymerPricingFact AS target
-- USING #StagingPolymerPricing AS source
--     ON  target.MaterialKey  = source.MaterialKey
--     AND target.pricing_date = source.pricing_date
-- WHEN MATCHED THEN
--     UPDATE SET
--         target.price_value         = source.price_value,
--         target.unit_of_measure     = source.unit_of_measure,
--         target.currency_code       = source.currency_code,
--         target.source_file_name    = source.source_file_name,
--         target.ingestion_timestamp = source.ingestion_timestamp,
--         target.loaded_at           = GETDATE()
-- WHEN NOT MATCHED BY TARGET THEN
--     INSERT (MaterialKey, pricing_date, price_value, unit_of_measure,
--             currency_code, source_file_name, ingestion_timestamp, loaded_at)
--     VALUES (source.MaterialKey, source.pricing_date, source.price_value,
--             source.unit_of_measure, source.currency_code,
--             source.source_file_name, source.ingestion_timestamp, GETDATE());
