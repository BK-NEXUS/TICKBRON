# PLAN SECURITY: batch 2 item N-1 (phone pre-hijacking)

Status: approved by the owner on 2026-10-10 ("N-1 ishlashni boshla"); stage 1 and stage 2 implemented (migration `users/0007_phone_number_unique_when_verified`, `pg_dump` taken before it).

## Problem
Registration and profile update accept any unclaimed phone number with no proof of ownership. SMS login never checked `phone_verified`, so an attacker could register with a victim's number; when the victim later signed in by SMS, the code logged them into the attacker's account. The global unique constraint also let an attacker squat a number so its real owner could not register.

## Stage 1 (done): close the takeover, no schema change
- SMS login (`otp/request`, `otp/verify`) acts only on accounts whose phone is verified; unverified numbers get the same generic answer and no code.
- New authenticated endpoints `POST /auth/phone/verify/request/` and `/confirm/` prove the account's own number (number taken from the account, same throttle/lockout/code storage as OTP).
- `phone_verified` is returned on the user object; profile shows the state with a verify dialog; login page explains the rule.

## Stage 2 (done): stop number squatting, one migration
- Replace the global unique on `User.phone_number` with a partial unique constraint (`phone_verified = true`). Unverified claims no longer block the real owner.
- Verifying a number clears the same number from other users' unverified claims (one transaction).
- Uniqueness validation and phone lookups consider verified holders only.
- Migration is new and reversible; `pg_dump` first.

## Out of scope
Card data: nothing here touches cards; payment tokens come from the provider and no PAN/CVV is stored.

## Step 2 of the 2026-10-12 work order: small batch (done)
- 2a N-17: admin writes are in `AdminAccessLog`: property approve/reject/suspend/region, hotel-owner creation, amenity and category CRUD, geography CRUD and reorder, internal notes, refund creation (`admin_panel/audit.py` mixin, `DETAIL_KEYS` + `object_id`, `level`; migration `admin_panel/0010_audit_admin_actions`, choices only, reversible, `pg_dump` taken).
- 2b N-8/L-3: `common/csrf.enforce_csrf` on login, register, OTP request and OTP verify.
- 2c L-1/N-10: `users.otp_code` stores HMAC-SHA256 (`users/otp.py`); migration `users/0008_otp_code_hashed` widens the column to 64, reverse clears pending codes first; `pg_dump` taken.
- 2d N-13: a forged webhook stores only `{redacted, sha256}`, no audit row, a log line; webhook endpoint throttled per IP (`THROTTLE_WEBHOOK_RATE`, default 600/min); bodies over 64 KB are refused.

