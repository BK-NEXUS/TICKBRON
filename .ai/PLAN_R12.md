# PLAN R12 — Status additions, auto-completion, no-show reports with 50% refund (BACKEND)

Status: PLAN, waiting for owner approval. No feature code until "approved". Gated item (money, refunds, migrations).
Author: Kolya's agent, 2026-10-05. Branch: `feat/r12-status` (from `feat/r6-currency` 95ebbd4, full suite green; master `e6bceeb` with R6 merged in afterwards).
Re-checked 2026-10-05 against master `e6bceeb`: backend code identical to 95ebbd4 (`git diff 95ebbd4 e6bceeb -- backend` empty); audit refs in section 0 spot-checked and still correct (statuses `models.py:33-39`, no caller of `complete_booking`/`mark_no_show` outside tests, state machine `state_machine.py:39-44`, expiry reason `models.py:527`, `TIME_ZONE='UTC'` `settings.py:170`, guests = distinct accounts `stats.py:93`, no Refund model, no Notification created outside tests, Booking indexes `models.py:146-156`).
Owner's second Part B brief (2026-10-05) covers sections 1-3 and stops partway through item 3 (inventory). Sections 4 (no-show refund, NO_SHOW_REFUND_PERCENT) and 5-8 come from the first brief and stay as planned until the owner says otherwise.
A new session continues from section 5 ("Implementation steps"), first step not marked DONE.

## 0. Audit (read-only, 2026-10-05, code at 95ebbd4)

Existing Status code (reuse, extend; no parallel endpoints):
- `backend/bookings/stats.py` — shared definitions. Counted = `confirmed`, `completed` (`stats.py:20`), period by check-in date (`stats.py:9`, `:81-84`), revenue = SUM(`total_price`) per booking currency (`stats.py:103-113`), guests = distinct accounts (`stats.py:93`, `:112`, `:136`). Periods: `all`, `YYYY`, `YYYY-MM` only (`stats.py:42-62`).
- `backend/admin_panel/status.py` — countries (`:180`), regions (`:216`), hotels of one region (`:257`, top 1000 `:36`, search by name only `:269`, fixed order `-bookings, -guests, name` `:274`), hotel detail (`:291`, monthly series only), users ranking (`:334`, audit-logged `:387`). Pagination 20 / max 100 (`:41-44`). Permission `IsSuperAdminOrStaff` (`admin_panel/views.py:42`).
- `backend/partner/status.py` — owner summary (`:26`), own hotels `owner=request.user` (`:38`). Permission `IsHotelOwner` also lets staff in (`partner/views.py:38-40`), staff then see only hotels they own.
- URLs: `admin_panel/urls.py:47-51`, `partner/urls.py:26`.

Bookings:
- Statuses: `pending, confirmed, cancelled, completed, no_show` (`bookings/models.py:33-39`). **`expired` does not exist**: expiry sets `cancelled` with the text reason "Booking expired - payment not completed within time limit" (`bookings/models.py:525-528`, state reason `expiry`).
- State machine: `confirmed → cancelled | completed | no_show`; `completed`, `no_show`, `cancelled` terminal (`bookings/state_machine.py:39-44`). `completed → no_show` is NOT allowed today.
- **Nothing moves a booking to `completed`.** `Booking.complete_booking()` (`bookings/models.py:612`) is only called from tests (`bookings/tests/test_state_machine.py:472`); `seed_demo_stats` writes `completed` directly (`core/management/commands/seed_demo_stats.py:202`). `mark_no_show()` (`bookings/models.py:644`) is also only used by tests. So in real data every paid booking stays `confirmed` forever.
- Fields: `guest_count` (persons, checked against `max_occupancy × number_of_rooms`, `bookings/serializers.py:150-155`), `children` (JSON list of ages, `models.py:104`; whether `guest_count` includes children is not defined in code, see open question 8.7), `number_of_rooms` (`:99`), `number_of_nights` (`:82`), `check_in`/`check_out` DateFields, R6 snapshot `charge_amount`/`charge_currency` (`:118-123`), soft delete `is_deleted`.
- Indexes on Booking (`models.py:146-156`): (status, created_at), (payment_status, created_at), (check_in, check_out), (confirmation_code), (guest, status), (property, status), (expires_at), (status, check_in); plus single-column indexes on guest, property, status, payment_status, check_in, check_out.
- Locking: inventory changes run in `transaction.atomic()` with `select_for_update()` on `DateInventory` per night (`cancel_booking` `models.py:446-462`), row lock `_lock_row()` (`:400`).

