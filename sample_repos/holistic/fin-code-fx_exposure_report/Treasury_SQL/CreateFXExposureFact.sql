-- Quarterly FX exposure fact table -- one row per currency per quarter-end
CREATE TABLE Reporting.FXExposureFact (
    FXExposureKey   INT           PRIMARY KEY,
    CurrencyCode    VARCHAR(3)    NOT NULL,
    QuarterEndDate  DATE          NOT NULL,
    TotalExposure   DECIMAL(18,2) NOT NULL
);
