-- Counterparty dimension table for bank relationship exposure tracking
CREATE TABLE Reporting.CounterpartyDim (
    Id                INT           PRIMARY KEY,
    CounterpartyName  VARCHAR(200)  NOT NULL,
    CreditRating      VARCHAR(5)    NOT NULL,
    ExposureLimit     DECIMAL(18,2) NOT NULL
);