Payments and refunds:
- `PaymentTransaction` (`payments/models.py:16`): `amount`, `currency`, status `pending, processing, completed, failed, refunded, partially_refunded`. Index (booking, status) (`:139`).
- **No Refund model.** A refund is a status change on the payment; the refunded amount exists only as text in `PaymentAuditLog.details['refund_amount']` (`payments/views.py:368-398`). Only one refund per payment (status must be `completed`, `payments/views.py:337`), so a second partial refund is impossible. The provider is called INSIDE the DB transaction (`payments/views.py:362`). A failed refund only sets `error_code='REFUND_ERROR'` on the payment (`:404-407`), there is no failed-refund row and no retry.
- Webhooks: `payments/webhooks.py` (idempotent, signature-checked).

Notifications: `accounts.Notification` (`accounts/models.py:117`, types include `booking`; user, title, message, booking FK, read flag) with a list endpoint (`accounts/urls.py:13`). **Nothing creates notifications today** (no `Notification.objects.create` outside tests).

Audit logs: `AdminAccessLog` (`admin_panel/models.py:64`, ids only, append-only, `details` whitelisted since R6) for staff reads/actions; `PaymentAuditLog` (`payments/models.py:343`) for every booking/payment state change (`bookings/models.py:709-729`).

Time zone: `TIME_ZONE = 'UTC'` (`config/settings.py:170`), `CELERY_TIMEZONE = TIME_ZONE` (`:321`). `timezone.localdate()` is therefore the UTC date: used for "today" in `admin_panel/status.py:301`, `partner/status.py:33`, booking create check-in validation (`bookings/models.py:332`, `bookings/serializers.py:106`, `properties/serializers.py:690`). **Finding:** between 00:00 and 05:00 Tashkent the server's "today" is yesterday (a check-in for yesterday is accepted). Only `currency/cbu.py:50` `tashkent_today()` uses Asia/Tashkent.

Rate limiting: DRF throttles (`config/settings.py:263-270`, scoped classes in `users/views.py:33-88`); throttling is off in tests (`TESTING`).

Demo data: `seed_demo_stats` creates bookings without `PaymentTransaction` rows, so payment-based revenue would be 0 for demo data (step 4 updates the seed).

## 1. Definitions (one module, `bookings/metrics.py`; `stats.py` keeps its public functions as thin wrappers)

| Name | Definition | Differs from today? |
|---|---|---|
| `guests` | SUM(`guest_count`) of the bookings in the set | YES: today `guests` = distinct accounts (`stats.py:93`). A family of 4 on one account was 1, becomes 4 |
| `unique_customers` | COUNT(DISTINCT `guest_id`) | new field, = today's `guests` |
| `nights` | SUM(`number_of_nights`) | new |
| `room_nights` | SUM(`number_of_nights × number_of_rooms`) | new |
| `bookings` | COUNT of bookings | same |
| headline (`stayed`) | bookings with status `completed` (not fully refunded) | NEW headline; today the headline is counted (confirmed+completed) |
| `counted` | `confirmed` + `completed` (not fully refunded) | same set as today minus fully refunded |
| `upcoming` | `confirmed` with check-in after today (Tashkent), shown separately, not limited by the period | new |
| `booking_status` | counts per `pending, confirmed, completed, cancelled, expired, no_show, no_show_reported` | new. `expired` = cancelled by expiry (reason constant, see 1a); `no_show_reported` = has a pending NoShowReport (then not in `confirmed`/`completed` counts of `booking_status`) |
| `fully_refunded` | count of counted/no_show bookings excluded by the refund rule | new |
| `revenue` | per currency: SUM(successful payments) − SUM(successful refunds), never mixed | YES: today SUM(`total_price`) in the hotel's own currency (`stats.py:103-113`). Old meaning kept as `booking_value` |

1a. `expired`: no such status. Plan: `cancellation_reason` text moves to a constant `EXPIRY_REASON` (`bookings/models.py:527`), and `expired` = cancelled with that reason. No migration. Alternative (needs a migration): a `cancel_kind` field. Default: the constant.

1b. Cancelled is never a guest, a stay or revenue. Pending is never counted.

