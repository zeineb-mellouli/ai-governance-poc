-- Daily liquidity forecast fact table -- one row per bank account per forecast day
CREATE TABLE Reporting.LiquidityForecastFact (
    LiquidityForecastKey  INT           PRIMARY KEY,
    BankAccountId         VARCHAR(20)   NOT NULL,
    ForecastDate          DATE          NOT NULL,
    ProjectedBalance      DECIMAL(18,2) NOT NULL
);
