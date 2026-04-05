# Modified Strategy Round 2 Tuning Summary

## Ranking
1. `cs_more_entries`: +16.26% | final $1162.64 | entries 249 | TP 68 | LS 84 | PD 97 | fees $35.93
2. `cs_base_reference`: +8.95% | final $1089.48 | entries 167 | TP 46 | LS 55 | PD 66 | fees $26.76
3. `cs_hold_winners`: +5.83% | final $1058.33 | entries 133 | TP 41 | LS 54 | PD 36 | fees $21.14
4. `cs_wider_stop`: +5.83% | final $1058.33 | entries 133 | TP 38 | LS 50 | PD 43 | fees $21.14
5. `cs_conviction`: -5.01% | final $949.85 | entries 62 | TP 13 | LS 27 | PD 21 | fees $12.28

## Best Variant
- Name: `cs_more_entries`
- Final capital: $1162.64
- Final PnL: +16.26%
- Entries: 249
- Win rate: 27.3%
- Fees: $35.93

## Reading Guide
- `cs_hold_winners` tests whether looser potential-drop exits preserve upside.
- `cs_wider_stop` tests a wider stop and higher take profit for bigger swings.
- `cs_more_entries` tests a more active, lower-threshold variant.
- `cs_conviction` tests fewer but larger bets.
