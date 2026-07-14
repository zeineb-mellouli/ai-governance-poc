-- =============================================================================
-- sql/CreateMaterialDim.sql
-- Polymer material reference (dimension) table.
-- Convention: PascalCase, Key suffix for PK, no type prefixes (Constitution IX)
-- Idempotent: safe to run multiple times.
-- =============================================================================

IF NOT EXISTS (
    SELECT 1 FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = N'dbo' AND t.name = N'MaterialDim'
)
BEGIN
    CREATE TABLE dbo.MaterialDim (
        MaterialKey          INT           IDENTITY(1, 1) NOT NULL,
        material_code        VARCHAR(50)                  NOT NULL,
        material_description VARCHAR(255)                 NULL,
        created_date         DATETIME2                    NOT NULL
            CONSTRAINT DF_MaterialDim_CreatedDate DEFAULT GETDATE(),

        CONSTRAINT PK_MaterialDim
            PRIMARY KEY (MaterialKey),

        CONSTRAINT UQ_MaterialDim_MaterialCode
            UNIQUE (material_code)
    );

    PRINT 'Created dbo.MaterialDim';
END
ELSE
BEGIN
    PRINT 'dbo.MaterialDim already exists — no changes made.';
END;
GO
