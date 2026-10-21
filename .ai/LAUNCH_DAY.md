# TICKBRON launch day (2026-10-21)

Code status: every ROADMAP item is DONE and merged (last: PR #61 R16 four currencies, PR #62 geography cleanup). Master CI green. Full backend suite 3194 passed (2026-10-19). The list below is only what code cannot do: owner decisions, accounts, servers. Details and exact variable names: `RELEASE_CHECKLIST.md` ("Production settings", "Real credentials still missing", "Prices in four currencies").

## 1. Owner must supply (blocks real money / real mail)
- Payme, Click, Visa keys (`PAYME_*`, `CLICK_*`, `VISA_*`) and a sandbox run of partial refunds (unverified).
- Hosting: server, domain, TLS certificate, nginx (`NUM_PROXIES`, `USE_X_FORWARDED_PROTO`), Postgres, Redis, Celery worker + beat.
- E-mail SMTP (`EMAIL_*`, `FRONTEND_URL`) for password reset. Telegram bot token + chat id for alerts.
- Commission rate and payment model decision; logo files; lawyer review of refund and "Reklama" wording; native-speaker review of uz/ru texts.

## 2. Deploy order (each step has a rollback)
1. `pg_dump -Fc` backup, kept off the server.
2. Set the production `.env` (checklist section "Production settings"); `DEBUG=False`, test modes False.
3. `python manage.py migrate` then `python manage.py check --deploy` (must print "no issues").
4. `python manage.py fetch_exchange_rates` (USD, KZT, RUB from cbu.uz); confirm beat runs it at 09:00 and 18:00.
5. Create the super-admin; do NOT run `seed_demo*`; delete any `*@tickbron.demo` rows if the DB came from dev.
6. Owners enter all four prices (UZS, USD, KZT, RUB) per rate plan (mandatory, `RATE_PLAN_PRICES_REQUIRED=true`).
7. Smoke by hand on the live site: register, search, book, pay (sandbox), cancel, owner calendar, admin Status.

## 3. Known, not fixed (none blocks launch)
Owners cannot upload photos yet; guest bookings list not paginated; geography table scrolls sideways on phones; no cancellation-refund notification; 13 Dependabot PRs (#29-#41) unreviewed; Redis result cache and thumbnails deliberately skipped (R14: 200 users, 0 failures, p95 search 163 ms).
