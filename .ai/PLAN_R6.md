# PLAN R6 — Currency: UZS, daily CBU rate, booking snapshot (BACKEND)

Status: PLAN, waiting for owner approval. No code until approved. Gated item (money + migrations).
Author: Kolya's agent, 2026-10-03. Branch when approved: `feat/r6-currency`.

## 0. Facts checked before planning (2026-10-03)

CBU API, verified with real requests today:
- `GET https://cbu.uz/uz/arkhiv-kursov-valyut/json/USD/YYYY-MM-DD/` → 200 `application/json`, a list with one object:
  `[{"id":1,"Code":"840","Ccy":"USD","CcyNm_RU":"…","CcyNm_UZ":"AQSH dollari","CcyNm_UZC":"…","CcyNm_EN":"US Dollar","Nominal":"1","Rate":"11808.76","Diff":"-12.42","Date":"01.10.2026"}]`
- `Rate`, `Nominal`, `Diff` are **strings**; `Date` is `dd.mm.yyyy`. Value of one unit = `Rate / Nominal` (Nominal is "1" or "10" in today's full list).
- A future date (`…/USD/2026-10-04/`) returns the latest published rate with its own `Date` (`03.10.2026`), so the date must be read from the response, never assumed from the URL.
- Unknown currency (`…/XYZ/…`) returns `[]`. `GET https://cbu.uz/uz/arkhiv-kursov-valyut/json/` returns all 74 currencies (same fields).
- Plain `http://cbu.uz/...` answers 403 (no redirect). The response sets a PHPSESSID cookie (ignored).
- Today USD = 11772.95 UZS (03.10.2026), daily `Diff` -35.81 (0.3%).

Current code:
- `currency` CharField(3, default 'USD', free text, no choices) on Property, RoomType, RatePlan, DateInventory, Booking, BookingItem, PaymentTransaction; Country has `currency` (UZ → UZS).
- Money: `DecimalField(decimal_places=2)` everywhere (Booking.total_price max_digits=12, PaymentTransaction.amount 12, RatePlan/DateInventory 10).
- Booking currency = `rate_plan.currency` (`bookings/models.py:304`); payment must equal `booking.total_price` + `booking.currency` (R4 H-1).
- Dev data: properties USD 12, EUR 3; rate plans USD 19, EUR 3; bookings USD 213, EUR 41 (EUR comes from `seed_demo_stats` Turkey hotels). No UZS yet.
- No HTTP client in requirements (plan uses the standard library, see 2). Celery beat exists (`CELERY_BEAT_SCHEDULE`, `bookings/tasks.py`).

## 1. Currency model and rounding

- New module `common/money.py` (one place for all rules):
  - `SUPPORTED_BASE_CURRENCIES = ('UZS', 'USD')`, `CHARGE_CURRENCY = 'UZS'`.
  - `quantize(amount, currency)`: Decimal only (floats rejected with TypeError). UZS → whole so'm `Decimal('1')`; USD → cents `Decimal('0.01')`; rounding `ROUND_HALF_UP` (commercial rounding, what guests expect).
  - `to_uzs(amount, rate)`: `quantize(amount * rate, 'UZS')`.
- Property `currency` gets choices UZS/USD (validation in serializers + `clean()`); new properties default to their country's currency when it is UZS or USD (Uzbekistan → UZS), else USD. The partner may pick UZS or USD.
- Property currency is authoritative: RoomType, RatePlan and DateInventory currencies must equal it (serializer validation; existing mismatches reported by the migration check, see 7). Partner writes cannot set a different currency on children.
- Nightly prices are stored and shown in the base currency. In a UZS property they must be whole so'm (validation, 400 otherwise).
- **Conversion happens once, on the stay total** (base total → UZS total, rounded once). Nights are not converted one by one, so there is no rounding drift between nights and total. The quote shows nightly prices in the base currency only.
- Exchange rate stored as `Decimal(max_digits=18, decimal_places=6)` = UZS per 1 unit (Rate / Nominal), never float.
- The client can never send currency or rate: booking create has no such fields (already true); payment create amount/currency must equal the booking snapshot (see 5); any extra `currency`, `exchange_rate`, `uzs_total` fields in bodies are ignored (tested).

## 2. Rate source: CBU, only in a scheduled task

- New app `currency` (models, fetch service, task, admin read-only).
- `ExchangeRate` history table (`exchange_rates`): `currency` (USD), `rate` Decimal(18,6) per 1 unit, `nominal`, `rate_date` (CBU `Date`), `source` ('cbu.uz'), `fetched_at`, `status` (`accepted` / `rejected`), `note` (why rejected). Unique (`currency`, `rate_date`, `source`, `status='accepted'`). Append-only like the audit log (no update/delete through the ORM).
- Fetch service `currency/cbu.py`:
  - Fixed URL template `https://cbu.uz/uz/arkhiv-kursov-valyut/json/{ccy}/{date}/` with `ccy` from a constant allow-list ('USD') and `date` = today's ISO date (Asia/Tashkent). No user input reaches the URL.
  - Standard library `urllib.request` with an opener whose redirect handler refuses every redirect (any 3xx = failure), HTTPS only, timeout 10 s, response body capped at 64 KB, `Content-Type` must be JSON.
  - Strict parsing: list with exactly one object, `Ccy == 'USD'`, `Code == '840'`, `Rate`/`Nominal` parse as positive Decimals, `Date` parses as `dd.mm.yyyy` and is not in the future and not older than 10 days. Anything else = failure.
- Celery task `currency.tasks.fetch_exchange_rates`, in `CELERY_BEAT_SCHEDULE` daily at 09:00 and 18:00 Asia/Tashkent (CBU publishes the next day's rate during the day; two runs make sure the new one is picked up; saving the same `rate_date` twice is a no-op). Task retries 3 times, 10 minutes apart, on network errors.
- Management command `fetch_exchange_rates` runs the same function (manual run, first install). Neither the task nor the command is ever called from a request handler.

## 3. Failure behaviour

- Fetch fails (network, timeout, redirect, bad JSON, wrong shape): log a warning (no response body in logs), keep the last accepted rate, nothing else changes. Bookings keep working with the last accepted rate.
- **Stale**: if the latest accepted rate is older than `FX_STALE_AFTER_DAYS` (setting, default 3 days), it is still used, but quote/booking responses carry `exchange_rate.stale: true` and every use logs a warning (rate-limited to once per hour). Staff see it in the API (`GET /admin-panel/exchange-rates/`, staff-only, read-only) so someone can act.
- **Sanity threshold**: a new rate that differs from the previous accepted rate by more than `FX_MAX_CHANGE` (setting, default 10%; normal daily moves are under 1%) is stored with `status='rejected'` and a note, logged as an error, and NOT used. The old rate stays in use until a staff member confirms the new one (`POST /admin-panel/exchange-rates/{id}/accept/`, super-admin only, audit-logged) or a later fetch comes back within the threshold. Non-positive or absurd values (e.g. < 1000 or > 100000 UZS per USD, settings) are rejected the same way.
- **Fresh install, no rate yet**: UZS properties work completely (rate 1, source `identity`, no lookup). For USD properties the quote returns the USD total with `uzs_total: null` and `exchange_rate: null`; booking create returns **503** `{"code": "exchange_rate_unavailable"}`, a clear message and nothing reserved, because Payme/Click can only charge UZS and we must not invent a rate. Running `manage.py fetch_exchange_rates` once fixes it. (Decision point A below.)

## 4. Booking snapshot

New Booking fields (all set once in `Booking.create_booking`, inside the existing transaction, from a DB read of the latest accepted rate; no HTTP):
- `currency` (existing) = base currency of the property; `total_price` (existing) = amount in the base currency.
- `charge_currency` ('UZS'), `charge_amount` (Decimal 14,2, whole so'm) = the amount the guest pays.
- `exchange_rate` (Decimal 18,6; 1 for UZS bases), `exchange_rate_date`, `exchange_rate_source` ('cbu.uz' / 'identity' / 'legacy', see 7), `exchange_rate_stale` (bool, what the guest was shown).
- Immutable after creation: `Booking.save()` refuses changes to these eight fields once the row exists (PermissionError, like AdminAccessLog), and `update()` on these columns is never used. Rate changes after booking change nothing. Proof test (8).
- The booking response includes the snapshot so the payment page shows exactly what will be charged.

## 5. Payments and refunds

- Payme and Click charge UZS only. Payment create rules (replaces the R4 H-1 rule): `amount == booking.charge_amount` and `currency == booking.charge_currency` ('UZS'); anything else 400. The client-sent values are only checked, never used to compute anything.
- Flow for a USD-priced room (100 USD/night, 2 nights, rate 11772.95):
  1. `GET /properties/{id}/quote/` → `total_price "200.00"`, `currency "USD"`, `uzs_total "2354590"` (200 × 11772.95 = 2354590.00, rounded once), `exchange_rate {rate "11772.950000", date "2026-10-03", source "cbu.uz", stale false}`.
  2. `POST /bookings/` → booking stores `total_price 200.00 USD` and the snapshot `charge_amount 2354590.00 UZS`, rate 11772.95 / 2026-10-03 / cbu.uz. If the rate changed between quote and booking (new day), the booking uses the current one and returns it; the payment page shows the booking's amounts, not the old quote.
  3. `POST /payments/transactions/` with `amount "2354590.00"`, `currency "UZS"` → must equal the snapshot. Webhooks compare the provider amount with `tx.amount` (already). Payme's tiyin unit (×100) is converted inside the Payme adapter when the real integration lands (not R6).
- Refunds use the payment transaction's amount (already the UZS snapshot), never today's rate. Partial refunds of UZS payments must be whole so'm (400 otherwise). Booking price changes or rate changes never alter refund limits.

## 6. API changes (documented in `.ai/API_CONTRACT.md` "2026-10-xx Currency")

- Quote: + `uzs_total`, `exchange_rate {rate, date, source, stale}` (null for UZS properties where `uzs_total == total_price`).
- Availability: per rate plan + `currency`; with dates also `uzs_total` per rate plan for the stay (computed from the same quote function, DB rate only).
- Booking (create/list/detail): + `charge_amount`, `charge_currency`, `exchange_rate`, `exchange_rate_date`, `exchange_rate_source`, `exchange_rate_stale`.
- Search results / property detail: amounts stay in the base currency with `currency`; optional `base_price_uzs` (latest rate, informational) — decision point D.
- All amounts are strings with exactly 2 decimals in JSON (`"2354590.00"`); UZS values always end in `.00`.
- Formatting rules for the frontend (documented, frontend implements): UZS → no decimals, digits grouped by 3 with a non-breaking space, suffix "so'm" in uz/en and "сум" in ru: `1 250 000 so'm`. USD → `$1,250.00` (en), `1 250,00 $` (ru/uz). Show the UZS amount as the main number when the user's language is uz/ru or the property is in Uzbekistan; for USD properties also show "≈ $200.00" next to the UZS amount, and "Rate of 03.10.2026 (CBU)" near the total. Stale rate → small note "rate may be out of date".
- New staff endpoints: `GET /admin-panel/exchange-rates/` (staff), `POST /admin-panel/exchange-rates/{id}/accept/` (super-admin; rejected → accepted, audit-logged).

## 7. Migrations (backup first)

- `pg_dump -Fc` of the dev database before each migration run (as in R4), and a line in the release checklist for production.
- `currency/0001`: ExchangeRate table (schema only; reverse drops it).
- `bookings/00xx_booking_charge_snapshot`: new nullable snapshot columns (reverse drops them).
- `bookings/00xx+1_backfill_snapshot` (data): every existing booking gets `charge_currency = currency`, `charge_amount = total_price`, `exchange_rate = 1`, `exchange_rate_date = created_at date`, `exchange_rate_source = 'legacy'`. This records what really happened: old bookings were priced and paid in their own currency (their PaymentTransactions say USD/EUR). Refund limits for them stay their recorded payment amounts. Batched (`iterator()`, 1000 rows). Reverse: no-op (columns are dropped by the schema reverse).
- Then make `charge_currency`/`charge_amount`/`exchange_rate*` NOT NULL for new rows (schema; reverse = nullable again).
- Properties: no data change for USD/UZS. A check step lists properties whose rooms/rate plans/inventory have a different currency than the property (expected 0 outside demo data). EUR handling: decision point B.
- Migration tests: forward + reverse on PostgreSQL (`TransactionTestCase` without `serialized_rollback`, as in R1).

## 8. Tests written first (each must fail before the code)

1. Rounding: UZS half-up to whole so'm (`2354589.50 → 2354590`, `…49 → …589`), USD to cents, floats rejected, conversion rounds the total once (sum of nights ≠ per-night rounding case).
2. CBU fetch with mocked HTTP: success (parses strings, Nominal 10 case, date taken from the body), timeout, 500, redirect refused, non-JSON, `[]`, two items, wrong Ccy, future/old date, oversize body → nothing saved and old rate kept; idempotent re-fetch of the same date.
3. Absurd value: +11% jump stored as rejected and not used; < 1000 rejected; super-admin accept makes it current; staff/guest cannot accept.
4. Stale: rate older than 3 days → still used, `stale: true` in quote and booking, warning logged.
5. No rate yet: UZS property books fine; USD property quote `uzs_total: null`, booking 503 `exchange_rate_unavailable`, no inventory touched.
6. Snapshot immutability: booking created at rate A; new rate B accepted; booking, its payment amount and refund limit unchanged; `save()` with a changed snapshot field raises.
7. USD booking charged in UZS: full flow quote → booking → payment (amount must be the UZS snapshot; USD amount or USD currency → 400) → webhook amount check.
8. Client-sent currency/rate ignored: extra `currency`, `exchange_rate`, `uzs_total` in booking body have no effect; partner cannot set a child currency different from the property.
9. Refund amount: full refund = UZS snapshot even after the rate moved; partial UZS refund with fractions → 400; legacy USD booking refunds in USD.
10. Task/command: beat schedule entry exists; no request handler imports the fetch module (static test: grep of view modules, plus `socket` blocked during the API test run for quote/booking).
11. Migration forward/reverse with legacy rows.

## 9. NOT in R6

- No live rate lookup in any request handler, serializer or model method (only the Celery task and the management command fetch).
- No client-supplied currency, rate or converted amount is ever trusted.
- No re-pricing of existing bookings; no change to old payments.
- No currencies other than UZS and USD as property base currency (unless decision B), no EUR/RUB conversion, no rate APIs other than cbu.uz, no HTML scraping.
- No real Payme/Click/Visa integration or tiyin conversion (credentials missing), no card form (R8).
- No frontend code (formatting rules and contract only, handed off in HANDOFF.md).
- No float arithmetic anywhere in money code.

## Decision points for the owner

- **A. USD property, no rate at all (fresh install)**: plan = booking refused with 503 until the first rate is fetched. Alternative: allow the booking and block payment. Recommendation: refuse (no unpayable bookings holding rooms).
- **B. Existing EUR properties (dev demo data only: 3 Turkey hotels from `seed_demo_stats`)**: plan = change `seed_demo_stats` to USD, and the migration refuses to run if a non-USD/UZS property exists, listing them (dev databases re-seed). Alternative: also allow EUR as a base currency (CBU publishes EUR; little extra work). Recommendation: USD/UZS only, as specified.
- **C. Thresholds**: stale after 3 days, reject jumps over 10%, absurd bounds 1000–100000 UZS per USD. All settings, can change later.
- **D. Search/detail cards**: show an informational `base_price_uzs` from the latest rate (yes/no). Recommendation: yes, marked informational; the charge always comes from the booking snapshot.
