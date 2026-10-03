# R4 Security Review (2026-10-03, Kolya's agent, branch feat/r4-security)

Scope: backend (`backend/`), all endpoints on master `976ea80` plus R2 geography, Status, room inventory and block endpoints. Frontend read-only (`npm audit`, card data check).
Severity: Critical / High (fixed now, each with a proof test that failed before the fix) / Medium / Low (listed, open unless marked).

## Summary

| Severity | Found | Fixed | Open |
|---|---|---|---|
| Critical | 1 | 1 | 0 |
| High | 4 | 4 | 0 |
| Medium | 6 | 0 | 6 |
| Low | 7 | 1 | 6 |

## Critical

### C-1 Vulnerable, end-of-life dependencies — FIXED ce806e3
- Evidence: `pip-audit -r requirements.txt` on master: Django 4.2.7 (4.2 LTS is end of life; 40+ advisories, including CVE-2025-64459 SQL injection through `QuerySet.filter(**kwargs)` `_connector`, CVE-2024-42005 SQL injection in `values()`/`values_list()` on JSONField, several DoS issues, and 2026 advisories fixed only in 5.2.x), djangorestframework 3.14.0 (PYSEC-2026-1304, -3827, -3828), cryptography 41.0.7 (9 advisories), python-dotenv 1.0.0 (PYSEC-2026-2270), black 23.11.0 (dev tool).
- Fix: Django 5.2.17 (LTS), DRF 3.18.1, cryptography 50.0.2, python-dotenv 1.2.4, black 26.5.1; compatible bumps of drf-spectacular 0.30.0, django-cors-headers 4.9.0, django-redis 6.0.0, django-debug-toolbar 6.0.0. After: `pip-audit` "No known vulnerabilities found"; full suite green (see Test results).

## High

### H-1 Payment currency was taken from the client — FIXED 0eaaa59
- Evidence: `payments/serializers.py` `PaymentTransactionCreateSerializer.validate` compared only `amount` with `booking.total_price`; `currency` was any client value, so a 300 USD booking could be paid as 300 UZS.
- Fix: currency must equal `booking.currency` (400 otherwise). Proof: `payments/tests/test_r4_payment_currency.py`.

### H-2 Password rules not enforced — FIXED 4a809e0
- Evidence: `users/serializers.py` (register) and `admin_panel/serializers.py` (create hotel owner) only had `min_length=12`; `users.validators.StrongPasswordValidator` was never used and `AUTH_PASSWORD_VALIDATORS` never ran. `aaaaaaaaaaaa`, `password1234`, `847261930475` were accepted (proof test: 11 failures before).
- Fix: both serializers run `validate_password` (Django min length / common / numeric / similarity + StrongPasswordValidator: upper, lower, digit, special, no common words; the 3-in-a-row sequence rule is off because it rejects random long passphrases). Proof: `users/tests/test_r4_password_strength.py`.

### H-3 Production started with insecure settings — FIXED 3ff44b6
- Evidence: with `DEBUG=False`, `SMS_TEST_MODE=True` was accepted and `users/services.py` returned every OTP code in the `/auth/otp/request/` response (log in as any phone number, including staff); the `.env.example` placeholder `SECRET_KEY` and short keys were accepted; `CORS_ALLOWED_ORIGINS` / `CSRF_TRUSTED_ORIGINS` silently defaulted to `http://localhost:3000`; `ALLOWED_HOSTS=*` was accepted. Code fallbacks `getattr(settings, 'SMS_TEST_MODE', True)` / `PAYMENT_TEST_MODE, True`.
- Fix: end of `config/settings.py` refuses to start (DEBUG off, not a test run) on any of these; fallbacks are False. Proof: `core/tests/test_r4_production_config.py` (10 refusals, good config starts, DEBUG keeps local defaults).

