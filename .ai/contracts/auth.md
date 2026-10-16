# AUTH CONTRACT

Browser auth is session-based with secure HttpOnly/Secure/SameSite cookies. State-changing requests require CSRF protection. JWT must not be stored in localStorage. Session rotation, verification, rate limiting and RBAC are mandatory.

## Authentication Methods

### Password-Based Authentication
- POST `/api/v1/auth/register/` - User registration
  - Required fields: `email`, `full_name`, `password`, `password_confirm`. E-mail only (2026-10-14): there is no phone field; a `phone_number` in the body is ignored and the account starts with `phone_number: null`. A number is added later with `PATCH /auth/me/update/` and proven with `/auth/phone/verify/`
  - Optional fields: `first_name`, `last_name` (nullable), `whatsapp`, `telegram`, `preferred_contact_method`
  - Auto-logs in user after successful registration
  - Rate limited: 5 requests/minute per IP

- POST `/api/v1/auth/login/` - Password login
  - Required fields: `email`, `password`
  - Rate limited: 10 requests/minute per IP
  - Client IP for rate limits and audit fields is `REMOTE_ADDR`; `X-Forwarded-For` is trusted only for `NUM_PROXIES` reverse proxies (default 0 = ignored). Rate-limit counters are shared through Redis when `USE_REDIS_CACHE` is on (default when `DEBUG=False`)
  - Lockout: 5 failures from one client IP lock that IP out of the account for 30 min; 20 failures across all IPs within 30 min lock the account for 15 min (`users/lockout.py`)
  - Every failure (unknown email, wrong password, inactive or locked account) returns the same 401 `{"detail": "Invalid credentials. If you have made several failed attempts, please try again later."}`

### Removed: SMS login and phone verification (2026-10-16)
`POST /auth/otp/request/`, `POST /auth/otp/verify/`, `POST /auth/phone/verify/request/` and `POST /auth/phone/verify/confirm/` no longer exist (404). Accounts are e-mail only. No endpoint takes a phone number for an account: register, `PATCH /auth/me/update/` and `POST /admin-panel/users/create-hotel-owner/` ignore a `phone_number` in the body. An old number stays on the account as read-only data (`phone_number`, `phone_verified` in the user object; the DB columns and the constraint `users_phone_unique_when_verified` are dropped in a later, separately approved migration).

### Password reset and change (OWASP A07-1, 2026-10-14)
- POST /api/v1/auth/password-reset/request/ - body `{email}`. Anonymous, CSRF token required, 5/hour per IP and 5 mails/day per address.
  - Always 200 `{"detail": "If this address is registered, we have sent a link to reset the password."}` (registered or not, active or not); the mail is sent by a Celery task. Invalid address format: 400.
  - The mail holds `FRONTEND_URL/reset-password?uid=<id>&token=<token>` (text in uz, ru and en). The token is single use and valid for `PASSWORD_RESET_TIMEOUT` (1 hour); it stops working after the password changes or the user signs in.
- POST /api/v1/auth/password-reset/confirm/ - body `{uid, token, password, password_confirm}`. Anonymous, CSRF token required, 10/hour per IP.
  - 200 `{"detail": "Your password was changed."}`; the user is NOT signed in, every session of the account ends, lockout counters are cleared.
  - 400 `{"error": "...", "code": "invalid_reset_link"}` for a broken, expired or used link (one answer for all cases); 400 `{"password": [...]}` when a password rule is broken (same rules as registration), the link then stays valid.
- POST /api/v1/auth/password/change/ - body `{current_password, password, password_confirm}`. Signed-in users only, 5/min per account.
  - 200 `{"detail": "Your password was changed."}`; this session stays signed in, the other sessions end.
  - 400 `{"current_password": [...]}` for a wrong current password (it counts as a failed login attempt), 400 `{"password": [...]}` for a weak password or one equal to the current one.
- Events (`tickbron.security`): `password_reset_requested` (`outcome=sent|ignored`), `password_reset_completed`, `password_reset_failed`, `password_changed`, `password_change_failed`. History row `password_change`. No address, password or token is logged.

## CSRF
- GET `/api/v1/auth/csrf/` - Get a CSRF token (public, no auth)
  - Response 200 `{"csrf_token": "<token>", "authenticated": <bool>}`; also sets the `csrftoken` cookie if missing
  - `authenticated` (added 2026-09-28): whether this session is logged in. The SPA asks it on page load and only calls `/auth/me/` when it is true, so anonymous visits make no 401 request (browser console error)
  - The `csrftoken` cookie is HttpOnly, so the SPA cannot read it; it takes the token from this endpoint instead
  - Every POST/PUT/PATCH/DELETE from a logged-in session must send it as the `X-CSRFToken` header, otherwise 403 `{"error": {"code": "error", "message": "CSRF Failed: CSRF token missing.", ...}}`
  - Django rotates the token on login (password login, register auto-login); fetch a new one after any login. Logout ends the session, so fetch again before the next login-protected write

## Session Management
- POST `/api/v1/auth/logout/` - Destroy session
- GET `/api/v1/auth/me/` - Get current user info
  - Includes read-only `is_staff` and `is_superuser` (bool). Staff can use the `/admin-panel/` and support lookup endpoints; only super-admins can use `POST /admin-panel/users/create-hotel-owner/`. The flags only drive the UI: the backend still checks permissions on every request, and `PATCH /auth/me/update/` cannot change them
  - Includes read-only `phone_verified` (bool, legacy, read-only): true for numbers proven before SMS verification was removed. Only then can the number be used for SMS login
  - Includes read-only `role` (string or null, added 2026-09-26): `"hotel-owner"` for owner accounts, null for regular users. Only a super-admin assigns it (`POST /admin-panel/users/create-hotel-owner/`); register, OTP and `PATCH /auth/me/update/` ignore any `role` in the body. The UI shows partner entry points only for `role == "hotel-owner"` or staff
  - The same user object (with both flags and `role`) is returned by register, login, refresh and `PATCH /auth/me/update/`
- POST `/api/v1/auth/refresh/` - Refresh session
- PATCH `/api/v1/auth/me/update/` - Update user profile
  - Required authentication
  - Optional fields: `full_name`, `first_name`, `last_name`, `whatsapp`, `telegram`, `preferred_contact_method` (a `phone_number` is ignored)
  - `guest_phone` on `POST /bookings/` is still an optional, validated international number (stored as E.164); it is the only place an API takes a phone number
  - Partial updates supported

## Configuration
- Password reset needs `FRONTEND_URL`, `EMAIL_*`, `DEFAULT_FROM_EMAIL` and a running Celery worker (or `CELERY_TASK_ALWAYS_EAGER=True` in local development). Production refuses to start without an https `FRONTEND_URL` and an `EMAIL_HOST`.
