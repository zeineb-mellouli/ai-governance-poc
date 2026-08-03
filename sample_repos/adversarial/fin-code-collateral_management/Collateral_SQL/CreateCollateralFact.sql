-- Daily collateral and margin call fact table -- one row per counterparty per day
CREATE TABLE Reporting.CollateralFact (
    CollateralKey        INT           PRIMARY KEY,
    CounterpartyId        VARCHAR(20)   NOT NULL,
    AsOfDate               DATE          NOT NULL,
    RequiredCollateral     DECIMAL(18,2) NOT NULL,
    PostedCollateral       DECIMAL(18,2) NOT NULL,
    MarginCallAmount       DECIMAL(18,2) NOT NULL
);
