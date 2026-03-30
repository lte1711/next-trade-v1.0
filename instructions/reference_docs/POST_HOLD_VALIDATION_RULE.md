# Post-Hold Validation Rule

## Purpose
Validate the report archive state after reversible hold rename has been applied to legacy flat role folders.

## Facts Required
- Legacy flat role folders are absent.
- `_legacy_verified_hold` role folders are present.
- Dated role folders remain present.
- Migration manifest target files remain reachable.
- Dashboard API remains available after hold rename.

## Gate Conditions
1. `reports\honey_execution_reports` must not exist.
2. `reports\candy_validation_reports` must not exist.
3. `reports\honey_execution_reports_legacy_verified_hold` must exist.
4. `reports\candy_validation_reports_legacy_verified_hold` must exist.
5. `reports\YYYY-MM-DD\honey_execution_reports` must exist.
6. `reports\YYYY-MM-DD\candy_validation_reports` must exist.
7. Manifest target missing count must equal 0.
8. Dashboard API should return HTTP 200 if runtime is expected to stay available.

## Validation Output
- `POST_HOLD_VALIDATION_DETAIL.csv`
- `POST_HOLD_VALIDATION_DETAIL.json`
- `POST_HOLD_VALIDATION_SUMMARY.txt`

## Interpretation
- If all gate conditions pass, post-hold state is structurally valid.
- If legacy flat folders reappear, or hold folders are missing, the hold state is invalid.
- If target files are missing, migration integrity must be rechecked before further cleanup.
- Dashboard API failure must be treated as an operational issue, not automatically as archive corruption.
