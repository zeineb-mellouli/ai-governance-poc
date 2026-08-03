# fin-code-credit_scoring_model

Finance · Code · Credit Scoring Model

## Purpose

Trains the logistic regression model used to grade new credit applications
and writes a probability-of-default score for each applicant.

## Structure — Medallion architecture

| Folder | Medallion layer | Contents |
|---|---|---|
| `bronze/` | Bronze | Raw credit applications as received from the loan origination system |
| `silver/` | Silver | Validated credit applications |
| `gold/` | Gold | Scored applications, ready for underwriting |
| `CreditScoring_Pipeline/` | — | `01` Bronze→Silver · `02` Silver→Gold model training and scoring |
| `CreditScoring_SQL/` | — | DDL for Reporting.CreditScoreFact |

## How to run

```bash
pip install -r requirements.txt

python CreditScoring_Pipeline/01_IngestApplications.py
python CreditScoring_Pipeline/02_TrainScoringModel.py
```

## Branch strategy

| Branch | Purpose |
|---|---|
| `master` | Production-ready — protected, requires PR review |
| `develop` | Integration branch |
| `user-story/{id}` | Feature work |

Commit message format: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
