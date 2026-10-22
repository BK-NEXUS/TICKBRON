# TICKBRON Backend Release Checklist

## Backend Main Plan (Checkpoints 1-20)
**Status:** READY
**Date:** 2026-09-21
**Owner:** Kolya

## Test Results
- **Full Test Suite:** 568 tests passed, 2 skipped
- **Test Coverage:** All core functionality tested
- **Test Execution Time:** ~2:49 minutes
- **Test Environment:** Django 4.2.7, Python 3.13.1, pytest 9.1.1

## Migration Status
- **Fresh Database Migration:** ✅ CLEAN
- **Migration Files Applied:** 27 migrations across 12 apps
- **Latest Migration:** payments.0002_alter_paymentauditlog_action
- **Missing Migrations:** None
- **Data Loss Risk:** None (only added new choice to existing field)

## OpenAPI Schema Status
- **Generation:** ✅ SUCCESSFUL
- **Output File:** schema.yml
- **Warnings:** 43 (17 unique) - non-critical type hints and serializer warnings
- **Errors:** 68 (17 unique) - graceful fallback for APIViews without serializers
- **Coverage:** All implemented endpoints documented

## Concurrency Check
- **Booking Engine Tests:** ✅ 24 tests passed
- **Double-Booking Prevention:** ✅ Confirmed
- **Transaction Safety:** ✅ Confirmed
- **State Machine Integrity:** ✅ Confirmed

## Permission Boundary Sweep
### Role-based Access Control
- **Anonymous Users:** ✅ Cannot access authenticated endpoints (403 returned)
- **Regular Users:** ✅ Cannot access admin/partner endpoints (403 returned)
- **Hotel-Owner Role:** ✅ Scoped to own properties only (404 for other properties)
- **Staff Users:** ✅ Can access admin endpoints but cannot create hotel-owner accounts (403)
- **Super-Admin:** ✅ Full admin access

### Data Isolation
- **Partner API:** ✅ Hotel-owners can only see/manage their own properties, rooms, rates
- **Payment API:** ✅ Users can only see their own payment transactions (queryset filtering)
- **Account API:** ✅ Users can only access their own favorites, reviews, history
- **Booking API:** ✅ Users can only access their own bookings
- **Admin API:** ✅ Staff/super-admin have appropriate scoping

### Permission Tests Coverage
- **partner/tests/test_partner_api.py:** 13 permission boundary tests
- **admin_panel/tests/test_admin_api.py:** 4 permission boundary tests
- **accounts/tests/test_views.py:** 3 permission boundary tests
- **bookings/tests/test_views.py:** 4 permission boundary tests
- **users/tests/test_views.py:** Authentication required by default
- **payments/tests/test_views.py:** User isolation via queryset filtering

## Security Review Confirmation
### Checkpoint 04 (Auth Security)
- ✅ Password complexity (12+ characters, complexity validation)
- ✅ Account lockout after 5 failed attempts (30-minute duration)
- ✅ Disposable email rejection
- ✅ IP tracking for login attempts
- ✅ Session-based authentication with secure cookies

### Checkpoint 15 (Payment Security)
- ✅ Webhook signature validation (Payme HMAC-SHA256, Click MD5)
- ✅ Timestamp validation (5-minute window)
- ✅ Replay attack prevention (duplicate event ID rejection)
- ✅ Idempotency support (duplicate key detection)
- ✅ No raw card data storage (tokens/references only)
- ✅ Audit trail (PaymentAuditLog)

### Checkpoint 18 (Partner Security)
- ✅ Hotel-owner role-based access control
- ✅ Property ownership scoping (owners can only access their own properties)
- ✅ Role-based endpoint protection
- ✅ Admin moderation endpoints for property approval

