-- ============================================================
-- Table  : Reporting.ProductDim
-- Schema : Reporting  (data model)
-- Grain  : One row per unique product (Type 2 SCD)
-- Key    : ProductKey  (surrogate identity)
-- ============================================================

CREATE TABLE Reporting.ProductDim (
    ProductKey        INT            IDENTITY(1,1) NOT NULL,
    ProductCode       NVARCHAR(20)   NOT NULL,
    ProductName       NVARCHAR(100)  NOT NULL,
    ProductCategory   NVARCHAR(50)   NOT NULL,
    SourceRegion      NVARCHAR(50)   NOT NULL,
    EffectiveDate     DATE           NOT NULL,
    ExpiryDate        DATE           NULL,
    IsCurrent         BIT            NOT NULL  DEFAULT 1,

    CONSTRAINT PK_ProductDim
        PRIMARY KEY (ProductKey),

    CONSTRAINT UQ_ProductDim_Code_Effective
        UNIQUE (ProductCode, EffectiveDate)
);
