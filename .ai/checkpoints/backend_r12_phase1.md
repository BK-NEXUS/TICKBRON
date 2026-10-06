# CHECKPOINT

Checkpoint: R12 phase 1 (business date, auto-completion, Refund model, notification codes)
Owner: Kolya (Kolya's agent)
Branch: feat/r12-status
Commits: 0c4f04f (1a), 8d8174e (1b), e204a3a (1c WIP) + d5c1c43 (1c suite green), 1d and docs commits after it
Status: READY

## Implemented
- 1a `BUSINESS_TIME_ZONE` (default Asia/Tashkent), `common.dates.business_today()`; booking create / quote / availability reject check-in before the Tashkent date (`TIME_ZONE` stays UTC).
- 1b `bookings/completion.py`: confirmed stays with `check_out < business_today()` become completed nightly (00:05 Tashkent, `CELERY_TIMEZONE = BUSINESS_TIME_ZONE`), `AutoCompletionRun` history (`bookings/0009`), command `complete_finished_stays [--dry-run]`, super-admin `GET /admin-panel/auto-completion/status/`.
- 1c `payments.Refund` (`payments/0003`, backfill `payments/0004`, reversible), `payments/refunds.py` (`create_refund` with the payment row locked and non-failed sum <= paid, `send_refund` after commit outside transactions, `mark_manual_done`, `retry_refund`), adapters `SUPPORTS_PARTIAL_REFUND = None` (unverified → `needs_manual`), staff refund endpoint writes through the model (`refund` field, 202 for needs_manual), needs-attention / mark-done / retry endpoints, `completed -> no_show` only with an approved report.
- 1d `accounts.Notification.code` + `params` (`accounts/0002`, reversible), `accounts.notify(user, code, params, booking=None)` with a code registry and English fallback text (`accounts/notifications.py`); params keys whitelisted, each value validated as id / amount / currency / percent / ISO date, so personal data is refused.

## Tests
- Full suite after 1c (`pytest --create-db`, xdist -n 8): first run 2 failed, 2101 passed, 2 skipped. Both = `bookings/tests/test_r6_snapshot_migration.py`: test setup kept other apps at their leaf, but `payments/0003` depends on `bookings/0009` (setup fixed, no assertion changed). The predicted failures in `payments/tests/test_views.py` / `test_r4_refund_cancel_booking.py` did not occur (already updated in e204a3a). Then 2103 passed, 0 failed, 2 skipped.
- TDD proof 1c (code restored to e204a3a~1, tests untouched, restored with `git checkout HEAD --`): behaviour code removed (model + migrations kept): 24 failed / 13 passed; model removed too: 2 collection errors.
- TDD proof 1d: `accounts/tests/test_r12_notify.py` written first, failed (module missing); then 28 passed (incl. reverse/forward of `accounts/0002`).
- Full suite after 1d (`pytest --create-db`, xdist -n 8): 2131 passed, 0 failed, 2 skipped.

## Security
- Refund amounts checked with the payment row locked; provider never called inside a DB transaction; audit `details` whitelisted (`refund_id`); notification params cannot carry names, emails, phones or free text; needs-attention rows have no guest PII.

## API/contract changes
- `.ai/API_CONTRACT.md` "2026-10-06 R12 phase 1".

## Dev database
- No dev database on this computer (`tickbron` does not exist, only `postgres`); nothing was migrated, `complete_finished_stays` not run. Where a dev DB exists: `pg_dump -Fc` first, `migrate`, `complete_finished_stays --dry-run`, then the real run.

## Known issues
- Payme / Click / Visa partial refunds unverified (RELEASE_CHECKLIST "Refunds (R12 phase 1)").
- The WIP commit e204a3a stays in history (already pushed; not rewritten); d5c1c43 completes it.