### Checkpoint 19 (Rate Limiting Security)
- ✅ Login endpoint: 10 requests per minute per IP
- ✅ Registration endpoint: 5 requests per minute per IP
- ✅ Payment initiation: 20 requests per minute per user
- ✅ Property search: 100 requests per minute per IP
- ✅ OTP endpoint: Not yet applicable (checkpoint 21 not implemented)
- ✅ Test mode detection to prevent test failures

## Environment Variables for Production

### Critical Security Variables (MUST BE SET)
- `SECRET_KEY` - Django secret key (generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DEBUG` - Set to `False` in production
- `ALLOWED_HOSTS` - Comma-separated list of allowed hostnames (e.g., `api.tickbron.uz,www.tickbron.uz`)

### Database Configuration
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port
- `DB_SSLMODE` - PostgreSQL SSL mode (default: `prefer`)

### CORS and Security
- `CSRF_TRUSTED_ORIGINS` - Comma-separated list of trusted origins
- `CORS_ALLOWED_ORIGINS` - Comma-separated list of allowed CORS origins
- `SECURE_SSL_REDIRECT` - Set to `True` for HTTPS enforcement
- `SESSION_COOKIE_SECURE` - Set to `True` for secure cookies
- `CSRF_COOKIE_SECURE` - Set to `True` for secure CSRF cookies
- `SECURE_HSTS_SECONDS` - HSTS max-age (default: 31536000)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` - Set to `True`
- `SECURE_HSTS_PRELOAD` - Set to `True`
- `SECURE_CONTENT_TYPE_NOSNIFF` - Set to `True`
- `SECURE_BROWSER_XSS_FILTER` - Set to `True`
- `X_FRAME_OPTIONS` - Frame options (default: `DENY`)

### Redis/Celery Configuration
- `REDIS_HOST` - Redis host (default: `localhost`)
- `REDIS_PORT` - Redis port (default: `6379`)
- `REDIS_DB` - Redis database number (default: `0`)
- `CELERY_BROKER_URL` - Celery broker URL (default: `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` - Celery result backend (default: `redis://localhost:6379/0`)

### Rate Limiting

### Monitoring

## Payments
There are no online payments: guests pay cash at the hotel (`.ai/PLAN_CASH_ONLY.md`). The payment settings (`PAYMENT_TEST_MODE`, Payme, Click, Visa keys) no longer exist, so there is nothing to configure. Old payment rows stay in the database as history.

## Deployment Readiness
- ✅ All migrations apply cleanly from scratch
- ✅ Full test suite passes
- ✅ Permission boundaries enforced
- ✅ Security measures in place
- ✅ Rate limiting configured
- ✅ OpenAPI schema documented
- ⚠️ SMS provider not yet implemented (checkpoint 21)

## Release Notes
- Backend main plan (checkpoints 1-20) is complete
- All core functionality implemented and tested
- Permission system properly scoped
- Security measures comprehensive
- Rate limiting protects sensitive endpoints
- Clean migration history
- Comprehensive test coverage

## Next Steps
1. Configure all security variables for production
2. Set up production database (PostgreSQL recommended)
3. Configure Redis for Celery
4. Set up SMS provider when checkpoint 21 is implemented
5. Perform production deployment testing
6. Configure monitoring and logging

## Known Limitations
- SMS functionality not yet implemented (checkpoint 21)
- Some OpenAPI warnings for type hints (non-critical)
- Admin endpoints use APIViews without serializers (graceful fallback handling)

## Blockers
None - Backend is ready for deployment with proper configuration.

## Security headers (R4, 2026-10-03)

What the Django app sends on every API response (`common/middleware.py` SecurityHeadersMiddleware, `django.middleware.security.SecurityMiddleware`, `XFrameOptionsMiddleware`; `config/settings.py:185-200`):

| Header | Value | Set by |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` (HTTPS requests only) | Django SecurityMiddleware + SecurityHeadersMiddleware (env `SECURE_HSTS_*`) |
| `X-Content-Type-Options` | `nosniff` | both |
| `X-Frame-Options` | `DENY` | XFrameOptionsMiddleware (env `X_FRAME_OPTIONS`) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | SecurityHeadersMiddleware |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | SecurityHeadersMiddleware |
| `Cross-Origin-Opener-Policy` | `same-origin` | Django default |
| Cookies | session + csrftoken: `HttpOnly`, `SameSite=Lax`, `Secure` when DEBUG is off | settings |

What the web server (nginx or similar, in front of both the SPA and `/api/`) must add, because the SPA's HTML/JS/CSS never pass through Django. For `/api/` it must also forward the client address and scheme, and overwrite (never append to) what the client sent:

```
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Host              $host;
```

- `Strict-Transport-Security: max-age=31536000; includeSubDomains` on every HTTPS response (add `preload` only after submitting the domain to hstspreload.org); redirect all `http://` to `https://` (or set `SECURE_SSL_REDIRECT=True` in Django and `SECURE_PROXY_SSL_HEADER` for the proxy).
- `Content-Security-Policy` for the SPA, starting point (fonts are self-hosted since 930214a; the map tile host `tile.openstreetmap.org` is listed below since the search map and the location picker, and add payment provider hosts when Payme/Click are integrated):
  `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'`
- Map privacy: the browser loads map tiles straight from OpenStreetMap, so OSM sees the visitor's IP address and the area viewed; the privacy policy (legal texts) must say so. The OSM tile policy needs the visible attribution (set in `components/mapTiles.ts`) and is meant for light use; plan a tile provider or own tile server before heavy traffic.
- Clickjacking: `frame-ancestors 'none'` in the CSP above, plus `X-Frame-Options: DENY` for older browsers (SPA responses).
- `X-Content-Type-Options: nosniff` and `Referrer-Policy: strict-origin-when-cross-origin` on SPA and `/media/` responses.
- `/media/` (uploaded photos): serve with `Content-Disposition: inline`, the image MIME type from the file extension only (jpg/png/gif/webp), `nosniff`, no script execution, and no directory listing.
- Remove `Server` / `X-Powered-By` version banners; limit request body size. A complete reference file is `deploy/nginx.conf.example` (1 MB for JSON, 12 MB only for photo upload). Django also refuses a JSON body over 4 MB and an upload over 12 MB (413) from the Content-Length header.
- Install runtime dependencies from `backend/requirements.txt`; `requirements-dev.txt` (tests, linters) is for development and CI only. CI is `.github/workflows/ci.yml` (tests, lint, build, `pip-audit`, `npm audit --omit=dev`).

## Production checklist (R4, 2026-10-03)

### Environment variables (the app refuses to start without the starred ones being safe)
- [ ] `DEBUG=False` (the app also refuses `DEBUG=True` when `ALLOWED_HOSTS` lists a public domain)
- [ ] `FRONTEND_URL`* the https:// address of the site (reset links point to it) and `EMAIL_HOST`* (+ `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`): password reset e-mails are sent through it. A Celery worker must run, the mail is sent by a task
- [ ] `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALERT_CHAT_ID`: alerts for locked accounts and server errors (empty = no alerts; add the bot to the chat first)
- [ ] `SECRET_KEY`* random, 50+ characters (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`), not the `.env.example` value
- [ ] `ALLOWED_HOSTS`* real host names, no `*`
- [ ] `CORS_ALLOWED_ORIGINS`* and `CSRF_TRUSTED_ORIGINS`* `https://` origins of the SPA only
- [ ] `SECURE_SSL_REDIRECT=True`* (refused otherwise)
- [ ] `NUM_PROXIES`* must be set explicitly: 0 = no proxy, 1 = one nginx/load balancer that appends to `X-Forwarded-For`. Unset or wrong, every visitor shares one IP (login throttle, lockout and promotion counters collapse, anyone can lock any known email)
- [ ] `USE_X_FORWARDED_PROTO=True`* whenever `NUM_PROXIES` > 0 (nginx must overwrite `X-Forwarded-Proto`); without it Django sees http, the https redirect loops and HSTS is never sent
- [ ] `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE`* stay True (default); `USE_REDIS_CACHE`* stays True (default)
- [ ] `SECURE_HSTS_PRELOAD` stays False until the owner decides to submit the domain to hstspreload.org (hard to undo); `SESSION_COOKIE_AGE` defaults to 7 days
- [ ] `DB_*` with `DB_SSLMODE`* = `require`, `verify-ca` or `verify-full` if the database is on another host (the app refuses `disable`, `allow`, `prefer`)
- [ ] `REDIS_URL` / `CELERY_*` (cache must be shared Redis: throttles and login lockout live there)
- [ ] `THROTTLE_ANON_RATE` / `THROTTLE_USER_RATE` left at defaults unless measured

### Test modes off
- [ ] `SMS_TEST_MODE=False`* (True returns OTP codes in responses)
- [ ] `scripts/checkpoint_checks/*.py` scripts and `scripts/smoke_test.py` are never run against production (they enable test modes)

### Demo data
- [ ] Never run `seed_demo` / `seed_demo_stats` in production (they refuse when DEBUG is off)
- [ ] If the production database was ever copied from a dev database, delete every `*@tickbron.demo` account and the demo hotels before launch: `User.objects.filter(email__endswith='@tickbron.demo')`

### HTTPS and server headers
- [ ] Valid TLS certificate, HTTP→HTTPS redirect, HSTS (see "Security headers" above)
- [ ] CSP, frame-ancestors, nosniff, Referrer-Policy on SPA responses; safe `/media/` serving
- [ ] `/api/docs/`, `/api/redoc/`, `/api/schema/` blocked at the proxy or limited to staff (SECURITY_REVIEW L-2)

### Database
- [ ] Application DB user with least privilege: owner of the `tickbron` schema objects only for migrations; at runtime CONNECT + SELECT/INSERT/UPDATE/DELETE on app tables, no SUPERUSER / CREATEDB / CREATEROLE (CREATEDB is needed only by the test runner on dev machines)
- [ ] Daily `pg_dump -Fc` backups kept off the server (e.g. 14 daily + 8 weekly), restore tested at least once; backup before every migration
- [ ] `python manage.py migrate` and `python manage.py check --deploy` (must print "no issues") on each release

### Real credentials still missing (owner decision / contracts)
- [ ] Eskiz (SMS for OTP): API credentials and sender id; until then OTP login cannot work in production (`SMS_TEST_MODE` must stay False)


## Currency and exchange rates (R6, 2026-10-03)

Hotels are priced in USD or UZS; guests are always charged in UZS (Payme and Click take only UZS). A USD hotel cannot be booked until an exchange rate exists (503 `exchange_rate_unavailable`, nothing reserved).

### First deploy (once)
- [ ] Backup first: `pg_dump -Fc` (the R6 migrations add the booking charge snapshot and backfill every existing booking)
- [ ] `python manage.py migrate`. The first R6 migration (`currency.0001`) STOPS with nothing changed if any property, room type or rate plan is priced in a currency other than USD/UZS, and lists them. Fix those rows (decide the real USD or UZS price with the hotel owner), then run `migrate` again.
- [ ] `python manage.py fetch_exchange_rates` right after the migration: stores today's CBU USD rate so USD hotels can be booked at once. It prints the rate, or why it failed. The server must reach `https://cbu.uz` (outbound HTTPS).
- [ ] Celery **beat** and a worker are running: `currency.tasks.fetch_exchange_rates` runs daily at 09:00 and 18:00 Asia/Tashkent (`CELERY_BEAT_SCHEDULE`), with 3 retries 10 minutes apart.
- [ ] Check `GET /api/v1/admin-panel/exchange-rates/status/` as a super-admin: `rate` set, `stale: false`, `last_error: null`.

### Manual "fetch rate now"
- `python manage.py fetch_exchange_rates` (same code as the scheduled task; safe to run any time, the same CBU date is stored once).

### Settings (environment, defaults shown)
- `FX_STALE_AFTER_DAYS=3`: an older rate is still used but marked `stale: true` (quote, booking, status) and logged as a warning.
- `FX_MAX_CHANGE=0.10`: a new rate more than 10% away from the current one is stored as `rejected` and not used until a super-admin accepts it (`POST /api/v1/admin-panel/exchange-rates/{id}/accept/`, written to the admin audit log with the old and new rate).
- `FX_MIN_RATE=1000`, `FX_MAX_RATE=100000`: accepted range of so'm per USD; anything outside is rejected.
- `FX_FETCH_TIMEOUT=10` (seconds).

### When the rate is stale or missing
- [ ] Look at `last_error` in the status endpoint (network, CBU answer format, rejected jump), run `fetch_exchange_rates` by hand, and if a correct rate was rejected for a real jump, accept it as super-admin.

### Unverified before production (R6, 2026-10-05)
Payment amount units, as implemented in `backend/payments/adapters.py`:
- Payme: tiyin (1 so'm = 100 tiyin). Confirmed in Payme's own Merchant API documentation ("Сумма платежа (в тийинах)").
- Click: so'm as a decimal number ("1000.00"). **NOT verified** from Click's own documentation; the only source so far is the amount format used in Click's integration library. Treat it as an assumption.

Before any real payment, each item below must be tested end to end in the provider's sandbox with real merchant credentials (none of this is verified yet):
- [ ] Click amount unit (so'm vs tiyin) on create, prepare/complete webhooks and refund.
- [ ] Payme partial-refund rules (allowed at all, how many times, minimum amount, what the webhook sends).
- [ ] Click partial-refund rules (same questions).
- [ ] The Payme adapter end to end: create, webhook signature and amount check, full refund, partial refund, failure and retry.
- [ ] The Click adapter end to end: the same steps.

## Business date and auto-completion (R12 phase 1, 2026-10-05)

- [ ] `TIME_ZONE` stays `UTC`. `BUSINESS_TIME_ZONE` (env, default `Asia/Tashkent`) decides "today" for booking check-in, statistics and auto-completion. Hotels in other countries use the same business date for now.
- [ ] **Celery beat, a worker and Redis must run in production.** `CELERY_TIMEZONE = BUSINESS_TIME_ZONE`: beat times in `CELERY_BEAT_SCHEDULE` are Tashkent times (exchange rates 09:00 and 18:00, auto-completion 00:05). Without beat, confirmed stays never become completed and the Status "stayed" numbers stay at 0.
- [ ] **Backup first: `pg_dump -Fc` before `migrate`, every time.** R12 phase 1 migrations: `bookings/0009` (auto-completion run history), `payments/0003` (Refund table), `payments/0004` (backfills a `succeeded` Refund for every `refunded` / `partially_refunded` payment; its reverse deletes only those rows), `admin_panel/0006` (audit actions), `accounts/0002` (notification `code` / `params`). All reversible.
- [ ] Once after deploy: `python manage.py complete_finished_stays --dry-run` (prints how many past stays are still `confirmed`), then without `--dry-run` (completes them; nothing touches pending, cancelled or no_show).
- [ ] Check `GET /api/v1/admin-panel/auto-completion/status/` as a super-admin the next morning: `last_run.finished_at` after 00:05 Tashkent, `failed: 0`, `waiting: 0`.

## Refunds (R12 phase 1, 2026-10-06)

- [ ] **Partial refunds with Payme, Click and Visa are NOT verified** (`SUPPORTS_PARTIAL_REFUND = None` in `payments/adapters.py`). Until a partial refund has been tested in each provider's sandbox, every partial refund skips the provider and is stored as `needs_manual`: staff pay it by hand and close it with `POST /api/v1/admin-panel/refunds/{id}/mark-done/` (`provider_reference` required). After a successful sandbox test, set `SUPPORTS_PARTIAL_REFUND = True` on that adapter only (with a test).
- [ ] Full refunds call the provider after the refund row is committed. A provider failure leaves the refund `failed`; super-admins retry it from `GET /api/v1/admin-panel/refunds/needs-attention/`.
- [ ] Someone on staff checks the needs-attention list daily (failed, needs_manual, pending for more than an hour).
- [ ] `migrate` prints `Refund backfill: N refund row(s) created, M payment(s) skipped`. Skipped = a `partially_refunded` payment without an audit row (amount unknown, never invented) or audit amounts above the payment: check each one by hand and record its refund with the real amount.

## No-show reports and refund (R12b, 2026-10-07)

- [ ] **Backup first: `pg_dump -Fc` before `migrate`.** R12b migrations: `bookings/0010` (NoShowReport, `Booking.no_show_refund_percent`; existing bookings get 0), `admin_panel/0008` (audit actions). Both reversible.
- [ ] **Partial refunds are unverified with Payme, Click and Visa.** A no-show refund is 50% of the payment, so in real mode it is stored as `needs_manual` and staff pay it by hand (see Refunds above). Verify each provider's partial refund in its sandbox before turning it on.
- [ ] **A lawyer must review the refund wording** shown to guests (`no_show_refund_statement`, in every language) and the owner/staff texts before launch; the 50% promise is a contract term.
- [ ] Settings to confirm: `NO_SHOW_REFUND_PERCENT` (50), `NO_SHOW_REPORT_WINDOW_DAYS` (7), `NO_SHOW_FLAG_*`, `THROTTLE_NO_SHOW_REPORT_RATE` (20/hour).


## Hotel promotions (R10, 2026-10-09)

- [ ] **Backup first: `pg_dump -Fc` before `migrate`.** R10 migrations: `promotions/0001` (two new tables) and `admin_panel/0009` (audit actions). Both reversible; no existing table gets a column.
- [ ] **Celery beat must be running** (task `promotions.tasks.end_expired_promotions`, 00:10 Asia/Tashkent). Without it statuses in the admin list stay stale; guests are still served correctly (computed from dates).
- [ ] **Redis must be the cache in production** (`USE_REDIS_CACHE`): view and click counts are deduplicated there. With a failing cache nothing is counted (a warning `Promotion counter skipped` is logged).
- [ ] A lawyer confirms the exact "Reklama" label wording and advertising-law requirements in Uzbekistan (the frontend label is an i18n key).
- [ ] Prices, invoices and refunds for advertising are handled outside the platform; the super-admin records `mark-paid` and the agreed price.


## "Kelmadi" screens (R12b frontend, 2026-10-10)

- [ ] **A lawyer must review the guest-facing refund sentence** (`no_show_refund_statement` in uz, ru, en) and the owner and staff dialog texts (`noShow.*`, `noShowAdmin.*`) before launch.
- [ ] Open client decisions that change this feature: who pays the provider fee, whether it applies to non-refundable rates, whether the hotel keeps the money or TICKBRON refunds from it.


## Final pass (R15, 2026-10-18)

Results on the code of this date (`master` after PR #54, plus the E2E changes of the R15 PR):
- **Backend:** `pytest --create-db`: 3153 passed, 0 failed (41 min 32 s), `makemigrations --check` clean.
- **Frontend:** `npm test` 170 files, 1954 tests passed; `npm run lint` clean; `npm run build` clean (first load 85 KB app + 59 KB React, gzip).
- **E2E against the real stack** (seed_demo + seed_demo_stats, Chromium): 29 of 29 passed (25 in the full run; the 3 crawls and promotions J5 passed in a second run after two environment fixes below). The crawl visits every page as guest, owner and admin at 1440px and 390px: no 404, dead button or console error.
- **Load test** (R14, `.ai/PERFORMANCE_REPORT.md`): 200 users, 0 failures, server-side p95 search 163 ms, booking 36 ms.

How to run the E2E (`frontend/playwright.config.ts`): backend with `seed_demo` and `seed_demo_stats`, `THROTTLE_ANON_RATE` and `THROTTLE_USER_RATE` very high, and the per-IP limits switched off (they are fixed: search 100/min, promotions 60/min, login 10/min; the E2E sends everything from one address), frontend `npm run dev` on port 3000, then `npm run test:e2e`. `E2E_CHROMIUM_PATH` points to a Chromium when Playwright's own is not installed. The crawl answers the OpenStreetMap tiles itself, so it needs no internet.

### Before the first production start (everything added since the first checklist)
- [ ] **Backup first: `pg_dump -Fc` before `migrate`.** Migrations added since 2026-10-10, all additive or reversible: `bookings/0011` and `properties/0014` (free cancellation: rate-plan terms, cancellation snapshot on bookings, refund reason `cancel`), `properties/0015` (`RoomType.is_vip`), `admin_panel/0010`, `0011` (audit actions, IP, payment reads), `users/0007`-`0009` (unique verified phone, hashed codes, SMS login columns dropped). No migration came with R12 additions, R14 or R15.
- [ ] New library **XlsxWriter 3.2.9** (Excel export, `requirements.txt`); `pip install -r requirements.txt` on the server.
- [ ] CBU exchange rates are loaded (R6 section above); a hotel priced in USD or EUR refuses bookings with 503 `exchange_rate_unavailable` until a rate exists.
- [ ] Map tiles come from `tile.openstreetmap.org` (CSP `img-src`, privacy note above): the guest's browser contacts OpenStreetMap on pages with a map. Decide whether the OSM usage policy fits the expected traffic or a paid tile provider is needed.
- [ ] Size the server from the load test: 4 shared cores gave about 86 requests/s; plan more workers/cores and run the same Locust file (`backend/scripts/loadtest/README.md`) on the real server before launch.
- [ ] Lawyer review of the refund wording (cancellation and no-show) and the "Reklama" label, as listed above.

### Open decisions of the owner
- UZS/USD selector on the front end: the backend sends no USD price. Add `base_price_usd_approx` or remove the selector?
- Remove the free-text location compatibility fields from the property API (kept for the old front end)?
- Redis search cache and image thumbnails were left out on purpose (R14 report); thumbnails belong to the "owners upload photos" feature, which does not exist yet.

### Found, not fixed (see HANDOFF for each)
- Owners cannot upload photos; photos are not served by a media route in development.
- The guest bookings list is not paginated (owner decision, R14 report).
- Provider partial refunds are unverified (Payme, Click, Visa).
- The new R12 cards and the Excel buttons, and the VIP badge, were checked by tests only, not by eye at 390px and 1440px (the crawl does load the pages and finds no errors).

## Cash bookings (stage 2 of PLAN_CASH_ONLY, 2026-10-22)
- [ ] Backup first (`pg_dump -Fc`): migration `bookings/0012_cash_arrival` adds two columns and confirms `pending` bookings still inside their 15-minute window.
- [ ] Celery **beat** and a worker run: `bookings.tasks.cancel_unarrived_bookings` every 10 minutes cancels a confirmed booking whose guest is not marked "arrived" `ARRIVAL_GRACE_HOURS` (default 2) after the arrival time. Without beat nothing is ever cancelled.
- [ ] Hotels are told to press "Guest arrived" in Status > arrivals; otherwise guests who did come are cancelled.
- [ ] `MAX_UPCOMING_BOOKINGS_PER_GUEST` (5, `bookings/views.py`) is the only brake on one account taking rooms without paying: confirm the number.

