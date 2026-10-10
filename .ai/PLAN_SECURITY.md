# PLAN SECURITY: batch 2 item N-1 (phone pre-hijacking)

Status: approved by the owner on 2026-10-10 ("N-1 ishlashni boshla"); stage 1 implemented, stage 2 (migration) follows.

## Problem
Registration and profile update accept any unclaimed phone number with no proof of ownership. SMS login never checked `phone_verified`, so an attacker could register with a victim's number; when the victim later signed in by SMS, the code logged them into the attacker's account. The global unique constraint also let an attacker squat a number so its real owner could not register.

## Stage 1 (done): close the takeover, no schema change
- SMS login (`otp/request`, `otp/verify`) acts only on accounts whose phone is verified; unverified numbers get the same generic answer and no code.
- New authenticated endpoints `POST /auth/phone/verify/request/` and `/confirm/` prove the account's own number (number taken from the account, same throttle/lockout/code storage as OTP).
- `phone_verified` is returned on the user object; profile shows the state with a verify dialog; login page explains the rule.

## Stage 2 (next): stop number squatting, one migration
- Replace the global unique on `User.phone_number` with a partial unique constraint (`phone_verified = true`). Unverified claims no longer block the real owner.
- Verifying a number clears the same number from other users' unverified claims (one transaction).
- Uniqueness validation and phone lookups consider verified holders only.
- Migration is new and reversible; `pg_dump` first.

## Out of scope
Card data: nothing here touches cards; payment tokens come from the provider and no PAN/CVV is stored.
