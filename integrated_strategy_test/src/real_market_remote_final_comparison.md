# Real Market Remote Final Comparison

## Aggressive vs Balanced
- Aggressive reference: `remote_risk_reference`
  Final capital $1440.01 | PnL +44.00% | Max DD -16.54% | Fees $11.84 | Max loss streak 4 | Up months 5 / Down months 6
- Balanced default: `v3_remote_default_capital_preserver`
  Final capital $1330.80 | PnL +33.08% | Max DD -11.46% | Fees $7.53 | Max loss streak 4 | Up months 6 / Down months 4

## Recommendation
- Choose the aggressive reference when maximizing upside is the top priority and a deeper drawdown is acceptable.
- Choose the balanced default when adoption safety matters more and you want materially lower drawdown with still-strong returns.

## Default Decision
- The balanced candidate remains the recommended default profile.
- The aggressive reference should remain an alternate high-beta profile for controlled experiments.
