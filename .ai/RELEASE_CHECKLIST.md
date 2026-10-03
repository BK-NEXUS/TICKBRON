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
- `DB_ENGINE` - Database engine (default: `django.db.backends.sqlite3`, production: `django.db.backends.postgresql`)
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

### Payment Provider Credentials (REAL CREDENTIALS REQUIRED)
- `PAYMENT_TEST_MODE` - Set to `False` for production payments
- `PAYME_MERCHANT_ID` - Payme merchant ID from Payme dashboard
- `PAYME_SECRET_KEY` - Payme secret key from Payme dashboard
- `CLICK_SERVICE_ID` - Click service ID from Click dashboard
- `CLICK_SECRET_KEY` - Click secret key from Click dashboard
- `CLICK_MERCHANT_ID` - Click merchant ID from Click dashboard
- `VISA_API_KEY` - Visa API key from Visa developer portal
- `VISA_SECRET_KEY` - Visa secret key from Visa developer portal

### Redis/Celery Configuration
- `REDIS_HOST` - Redis host (default: `localhost`)
- `REDIS_PORT` - Redis port (default: `6379`)
- `REDIS_DB` - Redis database number (default: `0`)
- `CELERY_BROKER_URL` - Celery broker URL (default: `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` - Celery result backend (default: `redis://localhost:6379/0`)

### SMS Provider (Checkpoint 21 - Not Yet Implemented)
- `SMS_PROVIDER_API_KEY` - SMS provider API key (when checkpoint 21 is implemented)
- `SMS_PROVIDER_SENDER_ID` - SMS provider sender ID (when checkpoint 21 is implemented)

### Rate Limiting
- `RATELIMIT_ENABLE` - Set to `True` for production rate limiting

### Monitoring
- `DATABASE_HEALTH_CHECK_ENABLED` - Set to `True` for database health checks
- `DATABASE_HEALTH_CHECK_INTERVAL` - Health check interval in seconds (default: `60`)

## Current PAYMENT_TEST_MODE Value
**Default:** `False` (code and `.env.example`). Since R4 (2026-10-03) the app refuses to start with `DEBUG=False` and `PAYMENT_TEST_MODE=True` or `SMS_TEST_MODE=True`.

## Deployment Readiness
- ✅ All migrations apply cleanly from scratch
- ✅ Full test suite passes
- ✅ Permission boundaries enforced
- ✅ Security measures in place
- ✅ Rate limiting configured
- ✅ OpenAPI schema documented
- ⚠️ Payment test mode active (requires real credentials for production)
- ⚠️ SMS provider not yet implemented (checkpoint 21)

## Release Notes
- Backend main plan (checkpoints 1-20) is complete
- All core functionality implemented and tested
- Payment system ready for live credentials
- Permission system properly scoped
- Security measures comprehensive
- Rate limiting protects sensitive endpoints
- Clean migration history
- Comprehensive test coverage

## Next Steps
1. Set real payment provider credentials in production environment
2. Set `PAYMENT_TEST_MODE=False` for production
3. Configure all security variables for production
4. Set up production database (PostgreSQL recommended)
5. Configure Redis for Celery
6. Set up SMS provider when checkpoint 21 is implemented
7. Perform production deployment testing
8. Configure monitoring and logging

## Known Limitations
- SMS functionality not yet implemented (checkpoint 21)
- Payment system in test mode (requires live credentials)
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

What the web server (nginx or similar, in front of both the SPA and `/api/`) must add, because the SPA's HTML/JS/CSS never pass through Django:

- `Strict-Transport-Security: max-age=31536000; includeSubDomains` on every HTTPS response (add `preload` only after submitting the domain to hstspreload.org); redirect all `http://` to `https://` (or set `SECURE_SSL_REDIRECT=True` in Django and `SECURE_PROXY_SSL_HEADER` for the proxy).
- `Content-Security-Policy` for the SPA, starting point (fonts are self-hosted since 930214a; add the map tile host when R11 adds Leaflet, and payment provider hosts when Payme/Click are integrated):
  `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'`
- Clickjacking: `frame-ancestors 'none'` in the CSP above, plus `X-Frame-Options: DENY` for older browsers (SPA responses).
- `X-Content-Type-Options: nosniff` and `Referrer-Policy: strict-origin-when-cross-origin` on SPA and `/media/` responses.
- `/media/` (uploaded photos): serve with `Content-Disposition: inline`, the image MIME type from the file extension only (jpg/png/gif/webp), `nosniff`, no script execution, and no directory listing.
- Remove `Server` / `X-Powered-By` version banners; limit request body size (e.g. `client_max_body_size 11m` for 10 MB photos).

## Production checklist (R4, 2026-10-03)

### Environment variables (the app refuses to start without the starred ones being safe)
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY`* random, 50+ characters (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`), not the `.env.example` value
- [ ] `ALLOWED_HOSTS`* real host names, no `*`
- [ ] `CORS_ALLOWED_ORIGINS`* and `CSRF_TRUSTED_ORIGINS`* `https://` origins of the SPA only
- [ ] `SECURE_SSL_REDIRECT=True` (or redirect at the proxy); `NUM_PROXIES` = number of proxies that append to `X-Forwarded-For` (rate limits and lockout key on the client IP)
- [ ] `DB_*` with `DB_SSLMODE=require` if the database is on another host
- [ ] `REDIS_URL` / `CELERY_*` (cache must be shared Redis: throttles and login lockout live there)
- [ ] `THROTTLE_ANON_RATE` / `THROTTLE_USER_RATE` left at defaults unless measured

### Test modes off
- [ ] `SMS_TEST_MODE=False`* (True returns OTP codes in responses)
- [ ] `PAYMENT_TEST_MODE=False`* (True fakes provider calls; `/confirm/` additionally needs DEBUG)
- [ ] `config/*_security_check*.py` scripts and `scripts/smoke_test.py` are never run against production (they enable test modes)

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
- [ ] Payme: `PAYME_MERCHANT_ID`, `PAYME_SECRET_KEY` (and real API integration + webhook status mapping)
- [ ] Click: `CLICK_SERVICE_ID`, `CLICK_MERCHANT_ID`, `CLICK_SECRET_KEY`
- [ ] Visa: `VISA_API_KEY`, `VISA_SECRET_KEY` (card payments must use provider tokenization; card data never touches our backend)
- [ ] Eskiz (SMS for OTP): API credentials and sender id; until then OTP login cannot work in production (`SMS_TEST_MODE` must stay False)

