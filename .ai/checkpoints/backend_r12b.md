# CHECKPOINT

Checkpoint: R12b (no-show reports + 50% refund)
Owner: Kolya (Kolya's agent)
Branch: feat/r12b-noshow (continues from master 20093b6, which already holds the R12 phase 2 and the R12b WIP commits)
Status: READY on the branch; the owner merges the PR.

## Implemented
- `NoShowReport` workflow (owner report / withdraw, staff approve / reject / reverse), `Booking.no_show_refund_percent` snapshot, disclosure fields, refunds through the `Refund` model, notifications, abuse flag, metrics `no_show_reported`, auto-completion skips pending reports (see the earlier commits and `.ai/checkpoints/backend_r12b_wip.md`).
- This session: owner bookings list `can_report_no_show`, `report_deadline`, `?reportable=true` (`bookings/noshow.py` `reportable_bookings`, `report_deadline`; `create_report` uses the same deadline), OpenAPI warnings fixed, docs.

## Tests
- New this session: `test_r12b_reportable.py` (13: check-in day, last window day, one day after, statuses, open/withdrawn report, filter, agreement with the endpoint; 11 failed before the code), `test_r12b_extras.py` (2: two concurrent approves refund once, OpenAPI builds with no warnings). The 20/hour throttle default was already tested in `test_r12b_noshow.py`; `check --deploy` in `core/tests/test_r4_production_config.py`.
- Full suite (`venvScriptspython.exe -m pytest --create-db -q -n 8`): 2488 passed, 0 failed, 2 skipped (first run 1 failed, the throttle-rates expectation below).
- Changed expectation: `core/tests/test_settings_defaults.py::test_anonymous_browsing_limit_allows_normal_use` throttle rates `{'anon': '2000/hour', 'user': '1000/hour'}` -> same plus `'no_show_report': '20/hour'` (the new throttle scope is part of the rates). Anon and user values unchanged.

## Known issues / not done
- Partial refunds unverified with Payme, Click and Visa: real mode stores `needs_manual` (RELEASE_CHECKLIST). A lawyer must review the refund wording.
- Test DB for xdist: `pytest-xdist` installed in the local venv only, not in requirements.txt.
