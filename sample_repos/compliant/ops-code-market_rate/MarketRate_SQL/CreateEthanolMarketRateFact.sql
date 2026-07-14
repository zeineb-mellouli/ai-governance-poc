-- ============================================================
-- Table  : Reporting.EthanolMarketRateFact
-- Schema : Reporting  (data model)
-- Grain  : One row per product per market date
-- Key    : EthanolMarketRateKey  (surrogate identity)
-- ============================================================

CREATE TABLE Reporting.EthanolMarketRateFact (
    EthanolMarketRateKey  INT            IDENTITY(1,1) NOT NULL,
    ProductKey            INT            NOT NULL,
    MarketDate            DATE           NOT NULL,
    PriceUsd              DECIMAL(10,2)  NOT NULL,
    VolumeTonnes          DECIMAL(12,2)  NOT NULL,
    SourceRegion          NVARCHAR(50)   NOT NULL,
    LoadedAt              DATETIME2      NOT NULL  DEFAULT GETUTCDATE(),

    CONSTRAINT PK_EthanolMarketRateFact
        PRIMARY KEY (EthanolMarketRateKey),

    CONSTRAINT FK_EthanolMarketRateFact_Product
        FOREIGN KEY (ProductKey)
        REFERENCES Reporting.ProductDim (ProductKey),

    CONSTRAINT UQ_EthanolMarketRateFact_Grain
        UNIQUE (ProductKey, MarketDate)
);