1c. Refund rule, per booking and per currency: paid = SUM(payments with status in `completed, refunded, partially_refunded`), refunded = SUM(Refund rows with status `succeeded`) (Refund model, step 3). **Fully refunded** = for every currency with paid > 0, refunded == paid. Failed or pending refunds never count. A fully refunded booking is excluded from guests, bookings, nights and revenue and only appears in `fully_refunded`. A partially refunded booking stays counted; its revenue is paid − refunded. Several payments are summed. A booking with no payment rows is counted with revenue 0 (legacy/demo data, see 0).

1d. An approved `no_show` booking: counted in `no_show`, not in `stayed`/`completed` totals, its revenue = money kept (paid − refunded), and it is never "fully refunded" by the 50% rule (unless the percent is 100, then the refund rule 1c applies).

1e. Date basis = check-in date. "Today" = `tashkent_today()` (moved to `common/dates.py`, re-exported from `currency.cbu`). Check-in is a DateField, so period bounds are plain dates; no UTC conversion of stored values is needed.

1f. Periods (`?period=`): `today`, `last_7_days` (today−6 … today), `last_30_days` (today−29 … today), `this_year` (1 Jan … 31 Dec of the current year), `last_5_years` / `last_10_years` (same day 5/10 years ago + 1 day … today), `custom` with `from`, `to` (ISO dates, `from <= to`, span at most 20 years, else 400), plus existing `all`, `YYYY`, `YYYY-MM`. Note: `last_*` end today, so confirmed future check-ins are outside them (they show in `upcoming`).

1g. Series granularity (`?granularity=`): `day`, `week` (ISO week, Monday), `month`, `year`; at most 1000 buckets (else 400, e.g. `day` over 10 years). Empty buckets included with zeros.

## 2. Automatic completion (client approved) — step 1, own commit

- Celery task `bookings.tasks.complete_finished_stays`, beat `crontab(hour=19, minute=5)` UTC = 00:05 Asia/Tashkent (CELERY_TIMEZONE is UTC; a comment states the Tashkent time, as for the CBU task).
- Selects `confirmed`, not deleted, `check_out < tashkent_today()` (check-out day passed), without a pending NoShowReport. Each booking: `complete_booking()` (row lock, state machine, `PaymentAuditLog` `booking_status_changed` reason `checkout_completed`). Per booking its own transaction, so one failure does not roll back the rest; failures are logged (id only) and the task raises at the end (like `expire_pending_bookings`, `bookings/tasks.py:9-18`).
- Idempotent: a second run finds nothing. Never touches cancelled, pending, expired or no_show (only `confirmed` is selected, and the state machine refuses the rest).
- Run summary in `AdminAccessLog` (actor_id 0 = system, action `auto_complete`, details `{changed, failed}`); `details` whitelist gets `changed`, `failed`.
- Command `python manage.py complete_finished_stays [--dry-run]` for existing data (same function), printing counts.
- No inventory change (the nights are past).
- Same commit: fix the UTC "today" finding (booking create check-in validation uses `tashkent_today()`), with tests at 00:30 Tashkent.

## 3. No-show report workflow (client decision: the hotel reports, staff decide) — step 2

Model `NoShowReport` (`bookings/models.py`, migration with reverse): `booking` FK, `property` FK, `created_by` FK, `comment` (plain text 10–500 chars, stripped, no HTML), `status` (`pending, approved, rejected, withdrawn`), `decided_by` FK null, `decision_comment`, `decided_at`, `created_at`, `updated_at`. Partial unique constraint: one `pending` report per booking. Indexes: (status, created_at), (property, status, created_at).

Owner (hotel owner of the booking's property; another owner's booking → 404):
- `POST /api/v1/partner/bookings/{id}/no-show-report/` `{comment}`: allowed when booking is `confirmed` or `completed`, `check_in < today` (check-in date passed), and `today <= check_out + NO_SHOW_REPORT_WINDOW_DAYS` (setting, default 7). Otherwise 400 with a code (`not_reportable_status`, `too_early`, `window_closed`, `report_exists`). Throttle scope `no_show_report` (20/hour per user).
- `GET /api/v1/partner/no-show-reports/` own reports (filter status, property, paginated).
- `POST /api/v1/partner/no-show-reports/{id}/withdraw/` own `pending` only → `withdrawn`. Owners never decide.
- A pending report does not change the booking. It is counted as `no_show_reported` (neither stayed nor no_show), and auto-completion skips the booking. If a report is rejected or withdrawn after check-out passed, the next nightly run completes the booking.

