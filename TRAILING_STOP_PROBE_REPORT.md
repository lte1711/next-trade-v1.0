# Trailing Stop Probe Report

Generated: 2026-04-09T15:55:46.801294+09:00
Status: `completed`

## Cases
- long_trailing_above_2pct: profit_pct=0.03, updated=True, managed_stop=101.97, expected_direction=raise_long_stop
- short_trailing_above_2pct: profit_pct=0.03, updated=True, managed_stop=97.97, expected_direction=lower_short_stop
- long_trailing_below_threshold: profit_pct=0.015, updated=False, managed_stop=None, expected_direction=no_update

## Next Evolution Targets
- Add a live scenario that tightens actual protective algo stop orders after profit expansion.
- Promote the trailing-stop probe into the regression gate summary for routine demo validation.
