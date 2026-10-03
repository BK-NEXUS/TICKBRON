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

Run these from `backend/`. The virtualenv is `venv/` (Windows: `venv\Scripts\python.exe`). Copy `.env.example` to `.env` for local config. It keeps `SMS_TEST_MODE` and `PAYMENT_TEST_MODE` off; set them to `True` in your local `.env` to get OTP codes in responses and the mock payment flow.

```bash
python manage.py runserver
python manage.py migrate
python manage.py process_expired_bookings [--dry-run]   # expire stale pending bookings, restore inventory
python manage.py db_health | init_db
python manage.py seed_demo                 # demo admin/owner/guest + 3 hotels (DEBUG only)
python manage.py seed_demo_stats           # DEMO data for the Status sections: 12 hotels, 60 guests, 250 past bookings (DEBUG only)

pytest                                   # full suite (uses --reuse-db; add --create-db after model changes)
pytest bookings/tests/test_views.py      # single file
pytest bookings/tests/test_views.py::TestClass::test_name
pytest -m "not slow"                     # markers: slow, integration, unit (--strict-markers is on)
pytest --cov=. --cov-report=html
ALLOW_SQLITE_TESTS=1 DB_ENGINE=django.db.backends.sqlite3 DB_NAME=:memory: pytest   # opt-in SQLite run

black . && isort . && flake8

celery -A config worker -l info
celery -A config beat -l info

python scripts/smoke_test.py             # register→login→book→favorites chain against a local DB
```

- Tests require PostgreSQL (the `DB_*` settings in `backend/.env`); `conftest.py` stops the run otherwise. pytest-django creates a separate `test_<DB_NAME>` database. SQLite is opt-in only (`ALLOW_SQLITE_TESTS=1`): it ignores varchar lengths and has no row locks, so `bookings/tests/test_concurrency.py` skips there.
- API docs: `/api/docs/` (Swagger), `/api/redoc/`, `/api/schema/`.
- `config/*security_check*.py` and `config/contract_check.py` are standalone per-checkpoint verification scripts (`python config/<name>.py`). They are not pytest tests.

## Architecture

- **Settings** (`config/settings.py`) are one env-driven module with no split settings files. SQLite is the default. PostgreSQL is enabled with `DB_ENGINE=django.db.backends.postgresql`. Without `DEBUG=true`, `SECRET_KEY` and `ALLOWED_HOSTS` must be set or startup fails. A `TESTING` flag (set when pytest is loaded) turns off DRF throttling, so rate-limit tests have to enable throttling themselves. `PAYMENT_TEST_MODE` and `SMS_TEST_MODE` default to `False` (an autouse fixture in `conftest.py` turns both on for tests).
- **Auth** uses DRF `SessionAuthentication` (session cookies plus CSRF, no tokens). `IsAuthenticated` is the default permission, so public endpoints must opt out explicitly. `users.User` is the custom user model. Login is by phone/SMS OTP (checkpoint 21). Roles come from `permissions.Role` / `Permission` / `RolePermission` through the `User.role` FK. Partner and admin endpoints use their own `has_permission` classes in `partner/views.py` and `admin_panel/views.py`.
- **URL layout** (`config/urls.py`), all under `/api/v1/`: `auth/` → users, root → properties and bookings, `payments/`, `me/` → accounts (customer profile), `partner/`, `admin-panel/` (CRM: customers, internal notes, statistics).
- **Base models**: most models inherit `common.models.BaseModel`, which combines timestamps, soft delete (`is_deleted`, via `soft_delete()`/`restore()`), and an active flag, with `BaseQuerySet` / `SoftDeleteManager`. Expect soft-deleted rows to be filtered out by default.
- **Errors**: raise the `TickBronException` subclasses in `common/exceptions.py`. `common.exception_handlers.custom_exception_handler` turns them into the uniform error envelope the frontend expects. Custom middleware in `common/middleware.py` adds security headers, request logging, and performance timing.
- **Booking domain**: `properties` holds Property, RoomType, RatePlan, and per-date `DateInventory`. `bookings.models` holds Booking and BookingItem. Inventory changes run inside `transaction.atomic()` with `select_for_update()` on inventory rows, so keep that locking whenever you touch reservation, cancellation, or expiry code. Status changes must go through `bookings/state_machine.py` (`BookingStateMachine`, `PaymentStateMachine`, `BookingPaymentStateMachine`): pending→confirmed/cancelled, confirmed→cancelled/completed/no_show, and the rest are terminal. Bookings carry a human-readable reference code used for support lookup.
- **Payments**: `payments/adapters.py` has one adapter per provider (Payme, Click, Visa) behind `get_payment_adapter(provider)`, with signature validation and a test mode. `payments/webhooks.py` (`WebhookProcessor`) handles signed, idempotent webhook processing that moves `PaymentTransaction` and Booking state forward. Keep webhooks idempotent and signature-checked.
- **Security expectations** (from `.ai/rules/security.md`): RBAC on every endpoint, CSRF, secure cookies, rate limits (`django-ratelimit` plus DRF throttles), signed and idempotent webhooks, minimal PII in responses and logs, and least privilege plus audit logging for admin actions.
