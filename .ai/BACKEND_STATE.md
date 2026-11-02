# BACKEND STATE

Owner: Kolya
Checkpoint sequence: 01 → 20 + CRM addendum 21-26
Current checkpoint: 26
Completed: 26

## Current state (2026-11-02)
- Full suites: backend `pytest --create-db` 4093 passed; frontend `npm test` 2415 passed; `tsc --noEmit`, `npm run lint`, `pip-audit`, `npm audit --omit=dev` and `manage.py check --deploy` (production-like settings) are clean.
- Guests pay cash at the hotel. The online payment code, routes and keys are gone (`core/tests/test_no_online_payments.py`); the `payments` app is kept only for its tables, among them the booking status history.
- Sign-in: e-mail and password. Guests and owners confirm sign-up and sign-in with a 6-digit code by e-mail (`users/email_codes.py`); staff and administrators use an authenticator app and cannot open a panel without it. The phone/SMS OTP of checkpoint 21 below was replaced; there is no SMS.
- Money: prices per currency (UZS, USD, KZT, RUB), rates from the Central Bank of Uzbekistan accepted by staff; a currency without a rate shows a note, not a silent dollar price. Hotel owner commission per month (`partner/commission.py`).
- Limits per visitor address are settings (`THROTTLE_*_RATE` in `backend/.env.example`).
- Open for the owner, not code: company and tax set-up, domain, server (where the data must be kept is a legal question), mail service, `.env`, first super admin, off-server backups, real-server load test and security check (TLS, firewall), lawyer review of the texts. See `.ai/OWNER_GUIDE_LAUNCH.docx` and `.ai/DEPLOY_DOCKER.md`.

Backend owns backend/, backend tests, backend infrastructure where explicitly assigned, and backend API contracts.

Before every checkpoint:
|- git pull
|- inspect recent commits
|- read relevant `.ai` files
|- inspect actual code
|- run relevant tests

Commit format:
`kolya NN project`

## Final Release Status
|- ✅ All 20 main checkpoints completed
|- ✅ CRM addendum checkpoints 21-26 completed
|- ✅ Full test suite at checkpoint 22: 614 tests (the current count is in "Current state" above)
|- ✅ Clean migration history
|- ✅ Comprehensive security measures
|- ✅ Permission boundaries enforced
|- ✅ Rate limiting configured
|- ✅ OpenAPI schema documented
|- ✅ Ready for production deployment

## CRM Addendum Progress
|- Checkpoint 21: Simplified registration + phone/SMS OTP authentication ✅
|- Checkpoint 22: Customer profile extensions + booking auto-fill ✅
|- Checkpoint 23: Booking reference code + support lookup API ✅
|- Checkpoint 24: Admin Customers directory API ✅
|- Checkpoint 25: Admin Customer detail API + internal notes ✅
|- Checkpoint 26: Admin statistics API ✅

## Remaining Work
|- None - all checkpoints completed

## Roadmap items (R-series, see .ai/ROADMAP.md)
|- R1, R2 (G1-G4), R4: done and merged (see ROADMAP).
|- R6 currency: DONE 2026-10-05, checkpoint `.ai/checkpoints/backend_r6.md`. Full suite `pytest --create-db`: 2029 passed, 0 failed, 2 skipped. The Payme/Click items that were open here ended with the removal of online payments.
|- R12 status additions (`.ai/PLAN_R12.md`, approved 2026-10-05, three phases). Phase 1 (business date, auto-completion, Refund model, notification codes) DONE 2026-10-06 on `feat/r12-status`, checkpoint `.ai/checkpoints/backend_r12_phase1.md`. Celery beat + worker + Redis are required (RELEASE_CHECKLIST); the refund items ended with the removal of online payments. Next: phase 2 (statistics), then phase 3 (no-show reports).
|- R12 phase 2 (Status statistics) DONE on `feat/r12-status` 2026-10-06, checkpoint `.ai/checkpoints/backend_r12_phase2.md`; READY FOR FRONTEND: R12a in HANDOFF; master merge pending (owner).
