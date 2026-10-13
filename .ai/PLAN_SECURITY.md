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
