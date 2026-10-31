# Plan: six-digit codes mailed to the address

Status: approved by the owner in chat (2026-10-31): a code at sign-up and a code at every sign-in; the confirm-password field stays. Built in `email-codes-1`.

## What it is
- **Sign-up**: the form is checked as before, but no account is made. A six-digit code goes to the address; the account is made when the code is typed, with the address marked confirmed (`email_verified`), and the new user is signed in.
- **Sign-in** of a **guest or hotel owner**: after the right password a code is mailed; the session starts only when the code is typed. The address is also marked confirmed (an account made before this change gets confirmed this way).
- **Staff and super admins** are not asked for a mailed code: they have the authenticator app (`users/two_factor.py`, required in production), which is stronger. (My decision; say if staff should have both.)

## Rules (`users/email_codes.py`)
- 6 digits from `secrets`, valid 10 minutes, works once, kept only as a keyed hash (HMAC with the secret key, bound to purpose and address) in the cache.
- 5 wrong tries burn the code (atomic counter). At sign-in wrong codes also count towards the same account lock as wrong passwords.
- A new code after 60 seconds, at most 5 mails an hour to one address, plus per-network limits on the endpoints.
- A waiting sign-up keeps the typed data in the cache for 10 minutes; the password is hashed before it is stored, the code never is.
- The mail is sent inside the request (not through the task queue) so the code never passes through queue logs. A mail server that fails gives a 503 and leaves nothing waiting.
- Mail only after the right password at sign-in, so nobody can make the site mail codes to an address by guessing.
- No migration: the cache holds the waiting data (Redis in production; a restart only means "ask for a new code").

## Switches (default on)
`EMAIL_VERIFICATION_REQUIRED`, `EMAIL_LOGIN_CODE_REQUIRED`. They need working mail (`EMAIL_HOST`, the production settings check already insists). If the mail server is down nobody can sign up or sign in as a guest or owner (password reset has the same dependency), so use a reliable mail service; a personal Gmail account sends about 500 mails a day.

## Decisions to confirm
- Staff are not asked for the mailed code (authenticator instead).
- A guest who signs in on a new phone every day gets a mail every time (no "remember this device"); add it if the daily typing annoys.