### H-4 Unbounded stay length and bulk ranges (one-request DoS) — FIXED cc94321
- Evidence: rate plans may have `max_nights=NULL`; `bookings/pricing.py` `quote_stay` built a Python list of every night and an SQL `IN` list; anonymous `GET /properties/{id}/quote/?check_out=9999-12-31` took most of a 78 s test run; booking create (lock=True) created a RoomInventory row per missing night first. Partner `bulk-price`, `room-inventory/bulk` and `blocks` wrote one row per day with no cap.
- Fix: `MAX_STAY_NIGHTS = 365` checked before any inventory query; the three bulk ranges use the same cap. Proof: `bookings/tests/test_r4_stay_length_limit.py` (8 tests, now 5 s).

## Medium (open)

### M-1 Emails are case-sensitive
- Evidence: `users/models.py:26` `normalize_email` lowercases only the domain; login looks up `email=` exactly (`users/views.py:133`). `Alice@x.uz` and `alice@x.uz` can be two accounts.
- Fix: lowercase emails on save, case-insensitive unique constraint (migration after a duplicate check), `iexact` lookups.

### M-2 Webhooks without a timestamp are accepted
- Evidence: `payments/webhooks.py:121` validates the timestamp only `if timestamp`; replay protection then relies on the event id alone.
- Fix: require a timestamp (or provider-specific replay data) when the real Payme/Click formats are integrated.

### M-3 Expired webhook blocks the genuine retry
- Evidence: `payments/webhooks.py:104-126` stores the event under its real `provider_event_id` before the timestamp check; a later valid delivery of the same id is answered "already processed".
- Fix: check the timestamp before creating the event, or store expired ones under a synthetic id like invalid signatures.

### M-4 Unbounded lists
- Evidence: `GET /admin-panel/users/` returns every user (`admin_panel/views.py` `AdminUserViewSet.list`, no pagination); `GET /partner/bookings/` returns all bookings with one extra query per booking (`partner/views.py:354`); `GET /bookings/` (own bookings) unpaginated; `GET /properties/{id}/availability/` without dates returns every DateInventory row (`properties/serializers.py:528-553`).
- Fix: paginate (page size cap), require/cap the availability date range. Frontend contract change, so coordinate (R14 performance).

### M-5 Registration reveals existing accounts
- Evidence: `POST /auth/register/` answers duplicate email (409) / phone ("already registered") differently from success (HANDOFF auth section). Login and OTP do not enumerate.
- Fix: same response for new and existing contacts plus a notification to the existing owner (needs email/SMS sending).

### M-6 Staff can edit any guest's review through the guest endpoint
- Evidence: `accounts/views.py:117-126` returns all reviews to `is_staff`, and the ModelViewSet allows PUT/PATCH/DELETE, so staff rewrite review text as if the guest wrote it; not in any audit log.
- Fix: staff read-only on `/me/reviews/`; moderation through an admin endpoint that only changes `status` and is audit-logged.

## Low

- L-1 OTP codes stored in plain text (`users/models.py:196`); a database reader sees live codes (5 min). Fix: store a hash. Open.
- L-2 API docs public in production (`/api/docs/`, `/api/redoc/`, `/api/schema/`, `config/urls.py`). Fix: staff-only or DEBUG-only. Open.
- L-3 Login CSRF: anonymous login/register/OTP POSTs are not CSRF-checked (DRF checks CSRF only for session-authenticated requests); an attacker page can log a victim into the attacker's account. SameSite=Lax limits other cases. Fix: `ensure_csrf_cookie` + enforce on these views. Open.
- L-4 `PUT/PATCH /me/favorites/{id}/` can switch `property` to an inactive property (`accounts/serializers.py:28-31`, the active check is only on create). Open.
- L-5 Validation errors are logged with `str(exc)` (`common/exception_handlers.py:75`) and may contain submitted values (e.g. an email). Fix: log field names only. Open.
- L-6 Uploaded photos keep the original file name (`common/storage.py:224`). Fix: random file names. Open.
- L-7 `manage.py check --deploy` reported 63 drf-spectacular schema warnings (W001/W002, documentation only). FIXED (SCHEMA_COMMIT).

