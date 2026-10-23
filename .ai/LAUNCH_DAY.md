# TICKBRON launch day (updated 2026-10-22 for cash at the hotel)

Guests pay cash at the hotel; the platform moves no money (`PLAN_CASH_ONLY.md`). The list below is only what code cannot do: owner decisions, accounts, servers. Details and exact variable names: `RELEASE_CHECKLIST.md` ("Production settings", "Prices in four currencies").

## 0. Code status
Everything is merged into master (2026-10-22): input rules, phone number, cash bookings, no online payments (#72), owner photos (#64), country/region pictures and the owner account place (#67), the four-currency prices (#61, with #58-#60). Only the Dependabot PRs are open. Run the smoke test below on the deployed build, not on a branch.

## 1. Owner must supply
- Hosting: server, domain, TLS certificate, nginx (`NUM_PROXIES`, `USE_X_FORWARDED_PROTO`), Postgres, Redis, Celery worker AND beat.
- E-mail SMTP (`EMAIL_*`, `FRONTEND_URL`) for password reset. Telegram bot token + chat id for alerts.
- Decisions: how the commission is taken now that guests pay cash at the hotel; logo files.
- Reviews: lawyer on the wording of the arrival rule ("if you do not arrive at that time we wait 2 more hours, then the booking is cancelled") and "Reklama"; a native speaker on all uz/ru texts (cancel dialog, arrival notices, no-show approval, phone hints).
- Two numbers the owner may want to change: the cap of 5 upcoming bookings per guest (`MAX_UPCOMING_BOOKINGS_PER_GUEST`), and whether a hotel should see the full guest phone in the arrivals list (today only the last 4 digits).

## 2. Deploy order (each step has a rollback)
1. `pg_dump -Fc` backup, kept off the server (new migrations below).
2. Set the production `.env` (checklist section "Production settings"); `DEBUG=False`. There are no payment settings any more. `ARRIVAL_GRACE_HOURS` defaults to 2.
3. Persistent `MEDIA_ROOT` and nginx `/media/` (owner photos, country and region pictures; checklist "safe `/media/` serving").
4. `python manage.py migrate` (new: `bookings/0012_cash_arrival` with a data step that confirms bookings still in their window, `geography/0004`, `partner/0002`, `properties/0016` for the per-currency prices), then `python manage.py check --deploy` (must print "no issues").
5. `python manage.py fetch_exchange_rates` (USD, KZT, RUB from cbu.uz); confirm beat runs it at 09:00 and 18:00. Confirm beat also runs the arrival check every 10 minutes (`cancel_unarrived_bookings`): without beat, guests who do not arrive are never cancelled.
6. Create the super-admin; do NOT run `seed_demo*`; delete any `*@tickbron.demo` rows if the DB came from dev.
7. Owners enter all four prices (UZS, USD, KZT, RUB) per rate plan (mandatory, `RATE_PLAN_PRICES_REQUIRED=true`). Super admin creates the hotel-owner accounts with phone and place.
8. Smoke by hand on the live site: register with a phone number, search, book (arrival time), see the confirmed page, cancel (free), owner arrivals list and "Guest arrived", admin Status (revenue = completed bookings), a photo upload by an owner.

## 3. Tell the hotels
- Press "Guest arrived" on the arrivals list for every guest who comes. A confirmed booking that is not marked is cancelled 2 hours after the arrival time the guest gave, and the room is released.
- Cancelling is free for the guest at any time before the stay starts; nothing is charged or refunded online.

## 4. Known, not fixed (none blocks launch)
Hotel owners cannot rename or edit a hotel after it is created; guest bookings list not paginated; geography table scrolls sideways on phones; the payment tables and `PaymentAuditLog` stay in the database as history (the booking status history is written there); six Dependabot bumps (#29 Django 6.1, #31 Celery 5.6, #33 isort, #35 flake8, #36 black, #38 Playwright) were tested and are safe but not merged, and #65 (Pillow 13) and #71 (the old cash-only stage 3, replaced by #72) are still open; Redis result cache and thumbnails deliberately skipped (R14: 200 users, 0 failures, p95 search 163 ms).

Last full runs before the last merge (cash, pictures and prices together): backend 2901 passed, frontend 1902 passed.