## OWASP Top 10:2025 hardening (2026-10-13): plan approved by the owner
Three read-only audits (A01..A10) found no SQL injection, XSS sink, unsafe deserialization, open redirect, SSRF or card-data storage. The gaps and the six batches are in the approved plan; status per item is kept in `.ai/SECURITY_OWASP.md` when the last batch is done.
- Batch 1 (done, no migration): A05-1 search word cap + EXISTS (no join per word); A06-1/A06-2 SMS budgets (account-keyed throttles on the logged-in verification endpoints, IP budget and daily per-number budget on the login code request); A06-3 pending-booking cap rechecked under a lock on the guest row; A05-2/A05-3 unknown webhook provider is a 404 and caller-chosen values are escaped in log lines; A10-8 non-object webhook JSON is a 400 and Django `SuspiciousOperation`/`BadRequest` map to 400.
- Owner decision 2026-10-13 (batch 2, A04-1): the `payment_method_token` field stays, the client will supply the real provider token soon. Until then the backend only refuses values that look like a card number (13-19 digits or Luhn-valid); the exact token format check is added when the provider token is known. Rest of batch 2 waits for the owner's explicit go.
- Batch 4 (access control details, done except A01-2): favorites accept and list only published hotels (A01-1); the public hotel page no longer returns `owner`, `approved_by`, `approved_at`, `rejection_reason` and the public availability no longer returns the partner's internal day `notes`, and it is bounded to 366 days from the start (A01-3/A01-4); review and payment create use `bookings.fields.OwnBookingField`, so a foreign booking id and a missing one get the same answer (A01-5); the permission matrix test has no catch-all for `/admin-panel/` any more, a new route family must be classified (A01-6). Open: `booked_rooms`/`remaining_rooms` stay public because the availability calendar and "only N left" use them (owner decision if occupancy should be hidden); A01-2 (refunds and no-show approval for super-admin only) waits for the owner's confirmation of Q2.
- Batch 5 (configuration and supply chain, done except the items below): `DEBUG=True` with a public domain in `ALLOWED_HOSTS` and a non-PostgreSQL `DB_ENGINE` with DEBUG off refuse to start (A02-1/2); JSON-only renderer outside DEBUG (A02-3); `RequestBodyLimitMiddleware` answers 413 for a JSON body over 1 MB or an upload over 12 MB from Content-Length (A02-4); `X-XSS-Protection: 0` (A02-7); env lists stripped (A02-8); `CONN_HEALTH_CHECKS`, dead DB-health and RATELIMIT settings removed (A02-10); Redis socket timeouts 2 s (A10-6, partly); `.env.example` ships `DEBUG=False` (A02-1/A07-5); `requirements.txt` (runtime, Pillow pinned, unused `django-ratelimit`, `cryptography`, `django-debug-toolbar` removed) and `requirements-dev.txt` (A03-2/3/4); `scripts/checkpoint_checks/` (A03-7); `.github/workflows/ci.yml` and `.github/dependabot.yml` (A03-1/A08-1); `deploy/nginx.conf.example` with the real CSP header (A02-5/A05-6).
- Batch 5 not done (reasons): hash-locked requirements (needs pip-tools in CI), celery 5.5/redis upgrade (would downgrade the installed kombu; needs a worker test run), `TICKBRON_TESTING` env var instead of `'pytest' in sys.modules` (the dev-only pytest packages are no longer installed in production, which removes the risk), Redis `IGNORE_EXCEPTIONS` (would make login lockout fail open), Swagger/ReDoc pinning (docs are staff-only outside DEBUG; low), Vite production build without `unsafe-eval`/`unsafe-inline` and the `<meta>` CSP (needs a browser check of the built app under the strict header from `deploy/nginx.conf.example`), photo re-encoding and storage quota (A08-5), key separation with `salted_hmac` (A04-3), webhook endpoint super-admin only/redaction (A04-2, with batch 2/3).

## OWASP batch 2 (2026-10-14): money paths and exceptional conditions. Owner approved ("2-paketni boshla")
No migration. Owner decision on A04-1: the `payment_method_token` field stays; only card-number-like values are refused until the real provider token format is known.
- A10-2/A06-5: a validly signed paid/failed message that cannot be applied (no matching transaction yet, amount mismatch) raises `WebhookNotApplicableError`: the event is stored `failed` with an audit entry, the endpoint answers 409 and the provider's retry is processed again. Informational events (created, pending, ping) are still acknowledged.
- A10-3: `Booking.process_expired_bookings` skips a booking with a `processing` payment updated within 30 minutes (`PAYMENT_IN_PROGRESS_GRACE`); older ones expire. A payment captured for a booking that cannot be confirmed gets a `needs_manual` refund (`flag_unconfirmable_payment`, idempotent key `unconfirmable:<payment>`, error code `BOOKING_NOT_CONFIRMABLE`) that shows in the staff needs-attention list.
- A10-1: `send_refund` turns any unexpected provider error into `failed` (`REFUND_ERROR`); `retry_refund` also accepts a refund pending for over an hour (`PENDING_TOO_LONG`, now in `payments/refunds.py`).
- A10-7: in payment create only the provider call is guarded; an unexpected error marks the transaction `failed` (`PROVIDER_ERROR`) and answers 502 instead of leaving it pending with a 500.
- A10-5: the booking and payment status history writes run in a savepoint and failures are logged with a traceback.
- A04-1: card-number-like values (13-19 digits, spaces/hyphens ignored, or a Luhn-valid run inside) are refused in `payment_method_token`.
- A06-4: a confirmed booking cannot be cancelled online from check-in day on (400). The 50 % refund by rate plan (client decision Q1) is not built yet.
- A10-9: `DatabaseError` is no longer turned into a 400 in booking create, booking cancel, OTP request and OTP verify.
- A10-10: a swallowed booking payment-status error in refunds is logged.
- Not in this batch: reconciliation of `processing` transactions with the provider (A10-4, own plan after the real adapters exist); a provider success for a transaction we already marked `failed` is still ignored (reconciliation covers it).

