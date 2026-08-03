# fin-code-var_risk_model

Finance · Code · Market Risk VaR Model

## Purpose

Computes the daily 99% 1-day Value-at-Risk (VaR) for the trading book,
combining historical simulation with a short-horizon volatility scaling
model. Feeds the desk risk-limit monitor and the regulatory capital report.

## Structure

| Folder | Contents |
|---|---|
| `bronze/` | Raw market data feed and trading positions, as received from the market data vendor and the position-keeping system |
| `Risk_Pipeline/` | `01` ingest, `02` volatility scaling model, `03` VaR computation and breach report |
| `Risk_SQL/` | DDL for the daily VaR breach fact table |

## How to run

```bash
pip install -r requirements.txt

python Risk_Pipeline/01_IngestMarketData.py
python Risk_Pipeline/02_VolatilityModel.py
python Risk_Pipeline/03_ComputeVaR.py
```

## Note

`hotfix-var-breach-mar24` was cut directly from `master` during the March
gilt-market shock to patch a same-day data gap. Marked for cleanup after the
incident review.
