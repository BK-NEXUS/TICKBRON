# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository context

TICKBRON is a hotel/property booking platform. The git root (`TICKBRON/`) holds `backend/` (this Django project), `frontend/`, and `.ai/`, the coordination layer shared by the AI agents working on the project. Backend owner: Kolya. Frontend owner: Baxram. GitHub (`BK-NEXUS/TICKBRON`, branch `master`) is where the two sync. Since 2026-09-25, Kolya's agent may work on both `backend/` and `frontend/` without asking first; commit naming is in `.ai/README.md`.

### `.ai/` workflow (read before changing code)
- Git history plus `.ai/` is the persistent memory. Chat history is not assumed. Start with `.ai/README.md`, `.ai/BACKEND_STATE.md`, `.ai/HANDOFF.md`, and `.ai/API_CONTRACT.md` (plus `.ai/contracts/{auth,booking,payments}.md`).
- Each task is one checkpoint: READ → SYNC (`git pull`) → AUDIT → SCOPE LOCK → IMPLEMENT → TEST → SECURITY CHECK → CONTRACT CHECK → update `.ai` checkpoint/state/handoff → COMMIT → PUSH → next item.
- Next item rule (2026-10-03, approved by Kolya): After an item is merged and pushed, continue with the next BACKEND item in `.ai/ROADMAP.md` automatically. Approval gate: an item that touches money (prices, currencies, payments, refunds), security or database migrations starts with a plan in `.ai/PLAN_<item>.md` (e.g. `PLAN_R6.md`); push it, show the owner a short summary, and WAIT for the owner's explicit approval before changing code. Everything else continues without waiting.
- Hard stops (report BLOCKED rather than guessing): merge/rebase conflicts, a missing contract or dependency, an unexplained regression, a high/critical security issue, an unsafe migration, or any change that would overwrite the other owner's work.
- Backend checkpoint commits are named `kolya NN project`, optionally followed by ` - <summary>` (e.g. `kolya 23 project - Booking reference code + support lookup API`). Commits outside a checkpoint have used `kolya - <summary>`. From 2026-09-25, use `kolya - backend: <short description>` (frontend: `kolya - frontend: …`, docs only: `kolya - docs: …`).
- Changes to the protected coordination files (`.ai/API_CONTRACT.md`, `HANDOFF.md`, `PROJECT_STATE.md`, `BACKEND_STATE.md`, `FRONTEND_STATE.md`) must be intentional and documented. Do not invent API contracts; the frontend depends on them.
- Checkpoint notes go in `.ai/checkpoints/backend_NN.md` (template: `CHECKPOINT_TEMPLATE.md`).

## Commands

Run these from `backend/`. The virtualenv is `venv/` (Windows: `venv\Scripts\python.exe`). Copy `.env.example` to `.env` for local config and set `DEBUG=True` there (the example ships `DEBUG=False`, so a copied file never runs a server in debug by accident). Install `requirements-dev.txt` for development.

```bash
python manage.py runserver
python manage.py migrate
python manage.py process_expired_bookings [--dry-run]   # expire stale pending bookings, restore inventory
python manage.py complete_finished_stays        # mark confirmed stays whose check-out has passed as completed
python manage.py fetch_exchange_rates           # CBU rates (dollar, tenge, rouble) for the staff to accept
python manage.py reset_2fa <email>              # clear an administrator's two-step sign-in (lost phone)
python manage.py db_health | init_db | load_geography | map_property_geography | seed_property_types | shrink_photos
python manage.py seed_demo                 # demo admin/owner/guest + 3 hotels (DEBUG only)
python manage.py seed_demo_stats           # DEMO data for the Status sections: 12 hotels, 60 guests, 250 past bookings (DEBUG only)

pytest                                   # full suite (uses --reuse-db; add --create-db after model changes)
pytest bookings/tests/test_views.py      # single file
pytest bookings/tests/test_views.py::TestClass::test_name
pytest -m "not slow"                     # markers: slow, integration, unit (--strict-markers is on)
pytest --cov=. --cov-report=html

black . && isort . && flake8

celery -A config worker -l info
celery -A config beat -l info

python scripts/smoke_test.py             # register→login→book→favorites chain against a local DB
```

- The project runs on PostgreSQL only (the `DB_*` settings in `backend/.env`); SQLite is not supported because it ignores varchar lengths and has no row locks. pytest-django creates a separate `test_<DB_NAME>` database.
- API docs: `/api/docs/` (Swagger), `/api/redoc/`, `/api/schema/`: open with `DEBUG=True`, staff only in production. Health: `/healthz/`, `/readyz/`.
- `scripts/checkpoint_checks/*.py` are standalone per-checkpoint verification scripts (run from `backend/`: `python scripts/checkpoint_checks/<name>.py`). They are not pytest tests.

