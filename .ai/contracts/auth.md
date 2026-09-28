# AUTH CONTRACT

Browser auth is session-based with secure HttpOnly/Secure/SameSite cookies. State-changing requests require CSRF protection. JWT must not be stored in localStorage. Session rotation, verification, rate limiting and RBAC are mandatory.

## Authentication Methods

### Password-Based Authentication
- POST `/api/v1/auth/register/` - User registration
  - Required fields: `email`, `full_name`, `phone_number`, `password`, `password_confirm`
  - Optional fields: `first_name`, `last_name` (nullable), `whatsapp`, `telegram`, `preferred_contact_method`
  - Auto-logs in user after successful registration
  - Rate limited: 5 requests/minute per IP

- POST `/api/v1/auth/login/` - Password login
  - Required fields: `email`, `password`
  - Rate limited: 10 requests/minute per IP
  - Client IP for rate limits and audit fields is `REMOTE_ADDR`; `X-Forwarded-For` is trusted only for `NUM_PROXIES` reverse proxies (default 0 = ignored). Rate-limit counters are shared through Redis when `USE_REDIS_CACHE` is on (default when `DEBUG=False`)
  - Lockout: 5 failures from one client IP lock that IP out of the account for 30 min; 20 failures across all IPs within 30 min lock the account for 15 min (`users/lockout.py`)
  - Every failure (unknown email, wrong password, inactive or locked account) returns the same 401 `{"detail": "Invalid credentials. If you have made several failed attempts, please try again later."}`

### Phone-Based OTP Authentication
- POST `/api/v1/auth/otp/request/` - Request OTP code
  - Required fields: `phone_number`
  - Rate limited: 3 requests/minute per phone number
  - Returns OTP code in response when `SMS_TEST_MODE=True`
  - `SMS_TEST_MODE` defaults to `False`; with it off and no SMS provider configured, returns 503
  - Always 200 `{"success": true, "message": "If this phone number is registered, a verification code has been sent."}` for registered, unknown and locked numbers (no account enumeration); only registered, unlocked numbers get a code. Does not create users

- POST `/api/v1/auth/otp/verify/` - Verify OTP and login
  - Required fields: `phone_number`, `otp_code` (6 digits)
  - Establishes session using same mechanism as password login
  - OTP expires after 5 minutes
  - Maximum 3 verification attempts per OTP
  - Rate limited: 5 requests/minute per phone number (429 when exceeded)
  - Same lockout as password login (per IP and account-wide), counted across all issued codes; while locked the code is not checked
  - Unknown number, wrong/expired code and locked account all return the same 400 `{"success": false, "message": "Invalid or expired OTP code"}`

## CSRF
- GET `/api/v1/auth/csrf/` - Get a CSRF token (public, no auth)
  - Response 200 `{"csrf_token": "<token>", "authenticated": <bool>}`; also sets the `csrftoken` cookie if missing
  - `authenticated` (added 2026-09-28): whether this session is logged in. The SPA asks it on page load and only calls `/auth/me/` when it is true, so anonymous visits make no 401 request (browser console error)
  - The `csrftoken` cookie is HttpOnly, so the SPA cannot read it; it takes the token from this endpoint instead
  - Every POST/PUT/PATCH/DELETE from a logged-in session must send it as the `X-CSRFToken` header, otherwise 403 `{"error": {"code": "error", "message": "CSRF Failed: CSRF token missing.", ...}}`
  - Django rotates the token on login (password, OTP verify, register auto-login); fetch a new one after any login. Logout ends the session, so fetch again before the next login-protected write

## Session Management
- POST `/api/v1/auth/logout/` - Destroy session
- GET `/api/v1/auth/me/` - Get current user info
  - Includes read-only `is_staff` and `is_superuser` (bool). Staff can use the `/admin-panel/` and support lookup endpoints; only super-admins can use `POST /admin-panel/users/create-hotel-owner/`. The flags only drive the UI: the backend still checks permissions on every request, and `PATCH /auth/me/update/` cannot change them
  - Includes read-only `role` (string or null, added 2026-09-26): `"hotel-owner"` for owner accounts, null for regular users. Only a super-admin assigns it (`POST /admin-panel/users/create-hotel-owner/`); register, OTP and `PATCH /auth/me/update/` ignore any `role` in the body. The UI shows partner entry points only for `role == "hotel-owner"` or staff
  - The same user object (with both flags and `role`) is returned by register, login, OTP verify, refresh and `PATCH /auth/me/update/`
- POST `/api/v1/auth/refresh/` - Refresh session
- PATCH `/api/v1/auth/me/update/` - Update user profile
  - Required authentication
  - Optional fields: `full_name`, `first_name`, `last_name`, `phone_number`, `whatsapp`, `telegram`, `preferred_contact_method`
  - `phone_number` (here, on register, OTP request/verify and create-hotel-owner; added 2026-09-26): a valid international number, separators allowed, stored and returned as E.164 (`+998901234567`). Otherwise 400 with `phone_number: ["Enter a valid phone number in international format, e.g. +998 90 123 45 67."]`
  - Partial updates supported

## Configuration
- `SMS_TEST_MODE` (default: False; `backend/.env.example` also sets False) - Controls OTP test mode behavior. Set it to True only for local development
- OTP logs never contain the full phone number; `users/services.py` logs it masked with `common.privacy.mask_phone` (`+998901234567` -> `+998*******67`)
- In test mode, OTP codes returned in API response for testing
- In production, integrate with real SMS provider