## Verified OK (with evidence)
- Every endpoint and role: `core/tests/test_r4_permission_matrix.py` walks the URL resolver (164 method/path pairs x 5 roles: anonymous, guest, hotel owner, staff, super-admin), fails on any unclassified new route. Geography admin and create-hotel-owner are super-admin only; Status, customers, support lookup, audit log are staff-only; partner incl. room-inventory/blocks/status is owner/staff.
- IDOR: `core/tests/test_r4_idor.py` (guest booking, payment, favorite, review, notification, history: read/change/delete/cancel/pay/review by another guest all 404/400) plus `partner/tests/test_access_matrix.py` (owner isolation).
- Roles: `UserUpdateSerializer` cannot set role/is_staff/is_superuser (`users/serializers.py`); hotel owners only via super-admin `create-hotel-owner`.
- Serializers: `UserSerializer` (own profile only) shows `is_staff`/`is_superuser`/role, never password hashes; partner bookings show guest name only.
- Prices: booking totals computed by `bookings/pricing.py` (no price field in `BookingCreateSerializer`); payment amount and (now) currency must equal the booking.
- Webhooks: signature checked before the event is recorded, constant-time compare (`payments/adapters.py:102`), fail closed without a secret, idempotent by event id, amount checked (`payments/webhooks.py:293`), row locks.
- `/confirm/` works only with `PAYMENT_TEST_MODE` and `DEBUG` (`payments/views.py`); both test modes default False and `.env.example` keeps them False (`core/tests/test_settings_defaults.py`), production now refuses them (H-3).
- Inventory locking: `select_for_update` in create/cancel/expire and RoomInventory; `bookings/tests/test_concurrency.py` passes on PostgreSQL.
- Refund + cancel: implemented atomically with the payment row locked (55a68a4, `payments/tests/test_r4_refund_cancel_booking.py`).
- OTP: CSPRNG 6 digits, 5 min expiry, 3 attempts per code, single use, `hmac.compare_digest` (`users/models.py:188-228`), code only in test-mode responses, never logged (masked phone).
- Lockout and limits: per account+IP (5 / 30 min) and per account (20), login 10/min per IP, register 5/min, OTP 3/min request and 5/min verify keyed by the normalized phone (`users/views.py:55-89`), so other spellings share a bucket; same message for unknown/locked/wrong (`users/views.py:28`), dummy hash on unknown email for timing.
- Sessions: HttpOnly + SameSite=Lax cookies, Secure when DEBUG is off (`config/settings.py:187-192`), CSRF on authenticated state changes, logout flushes the session.
- SQL: no `.raw()`, `.extra()` or `RawSQL`; `connection.cursor()` only in `db_health` with fixed SQL.
- Uploads: 10 MB, jpg/png/gif/webp, Pillow verifies the content (`ImageField`), Django storage strips path components.
- Logs: request log has user id not email, phones masked, no OTP/passwords/tokens; 500 responses carry no details unless DEBUG (`common/exception_handlers.py:40`).
- Customer data endpoints (customers, support lookup, status users, users list) are staff-only and now audit-logged (dea62c2).
- Seed commands refuse to run without DEBUG (`core/management/commands/seed_demo.py:82`, `seed_demo_stats.py:88`).
- Throttles: anonymous 2000/hour (shared-IP browsing), strict scopes on login/register/OTP/payments (`core/tests/test_settings_defaults.py::test_sensitive_endpoints_keep_their_strict_limits`).

## Frontend (read-only)
- No card form on master yet (R8); payment request has no card fields (`frontend/src/adapters/paymentAdapter.ts:31`).
- `npm audit`: 18 vulnerabilities (3 critical, 11 high, 4 moderate), listed in HANDOFF.md "Frontend needs".
