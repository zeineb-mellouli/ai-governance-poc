-- Credit scoring results fact table -- one row per credit application
CREATE TABLE Reporting.CreditScoreFact (
    CreditScoreKey        INT           PRIMARY KEY,
    ApplicationId          VARCHAR(20)   NOT NULL,
    ScoredDate              DATE          NOT NULL,
    ProbabilityOfDefault    DECIMAL(6,4)  NOT NULL
);