Staff (`IsSuperAdminOrStaff`):
- `GET /api/v1/admin-panel/no-show-reports/` pending first, oldest first; filters `status`, `property`, `from`/`to` (created date). Each row includes the booking reference, hotel, dates, the owner's comment, the exact refund amount that approval would pay (section 4), and `hotel_flagged`.
- `POST .../{id}/approve/` `{decision_comment}` (required, 10–500) and `POST .../{id}/reject/` `{decision_comment}`. Approve: booking `confirmed|completed → no_show` (state machine gains `completed → no_show`, reason `no_show_report_approved`, allowed only through this path), plus the refund of section 4. Reject: booking unchanged, no money moves.
- Correction (staff, audit-logged): `POST .../{id}/reverse/` `{decision_comment}`. approved → rejected: booking back to `completed` if check-out passed, else `confirmed`; **money already refunded is not taken back** (refunds cannot be reversed with the providers), the decision comment must say so; the guest notice is not repeated. rejected → approved: runs the normal approve (refund once, idempotency key, section 4).
- Every action → `AdminAccessLog` (`no_show_report_approve|reject|reverse`, ids only: report, booking, actor) and `PaymentAuditLog` for the booking state change.

Notifications (existing `accounts.Notification`, type `booking`): the owner gets the decision (approved/rejected, with the decision comment); the guest gets an in-app notice on approval only ("Your booking ABC123 was marked as a no-show; X so'm (50%) will be refunded"). A guest dispute flow is out of scope (next step).

Flag rule (90 days): per hotel, `rate = reports created in the last 90 days / bookings with check-in in the last 90 days (counted + no_show)`; platform average = total reports / total such bookings. A hotel is flagged when it has at least 5 reports AND its rate is at least 3× the platform average AND at least 10% (minimum floor so a near-zero average does not flag everyone). Settings `NO_SHOW_FLAG_MIN_REPORTS=5`, `NO_SHOW_FLAG_FACTOR=3`, `NO_SHOW_FLAG_MIN_RATE=0.10`. Computed in one grouped query per queue page.

Inventory: nights already in the past change nothing. On approval, future nights of a multi-night stay (nights dated after today, Tashkent) are released with the same locking as `cancel_booking` (`select_for_update` on each `DateInventory`, nights in date order, `booked_rooms − rooms`), because the guest is not there and the hotel may resell the room. Default; open question 8.8.

## 4. No-show refund (client decision: NO_SHOW_REFUND_PERCENT, default 50) — step 3

- Setting `NO_SHOW_REFUND_PERCENT` (env, integer 0–100, default 50; startup fails outside 0–100).
- Snapshot: new `Booking.no_show_refund_percent` (PositiveSmallInteger, null), written in `Booking.create_booking` in the same transaction that locks inventory and writes the R6 rate snapshot, and added to the immutable snapshot fields (`save()` refuses changes). **Old bookings** (before the migration): `null` = no automatic no-show refund (they were never told about one); approval then moves the booking to no_show and refunds nothing, the approve dialog says "no no-show refund promised for this booking", staff can still refund by hand with the existing refund. (Open question 8.9.)
- Refund model `Refund` (`payments/models.py`, migration + data migration from existing `payment_refunded` audit rows, reverse = drop): `booking`, `payment_transaction`, `amount`, `currency`, `reason` (`staff`, `no_show`), `status` (`pending, succeeded, failed`), `idempotency_key` (unique), `attempts`, `last_error`, `provider_response`, `created_by`, timestamps. The existing staff refund endpoint writes a Refund row too (same behaviour for the client of that endpoint).
- Amount (whole so'm, ROUND_HALF_UP, `common.money`): `paid` = SUM of successful UZS payments of the booking (= the `charge_amount` snapshot, never today's rate); `already` = SUM of `succeeded` + `pending` refunds; `target = quantize(paid × percent / 100, 'UZS')`; `refund_now = max(0, target − already)`; and `already + refund_now <= paid` is checked inside the transaction with the payments and refunds locked. Failed refunds do not count as already refunded. Several payments: the refund is split across payments, newest first, never more than each payment's remaining amount. Legacy bookings charged in USD/EUR: no automatic refund (snapshot null).
- Approve = ONE `transaction.atomic()`: lock report, booking, payments, refunds; booking → `no_show`; `Refund(status=pending, idempotency_key=f"{booking.id}:no_show")` (unique, so a second approve, a race or a reverse/approve cycle can never create a second one); audit entries; guest notification. Then `transaction.on_commit` → Celery task `payments.tasks.process_refund(refund_id)`, which calls the provider through the existing adapter (`adapter.refund_payment`) outside any DB transaction, then records `succeeded` or `failed` (+ `attempts`, `last_error`). Retries: 3, 10 minutes apart, then stays `failed`. Retrying a refund re-sends the same refund id as the provider's idempotency reference where the provider supports it (Payme/Click rules unverified, see 8.6).
- Provider failure: booking stays `no_show`, refund `failed`, listed in `GET /api/v1/admin-panel/refunds/needs-attention/` (staff; failed or pending > 1 hour), with `POST /api/v1/admin-panel/refunds/{id}/retry/` (super-admin, audit-logged; only `failed`).
- Reject moves no money. Percent 0 → no Refund row.
- Disclosure (client requirement):
  - `GET /properties/{id}/quote/` and `POST /bookings/` responses: `no_show_refund_percent` (int), `no_show_refund_amount` (UZS string, from `uzs_total` / `charge_amount`, null when the UZS amount is unknown), `no_show_refund_text_key` = `"no_show_refund_statement"` with params `{percent, amount}` (frontend text: "If you do not arrive, {percent}% of the amount paid will be refunded: {amount} so'm.", uz/ru/en; lawyer review pending).
  - Booking detail/list: the stored snapshot (same three fields, amount from `charge_amount`).
  - Staff approve dialog: the queue row and `GET .../no-show-reports/{id}/` return `refund_preview {amount, currency, percent, already_refunded, paid}` computed with the same function as approve.

