# Real Market V3 Risk Tuning Summary

## Ranking By Risk-Adjusted Score
1. `remote_risk_reference`: pnl +44.00% | max DD -16.54% | score +27.46 | entries 81 | fees $11.84
2. `remote_capital_preserver`: pnl +33.08% | max DD -11.46% | score +21.62 | entries 66 | fees $7.53
3. `remote_smoother_equity`: pnl +23.19% | max DD -13.29% | score +9.90 | entries 77 | fees $9.33
4. `remote_drawdown_guard`: pnl +19.56% | max DD -18.31% | score +1.25 | entries 75 | fees $9.68

## Best Risk-Adjusted Candidate
- Name: `remote_risk_reference`
- Final capital: $1440.01
- Final PnL: +44.00%
- Max drawdown: -16.54%
- Max consecutive losses: 4

## Interpretation
- `remote_drawdown_guard` tightens entries and shrinks size first.
- `remote_capital_preserver` is the most defensive variant.
- `remote_smoother_equity` aims to reduce churn without over-tightening entries.
