# Plan: two-step sign-in (2FA) for administrators

Status: PLAN ONLY, nothing built. Needs the owner's answers to the questions at the end (security work: plan first, then approval).

## What it is, in one paragraph
After the correct e-mail and password, the administrator must also type a 6 digit code from an authenticator app on their phone (Google Authenticator, Microsoft Authenticator, Authy, 2FAS). The code changes every 30 seconds and is made from a secret that only the phone and the server know (standard TOTP, RFC 6238). A stolen or guessed password alone is then not enough to enter the admin panel. If the phone is lost, the person uses one of 10 printed backup codes.

## Who needs it
- **Super admin** (`is_superuser`): must. It controls money, hotels, ads and every account.
- **Staff** (`is_staff`, not super admin: moderators and support): must too. They can read personal data and decide reviews and hotel approvals.
- **Hotel owners**: not required (they log in with a password like guests). Offered later as a choice in their profile, the same code path. Not in this plan's first version.
- **Guests**: no.

## Today (verified in the code)
- The user already has the unused fields `two_factor_enabled`, `two_factor_secret`, `two_factor_backup_codes` (`users/models.py`) and `UserSerializer` returns `two_factor_enabled`. No code uses them.
- Sign-in is one function: `users/views/auth.py::login_view` -> `users/sessions.py::start_session` (`login()` is called only there, plus once in `register`, which makes a guest). So there is one place to put the second step.
- Password reset (`/auth/password-reset/...`) changes the password only; it does not sign anybody in, so it needs no second step, but it must not switch 2FA off.
- Lockout and per-IP limits exist (`users/lockout.py`), the audit log `AdminAccessLog` exists, `log_security_event` exists.

## How sign-in works with 2FA (backend)
1. `POST /auth/login/` with e-mail and password, as now. If the account **needs 2FA and has it set up**: no session is created. The answer is `200 {"two_factor_required": true}` and the server remembers "password OK for user X" in the session store for **5 minutes** (not a login; the user stays anonymous for every other endpoint).
2. `POST /auth/login/2fa/` with `{code}` (6 digits) or `{backup_code}`. Correct: the session is started (`start_session`, method `password+totp`). Wrong: 401 with the same text for every wrong case.
3. Wrong codes count like wrong passwords: 5 wrong codes lock that step for 30 minutes (reuse `users/lockout.py`), a throttle of 10 per minute per IP block, every failure goes to `log_security_event`.
4. A code can be used once (the last accepted time step is stored); a code from the previous or next 30 second step is accepted (phone clock drift).
5. If the account **needs 2FA but has not set it up yet**: the password login starts a session limited to one thing, the setup screen (every other admin endpoint answers 403 "Set up two-step sign-in first"). So the first administrator is never locked out of an empty system, and nobody keeps an unprotected admin session.

## Setting it up (backend)
- `POST /auth/2fa/setup/` (logged in): makes a new secret, returns the `otpauth://` link and the same text secret (for typing). Nothing is switched on yet.
- `POST /auth/2fa/confirm/` `{code}`: the first correct code switches `two_factor_enabled` on and returns the **10 backup codes once** (stored only as hashes, each usable once).
- `POST /auth/2fa/disable/`: refused for staff and super admins (it is required for them). Allowed for other accounts later, with password + code.
- A super admin can **reset another administrator's 2FA** (lost phone and lost backup codes): `POST /admin-panel/users/<id>/2fa-reset/`; it needs the super admin's own current code, logs `AdminAccessLog` (`two_factor_reset`), ends that user's sessions and sends them a notice. Nobody can reset a super admin's 2FA except by a server command (`manage.py reset_2fa <email>`), because the only one who could is that person.
- Changing the password asks for the old password as today; it does not change 2FA.

## Frontend
- Login page: after the password, if the answer says `two_factor_required`, the same card shows a 6 digit field (numeric keyboard, `autocomplete="one-time-code"`), a "Use a backup code" link and a back link. Errors, loading state, mobile 390 px, keyboard use and the three languages (en, uz, ru) as everywhere.
- Setup screen: a QR code (drawn in the browser from the `otpauth://` link, no picture goes to another site), the text secret, a code field, then the 10 backup codes with "Copy" and "Download" and a tick "I saved them" before it lets go.
- Admin panel: a small "Two-step sign-in" status in the account/profile menu, and for the super admin a "Reset" button next to every administrator and staff user.

## Security decisions (my defaults)
- Library: **`pyotp`** (small, widely used) instead of writing the code check by hand; tested against the RFC 6238 vectors. One new dependency in `requirements.txt` (checked by the CI advisory step).
- Secret at rest: encrypted with a key from a new setting `TWO_FACTOR_KEY` (Fernet from the `cryptography` package; a second dependency). If the database leaks without the `.env` file, the secrets are useless. The key is required in production (the settings check refuses to start without it), same style as the other required settings.
- Backup codes: 10 random codes of 10 characters, stored as password hashes (like passwords), shown once.
- The "password OK, waiting for code" state lives in the server session and expires in 5 minutes; it carries no permission.
- Existing sessions of an administrator are ended when 2FA is switched on or reset.
- Never logged: codes, secrets, backup codes.
- Migration: one new field `two_factor_last_step` (integer, null) and a rename-free reuse of the three existing fields; additive and reversible. `pg_dump` before touching a dev database.
- Rollout: switched on by a setting `TWO_FACTOR_REQUIRED_FOR_ADMINS` (default True in production). Existing administrators get the setup screen at their next login (point 5 above), so nobody is locked out.

## Tests first (examples)
- Password right, 2FA on: no session, `two_factor_required`; every admin endpoint 401/403 until the code is given.
- Right code: session starts; wrong, expired (over 5 minutes), reused and old-step codes are refused; 5 wrong codes lock; backup code works once only.
- Admin without 2FA set up: only the setup endpoints work; after confirm, the panel works.
- Guest and hotel owner: login unchanged (no extra step).
- Disable refused for admins; reset by a super admin needs their code, ends sessions, writes the audit row, notifies; staff cannot reset anybody; nobody resets a super admin through the API.
- RFC 6238 test vectors for the code check; the secret is not readable in the database as plain text; the codes and secrets never appear in logs.
- Frontend: the two-step login card, backup code switch, setup screen with the saved-codes tick, errors, three languages (key parity test).
- `UserSerializer` still returns `two_factor_enabled`; the three old field tests keep passing.

## Delivery in three pull requests
1. Backend: model change, `pyotp` check, login second step, setup/confirm, lockout and throttles, audit, settings check, tests, contract and handoff notes.
2. Frontend: login second step, setup screen with QR (a small library for drawing the QR in the browser, checked for size and advisories), status in the profile menu, tests, browser check at 390 and 1440 px.
3. Super admin reset and the `reset_2fa` command; optional 2FA for hotel owners only if the owner asks.

## Not in this plan
- SMS codes (cost, SIM-swap risk), e-mail codes (SMTP is not set up and an e-mail account is a weaker second step), hardware keys / passkeys (a good later step), "remember this device for 30 days" (adds risk; can be added if the daily typing annoys the staff), 2FA for guests.

## Questions for the owner (my default in brackets)
1. 2FA **required** for super admin and staff, and off for owners and guests? (yes)
2. Is a phone with an authenticator app available to every administrator and staff member? (they install a free app; I write the steps in the guide)
3. "Remember this device" for 30 days to type the code less often? (no, add later if wanted)
4. Is it fine to add two libraries, `pyotp` and `cryptography`? (yes)
5. Who resets a super admin who lost the phone and the codes? (the server owner, with the `reset_2fa` command)
