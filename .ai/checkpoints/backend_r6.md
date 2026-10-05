# CHECKPOINT

Checkpoint: R6 currency (UZS charge, CBU rate, booking snapshot)
Owner: Kolya (Kolya's agent)
Commit: e32f1ce, efc642d, be45047, 7afdaba (WIP), 581e568 (suite green), docs commit after it
Status: READY

## Implemented
- `common/money.py`: USD/UZS list, UZS whole so'm, USD cents, ROUND_HALF_UP, conversion rounded once on the stay total, floats rejected.
- `currency` app: `ExchangeRate` history (append-only), `ExchangeRateFetch` log, CBU fetch (`currency/cbu.py`, HTTPS only, no redirects, 64 KB cap, strict parsing), Celery task 09:00 and 18:00 Asia/Tashkent, `fetch_exchange_rates` command, sanity limits (FX_MAX_CHANGE, FX_MIN_RATE, FX_MAX_RATE), stale flag (FX_STALE_AFTER_DAYS), migration guard (non USD/UZS prices stop `migrate`).
- Booking charge snapshot (`charge_currency`, `charge_amount`, `exchange_rate`, `exchange_rate_date`, `exchange_rate_source`, `exchange_rate_stale`), written in `Booking.create_booking` inside the inventory-locking transaction, immutable (`save()` raises). USD hotel without a rate: 503 `exchange_rate_unavailable`, nothing reserved. Migrations `bookings/0006-0008` (nullable, backfill `legacy`/`identity`, NOT NULL).
- Quote `uzs_total` + `exchange_rate`; search/detail/availability `base_price_uzs_approx` + `uzs_rate` (one rate lookup per request).
- Payments: amount/currency must equal the booking snapshot; Payme tiyin conversion inside the adapter; UZS partial refunds whole so'm.
- Staff exchange-rate endpoints (list, status, accept) with audit log `details`.
- 2026-10-05: shared test rate fixture (`conftest.py` `default_exchange_rate`, opt-out marker `no_default_exchange_rate`), `AdminAccessLog.record()` accepts only listed non-personal `details` keys.

## Tests
- Before the fix (feat/r6-currency at 7afdaba, `pytest --create-db`): 23 failed, 1999 passed, 2 skipped. 21 = USD booking without a rate (fixture), 2 = audit log field set now has `details` (design change, explained in commit 581e568).
- After: 2029 passed, 0 failed, 2 skipped (pre-existing `skipTest` in `payments/tests/test_views.py:144` and `:362`).
- TDD proof (code removed, test files untouched, restored with `git checkout HEAD --`):
  - money (functions stubbed): 11 failed / 1 passed; with code 12 passed
  - CBU fetch (functions stubbed): 25 failed / 4 passed; with code 29 passed
  - rates (functions stubbed): 9 failed; with code 9 passed
  - migration guard (function stubbed): 3 errors; with code 3 passed
  - booking snapshot (bookings models/serializers/views at e61f0de): 19 failed / 2 passed
  - UZS payments (payments models/serializers/views/webhooks/adapters at e61f0de): 16 failed
  - UZS prices + currency rules (properties serializers/views, partner serializers at e61f0de): 14 failed / 2 passed
  - admin rate endpoints (admin_panel urls/views, currency/views at e61f0de): 14 failed / 1 passed
  - audit details whitelist (admin_panel/models.py at 7afdaba): 6 failed / 21 passed

## Security
- No live rate lookup in any request handler; client-sent currency/rate/amount ignored; audit log `details` whitelisted (no personal data).

## API/contract changes
- `.ai/API_CONTRACT.md` "2026-10-03 Currency" (Click unit note added 2026-10-05).

## Known issues
- Click amount unit (so'm) NOT verified from Click's own documentation; Payme and Click partial-refund rules and both adapters untested in a sandbox. See `.ai/RELEASE_CHECKLIST.md` "Unverified before production".
- Per-rate-plan `uzs_total` in availability not done (quote gives it).
- `feat/r6-currency` at the WIP commit 7afdaba was already merged into master by PR #4 (32dad37, 2026-10-03) while the suite was red; master was red until this checkpoint is merged.

## Next checkpoint
- R12 status additions: audit and plan (`.ai/PLAN_R12.md`), waiting for approval.

## Handoff
- `READY FOR FRONTEND: R6` in `.ai/HANDOFF.md` after the merge into master.