## Architecture

- **Settings** (`config/settings.py`) are one env-driven module with no split settings files. The database engine is fixed to PostgreSQL. Without `DEBUG=true`, `SECRET_KEY` and `ALLOWED_HOSTS` must be set or startup fails. A `TESTING` flag (set when pytest is loaded) turns off DRF throttling, so rate-limit tests have to enable throttling themselves. Limits of the busy public endpoints are settings (`THROTTLE_*_RATE`, see `.env.example`); the cache is Redis in production and local memory in tests.
- **Auth** uses DRF `SessionAuthentication` (session cookies plus CSRF, no tokens). `IsAuthenticated` is the default permission, so public endpoints must opt out explicitly. `users.User` is the custom user model. Accounts are e-mail only: sign-up and login use e-mail and password, and a password reset link is sent by e-mail (there is no SMS login). Roles come from `permissions.Role` / `Permission` / `RolePermission` through the `User.role` FK. Partner and admin endpoints use their own `has_permission` classes in `partner/views.py` and `admin_panel/views.py`.
- **URL layout** (`config/urls.py`), all under `/api/v1/`: `auth/` → users, root → properties and bookings, `geography/`, `me/` → accounts (customer profile, notifications), `partner/` (hotel owner: hotels, rooms, rates, bookings, commission, status), `admin-panel/` (staff: users, customers, moderation, statistics, status, commission, exchange rates, advertising, no-show reports), `promotions/` (public banners), `chat/` (support chat). There is no payments route: guests pay cash at the hotel.
- **Base models**: most models inherit `common.models.BaseModel`, which combines timestamps, soft delete (`is_deleted`, via `soft_delete()`/`restore()`), and an active flag, with `BaseQuerySet` / `SoftDeleteManager`. Expect soft-deleted rows to be filtered out by default.
- **Errors**: raise the `TickBronException` subclasses in `common/exceptions.py`. `common.exception_handlers.custom_exception_handler` turns them into the uniform error envelope the frontend expects. Custom middleware in `common/middleware.py` adds security headers, request logging, and performance timing.
- **Booking domain**: `properties` holds Property, RoomType, RatePlan, and per-date `DateInventory`. `bookings.models` holds Booking and BookingItem. Inventory changes run inside `transaction.atomic()` with `select_for_update()` on inventory rows, so keep that locking whenever you touch reservation, cancellation, or expiry code. Status changes must go through `bookings/state_machine.py` (`BookingStateMachine`, `PaymentStateMachine`, `BookingPaymentStateMachine`): pending→confirmed/cancelled, confirmed→cancelled/completed/no_show, and the rest are terminal. The booking API creates a booking already `confirmed` (cash at the hotel, no payment window). Totals, currency and availability are computed only on the backend (`bookings/pricing.py`, the same function prices the public quote and the booking). Bookings carry a human-readable reference code used for support lookup. Celery beat (`CELERY_BEAT_SCHEDULE` in settings) expires old pending bookings, cancels unarrived ones, completes finished stays, fetches exchange rates and runs the advertising renewals.
- **Payments**: there is no online payment. The code, routes and keys of the old card payment are gone (`core/tests/test_no_online_payments.py` keeps it so). The `payments` app only remains for its tables, among them the booking status history that `Booking` writes; do not drop them without a plan. If card payment returns, start with a plan in `.ai/`.
- **Commission**: `partner/commission.py` computes a hotel owner's commission per month and currency from confirmed and completed bookings at the percent in force that month (`CommissionRate`); staff confirm a month as paid only after it ended (`CommissionPayment`, one per owner and month).
- **Sign-in**: guests and owners confirm sign-up and sign-in with a 6-digit code by e-mail (`users/email_codes.py`: one use, 10 minutes, 5 tries); staff and administrators use an authenticator app (TOTP, `users/two_factor.py`) and cannot open any panel before setting it up.
- **Public cache**: `common/public_cache.py` caches a few public pages for a short time (`PUBLIC_CACHE_SECONDS`); quotes, banners and view counters are never cached.
- **Security expectations** (from `.ai/rules/security.md`): RBAC on every endpoint, CSRF, secure cookies, rate limits (DRF throttles, per visitor address, see `common/throttling.py` and `users/throttles.py`), minimal PII in responses and logs, and least privilege plus audit logging for admin actions.
