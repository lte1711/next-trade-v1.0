# Empirical Runtime Evaluation

## Verdict
Demo testnet readiness remains `GO`.

As of April 9, 2026, the runtime has enough empirical evidence to move forward to the next evolution stage without reopening core plumbing work first. The system has already passed the full final gate, generated real demo trades, separated intended skips from true errors, and restored live position metadata after restart.

## Evidence
`Final gate`

- [final_gate_runner.json](/c:/next-trade-ver1.0/final_gate_runner.json) shows 8 of 8 validation runs passed on April 9, 2026.
- This includes initialization, forced lifecycle, multi-symbol lifecycle, short-side flow, trailing stop, and live stop-tightening symmetry.

`Historical unattended demo evidence`

- [unattended_live_demo_status.json](/c:/next-trade-ver1.0/unattended_live_demo_status.json) shows a live demo session that started on April 9, 2026 at 17:05:32 +09:00.
- At the observed snapshot it had completed 13 cycles, generated 260 signals, executed 10 trades, and reached 4 concurrent active positions.
- This file is important because it proves real entries occurred after the signal-input wiring fix.
- This file should also be treated carefully because it still contains legacy cycle semantics from before skip/error cleanup was finished.

`Skip separation evidence`

- [supervised_skip_probe_status.json](/c:/next-trade-ver1.0/supervised_skip_probe_status.json) shows a fresh 2-cycle supervised probe on April 9, 2026.
- It completed with `cycles_with_errors=0` while recording 6 skips total.
- The sample skips were:
  - low-price preflight block for `1000WHYUSDT`
  - duplicate-entry block for `HIPPOUSDT`
  - duplicate-entry block for `NEIROUSDT`
- This proves the runtime can distinguish intended blocks from actual cycle failures.

`Preflight and system error cleanup evidence`

- [supervised_preflight_event_probe.json](/c:/next-trade-ver1.0/supervised_preflight_event_probe.json) shows a later fresh probe on April 9, 2026 after preflight handling was moved out of `system_errors`.
- That probe completed with `signals_generated=20`, `trades_executed=1`, `errors=[]`, and `system_errors=0`.
- This is the cleanest evidence that intended operating blocks no longer contaminate runtime health metrics.

`Restart resilience evidence`

- A fresh runtime initialization and `sync_positions()` recheck on April 9, 2026 restored live metadata for 3 active positions.
- `1000WHYUSDT` was no longer present in the fresh valid symbol pool, confirming the upstream ultra-low-price filter.
- The restored live position state was:

| Symbol | Strategy | Entry Time | Stop Loss | Take Profit | Managed Stop |
|---|---|---:|---:|---:|---:|
| HIPPOUSDT | ma_trend_follow | 1775723212379 | 0.03 | 0.045 | 0.000209 |
| NEIROUSDT | ma_trend_follow | 1775722060663 | 0.03 | 0.045 | 0.000057 |
| ZRCUSDT | ma_trend_follow | 1775724356161 | 0.03 | 0.045 | 0.00184 |

- This confirms the combined journal, local-state, and exchange-fallback restoration path is working.

## Assessment
The runtime is no longer blocked by execution infrastructure. The empirical record now supports these conclusions:

- Core runtime stability is good enough for continued demo evolution.
- Real demo trades have been observed, so the system is no longer trapped in an all-`HOLD` state.
- Protective lifecycle validation is already strong.
- Duplicate-entry and preflight blocks are now operational skips, not runtime failures.
- Restart resilience is materially improved and now backed by live reconstruction data.

The main remaining weakness is no longer plumbing. It is strategy quality: which symbols get selected, how noisy candidates are filtered, and how signal thresholds should adapt to real performance.

## Next Evolution
The next step should be an adaptive signal-quality layer rather than another round of core runtime plumbing.

That next phase should focus on:

- improving symbol quality before they reach execution
- ranking candidates with live outcome feedback
- tightening entry selectivity using observed skip/trade outcomes
- reducing low-value churn while preserving validated protective behavior

## Consolidated Artifact
The machine-readable version of this evaluation is stored in [EMPIRICAL_RUNTIME_EVALUATION.json](/c:/next-trade-ver1.0/EMPIRICAL_RUNTIME_EVALUATION.json).