## 5. Implementation steps (each: failing tests first, small commits, push after each; master only when the full suite is green)

1. Auto-completion task + `complete_finished_stays` command + `tashkent_today()` fix for booking create. [no migration except AdminAccessLog action choices]
2. `completed → no_show` transition (report path only), `NoShowReport` model + migration, owner endpoints (create, list, withdraw), staff queue + approve/reject/reverse, notifications, flag rule, inventory release of future nights.
3. `NO_SHOW_REFUND_PERCENT` setting, `Booking.no_show_refund_percent` snapshot + migration, `Refund` model + migration + backfill, existing refund endpoint writes Refund rows, approve-with-refund, `process_refund` task, needs-attention list + retry, disclosure fields on quote/booking.
4. `bookings/metrics.py`: one module with the definitions of section 1 (periods, granularity, guests vs unique_customers, nights, room_nights, booking_status, refund rule, revenue per currency, series). `stats.py` delegates to it; existing endpoints keep their shapes plus the new fields. Update `seed_demo_stats` to create matching payments (DEBUG only).
5. `GET /api/v1/admin-panel/status/users/{id}/` (staff): `?period`, `from`, `to`; totals, `booking_status`, `hotels_visited`, per-hotel breakdown (bookings, nights, guests, spent per currency), paginated booking history; `AdminAccessLog` `status_user_view` with target_user_id.
6. `GET /api/v1/admin-panel/status/hotels/` (staff; flat list next to the existing region list): `period`, `search` (hotel name, city/location, country name/code, region name, all languages), filters `country`, `region`, `status`; `ordering` whitelist `revenue, bookings, guests, nights, rating, created_at` with `-` (unknown → 400); revenue sort uses the UZS revenue; `page_size` max 100; top 1000. Rating = average `overall_rating` of approved reviews (`accounts/models.py:55`).
7. Hotel detail (`/admin-panel/status/hotels/{id}/`): + `booking_status`, `series` for `granularity`, `reconciliation` block (today, this week, this month, this year, all time: guests and bookings, stayed and counted). Existing `monthly` kept.
8. Owner: `GET /partner/status/` + `GET /partner/status/hotels/{id}/` (same shapes as 7, own hotels only, another owner's id → 404), series day/week/month/year, reconciliation block, `GET /partner/status/arrivals/?day=today|tomorrow` (guest name, booking reference, room type, rooms, nights, special requests, phone last 4 digits only, no email).
9. CSV export: `?export=csv` on the admin hotels list, users ranking, user detail history and the owner reconciliation table. Same permissions and filters, UTF-8 with BOM, `StreamingHttpResponse`, max rows `CSV_EXPORT_MAX_ROWS` (default 10000, then a final "truncated" line), cells starting with `= + - @` (and tab / CR) prefixed with `'`, `AdminAccessLog` `export_csv` (details: export name, row count).
10. `API_CONTRACT.md` for every new field/endpoint; after merging into master `READY FOR FRONTEND: R12 - <endpoints, fields, definitions>` in `HANDOFF.md`.

Migrations (all reversible, `pg_dump -Fc` of the dev DB before each run): AdminAccessLog choices (1), NoShowReport (2), Booking.no_show_refund_percent + Refund + backfill (3), indexes if EXPLAIN shows a gain (4/6).

## 6. Tests to write first

- Consistency: for one period, SUM over all users == SUM over all hotels (bookings, guests, nights, revenue per currency); one user's per-hotel row == that hotel's numbers filtered to that user.
- Tashkent midnight: check-in today vs yesterday at 23:59 / 00:01 Tashkent (freezegun or patched `tashkent_today`); auto-completion at 00:05 Tashkent.
- Cancelled and pending excluded; `persons` vs `unique_customers` (one account, 3 bookings of 2 and 4 persons → guests 10, unique 1).
- Refund rule: full refund excluded (two payments, one refund each); partial stays with paid − refunded; failed refund ignored; different currencies never mixed.
- No-show workflow: permissions (five roles), too early, window closed, double report, other owner 404, pending report blocks completion, approve (confirmed and completed), reject, withdraw, reverse both ways, notifications, flag rule.
- Refund: amount (50% of 2 354 590 → 1 177 295, half-up on odd so'm), snapshot immutable after the setting changes, old booking null → no refund, double approve / concurrent approve → one Refund, earlier partial refund and earlier failed refund, several payments, total never exceeds paid, provider failure → failed + needs-attention + retry → succeeded, provider called only after commit (no call when the transaction rolls back).
- Owner cannot read or touch another owner's hotel, report or arrivals; arrivals phone masked, no email.
- Access matrix with all five roles (anonymous, guest, owner, staff, superadmin) on every new endpoint (extend `core/tests/test_r4_permission_matrix.py`).
- Sort whitelist (unknown → 400), page_size cap, custom range validation (from > to, > 20 years, bad dates), granularity bucket cap.
- Constant query count as data grows (`django_assert_max_num_queries` with 5 and 50 hotels/bookings).
- Audit entries for user view, exports, report decisions, auto-completion run.
- CSV: BOM, injection prefix, max rows, same filters as JSON, permissions.
- EXPLAIN (ANALYZE) of the heaviest queries (hotels list with revenue sort, user detail) on ~50k seeded bookings, before/after candidate indexes (property, status, check_in) and (guest, status, check_in); add only those that change the plan/time; report both.

## 7. Frontend needs (also written to HANDOFF.md "Frontend needs (R12, PLANNED)")

- Owner: "Guest did not arrive" button with a comment dialog (10–500 chars) on the arrivals and bookings lists (only when allowed: show the API error code otherwise); "My reports" list with withdraw.
- Staff: "No-show reports" queue (pending first, filters, flagged-hotel badge) with approve/reject dialogs showing the exact refund amount and requiring a comment; needs-attention refunds list with retry.
- Refund statement on the payment step (before the pay button), the confirmation page and My bookings, in uz/ru/en from `no_show_refund_text_key`, never computed by the frontend.
- New status labels: `no_show`, `no_show_reported`, `expired`, refund `pending/succeeded/failed`.
- Status pages: period selector with the new periods and custom range, granularity selector, reconciliation block, hotels list with sort/search/filters, user detail page, CSV download buttons.

## 8. Open questions for the client (defaults used until answered)

1. The percent is taken from the amount actually paid (UZS snapshot), not the booking value. Default: yes.
2. It applies to all rate plans, including non-refundable ones. Default: yes.
3. No commission logic yet (`stats.commission_amount` stays None).
4. Provider fees ignored for now.
5. A lawyer must review the guest-facing statement in uz/ru/en before production.
6. Payme and Click partial-refund rules must be verified in each sandbox (NOT verified; RELEASE_CHECKLIST "Unverified before production").
7. Does `guest_count` include children? Default: yes (it is checked against room occupancy), so `guests` = SUM(`guest_count`) and `children` is not added again.
8. Release future nights on approval so the hotel can resell them? Default: yes.
9. Old bookings without a percent snapshot: default no automatic no-show refund. Alternative: use 50%.
10. "Minus refunds already made": default `refund = 50% × paid − already refunded` (floor 0), i.e. the guest ends with at most 50% back in total. Alternative: 50% of (paid − refunded).
11. Staff reversing an approved no-show: money already refunded is not taken back. Default: yes.
12. Changing `guests` from accounts to persons changes existing Status numbers (contract change, documented). Default: yes, `unique_customers` keeps the old number.
