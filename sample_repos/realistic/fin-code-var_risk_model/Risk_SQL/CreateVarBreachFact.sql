-- Daily VaR breach fact table, added by the reporting team after the March
-- incident to persist breaches for the audit trail.
CREATE TABLE Reporting.VarBreachFact (
    VarBreachKey     INT           PRIMARY KEY,
    Desk             VARCHAR(20)   NOT NULL,
    InstrumentId     VARCHAR(20)   NOT NULL,
    VarAmount        DECIMAL(18,2) NOT NULL,
    RiskLimitAmount  DECIMAL(18,2) NOT NULL,
    BreachDate       DATE          NOT NULL
);