## OWASP batch 3 (2026-10-14): logging and alerting (A09). Owner approved ("3-paketni boshla")
Migration `admin_panel/0011_audit_ip_and_payment_reads` (new, reversible: adds `ip_address`, widens the action choices); `pg_dump` of the dev database taken first, forward/back/forward run on a scratch database.
- A09-1: `common/security_log.log_security_event` writes `event=<name> user=<id|none> ip=<addr> method path ...` to the `tickbron.security` logger. Events: `login_success`, `login_failed` (reason `unknown_account`, `locked`, `bad_credentials`), `lockout` (scope `ip` or `account`, logged once when the lock starts), `logout`, `account_created`, `otp_login_failed`, `webhook_rejected`, `webhook_not_applied`. Login, logout and sign-up also write the user-visible `AccountHistory` rows (`accounts/history.py`). Only ids, addresses and fixed reason codes are logged: no e-mail, phone, password, code or token.
- A09-2/A09-9: refused requests are events too: `permission_denied`, `csrf_failed`, `unauthenticated`, `throttled`, each with user, address, method, path and the view name.
- A09-3: `tickbron.security` is always INFO, in `logs/security.log` (10 MB x 10) and on stdout; the root logger now also writes to the file, so module loggers (payments, bookings, users, currency) are no longer stdout-only.
- A09-7: `AdminAccessLog.ip_address` (taken from the request through a context variable set by `RequestLoggingMiddleware`, so the existing 30+ `record()` calls needed no change).
- A09-8: a staff member listing or opening webhook events or payment audit entries writes `webhook_list|view` and `payment_audit_list|view` rows (`StaffReadAuditMixin`). A guest reading their own rows writes nothing. Staff listing `/payments/transactions/` sees only their own payments, so no row is needed there.
- A09-5: `/healthz/` (process) and `/readyz/` (database + cache; 503 without details).
- Not done, needs the owner: A09-4 the alert channel (Sentry, Telegram or e-mail on `tickbron.security` events such as `lockout`, `webhook_rejected`, `webhook_not_applied` and 5xx spikes) and the Celery beat heartbeat; A09-6 DB-level append-only for the audit tables (REVOKE or trigger, needs database privileges); A09-13 forged-webhook rows (store the address, prune after 30 days); A09-10/A09-11 audit rows for partner writes and phone changes; retention of the DB audit tables and log shipping.

## OWASP batch 6, part 1 (2026-10-14): password reset and change (A07-1), Telegram alerts (A09-4). Owner: "sen tavsiya qilgan ishlarni qil"
No migration. Plan and design: the approved plan of this step (signed single-use token from Django's `PasswordResetTokenGenerator`, 1 hour; mail by a Celery task; one answer for every address; sessions of the account end on reset and change).
- Done: the three endpoints and `users/password_reset.py`, `users/tasks.py`; settings `EMAIL_*`, `FRONTEND_URL`, `PASSWORD_RESET_TIMEOUT`, `CELERY_TASK_ALWAYS_EAGER`; production refuses to start without an https `FRONTEND_URL` and an `EMAIL_HOST`; frontend pages `ForgotPasswordPage`, `ResetPasswordPage`, `ChangePasswordForm` (profile), link on the login page, i18n uz/ru/en; Telegram alerts (`common/alerts.py`, `common/tasks.py`) for `lockout`, `webhook_rejected`, `webhook_not_applied` and any ERROR, once per 10 minutes per message, off until `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALERT_CHAT_ID` are set.
- Not done: e-mail verification at registration (the other half of A07-1), staff 2FA, forcing hotel owners to change the admin-set password at first login (the change endpoint exists for it), SMS-based reset.
