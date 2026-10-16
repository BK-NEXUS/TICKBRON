# Plan: remove phone / SMS login from the backend

Status: PROPOSED, waiting for the owner's explicit approval (security + database migration gate in `.ai/README.md`). No code is changed by this file.

## Why
The owner wants sign-in and sign-up by e-mail only and no phone number typed anywhere (frontend done, commit `0aadb32`). The backend still exposes SMS login and phone verification that nothing calls. Unused auth endpoints are attack surface: SMS cost abuse, number enumeration timing, a second login path to defend. They also never worked in production: `OTPService.send_otp` (`users/services.py:60`) raises 503 "SMS provider is not configured" unless `SMS_TEST_MODE` is on, and production refuses to start with it on (`config/settings.py:481`).

## What exists (evidence)
- Endpoints: `POST /auth/otp/request/`, `POST /auth/otp/verify/`, `POST /auth/phone/verify/request/`, `POST /auth/phone/verify/confirm/` (`users/urls.py`, `users/views/otp.py`).
- Logic: `users/services.py` (`OTPService`, 173 lines), `users/otp.py` (`hash_otp`), `User.generate_otp` / `User.verify_otp` (`users/models.py:199-245`), 8 SMS throttle classes (`users/throttles.py`), `lockout` docs mention OTP.
- Data: `users.User` columns `phone_number`, `phone_verified`, `otp_code`, `otp_expires_at`, `otp_attempts`; DB constraint `users_phone_unique_when_verified` (migration `0007`); `otp_code` hashed (migration `0008`).
- Settings: `SMS_TEST_MODE` and its production guard.
- Tests: about 1100 lines in 9 files (`test_otp*.py`, `test_n1_phone_*.py`, `test_sms_abuse_throttles.py`, `test_phone_unique.py`, `test_phone_validation.py` partly), plus references in `core/tests/test_r4_permission_matrix.py`, `test_settings_defaults.py`, `test_r4_production_config.py`, `conftest.py`.
- Other places that take a phone: `PATCH /auth/me/update/` (`UserUpdateSerializer.phone_number`), `POST /admin-panel/users/create-hotel-owner/` (optional `phone_number`), `POST /bookings/` (optional `guest_phone`, falls back to the account number).

## Stage 1: no migration (recommended first)
1. Tests first: the permission matrix and route tests expect the four endpoints to answer 404; profile update and create-hotel-owner ignore `phone_number`.
2. Remove the four routes, `users/views/otp.py`, `OTPService`, `users/otp.py`, `User.generate_otp` / `verify_otp`, the SMS throttles, `RequestOTPSerializer`, `VerifyOTPSerializer`, `ConfirmPhoneSerializer`.
3. `UserUpdateSerializer` and create-hotel-owner stop accepting `phone_number`. `UserSerializer` keeps `phone_number` and `phone_verified` read-only (old data stays visible to admins, nothing breaks for the frontend types).
4. Remove `SMS_TEST_MODE` (settings, `.env.example`, `conftest.py`, production guard) and update `.ai/contracts/auth.md`, `API_CONTRACT.md`, `RELEASE_CHECKLIST.md`.
5. Delete the tests of the removed behaviour (listed above); every other test stays unchanged. Full suite on PostgreSQL before the push.
Result: the columns stay, so existing accounts and old bookings lose nothing and the change is fully reversible with `git revert`.

## Stage 2: migration (separate approval, after stage 1 is live)
New reversible migration: drop `otp_code`, `otp_expires_at`, `otp_attempts`, `phone_verified` and the constraint `users_phone_unique_when_verified`. `phone_number` stays as an optional, read-only legacy field (old bookings and admin screens use it). `pg_dump` before running it; the reverse migration re-adds the columns empty.

## Open questions for the owner
1. Booking: keep the optional `guest_phone` API field (old clients) or stop accepting it too? Without it hotels see no phone at all; arrivals list shows only the last 4 digits today.
2. Stage 2: drop the OTP columns now, or keep them for a while?
3. Should `phone_number` be removed completely later (also from admin screens and CSV exports) or stay as old read-only data?

## Risks
- A user who has only ever logged in by SMS (no password) cannot log in after this. Seed/demo users all have passwords; they can use "Forgot password" by e-mail. Check on the live database: `SELECT count(*) FROM users WHERE password = '' OR password LIKE '!%';` before stage 1 goes live.
- Third-party clients of the removed endpoints: none known (only this frontend).
