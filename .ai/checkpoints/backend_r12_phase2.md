# CHECKPOINT

Checkpoint: R12 phase 2 (Status statistics)
Owner: Kolya (Kolya's agent)
Branch: feat/r12-status (phase 1 commits up to de98bb2, phase 2 after it)
Status: READY on the branch. NOT merged into master (see Known issues).

## Implemented
- `bookings/metrics.py`: the one place for the definitions (guests = SUM guest_count, unique_customers, nights, room_nights, stayed, counted, upcoming, no_show, fully_refunded, revenue = paid - succeeded refunds per currency, booking_value = old revenue, booking_status incl. expired), periods (today, last_7/30_days, this_year, last_5/10_years, custom <= 20 years, YYYY, YYYY-MM), granularity day/week/month/year (<= 1000 buckets), series, reconciliation. `bookings/stats.py` keeps the old names as thin wrappers.
- Admin: flat `GET status/hotels/` (search, country/region/status filters, ordering whitelist, top 1000), `GET status/users/{id}/`, hotel detail + booking_status/series/reconciliation, new fields on countries/regions/region hotels/users, CSV export (`common/csv_export.py`: BOM, formula-injection prefix, `CSV_EXPORT_MAX_ROWS`, audit `export_csv`), audit `status_user_view` (`admin_panel/0007`, reversible).
- Owner: summary + series + reconciliation, `status/hotels/{id}/`, `status/arrivals/` (phone last 4 digits, no email), reconciliation CSV.
- `seed_demo_stats` creates matching payments (and refunds for cancelled demo bookings).
- Settings: `CSV_EXPORT_MAX_ROWS`, `NO_SHOW_REPORT_WINDOW_DAYS` (default 7).

## Tests
- New: `bookings/tests/test_r12_metrics.py` (48), `admin_panel/tests/test_r12_status.py`, `partner/tests/test_r12_partner_status.py`, seed payments test. Constant query counts at 5 and 50 rows; five-role access matrix extended.
- TDD proof: phase 2 code reverted to HEAD, tests kept: 42 failed, 12 passed, 1 error (new test files); restored.
- Existing expectations changed (old -> new, reason), assertions not weakened, each marked `# R12:` in the test:
  - guests 3 -> 5 (countries UZ, regions Tashkent), 2 -> 3 (alpha hotel, hotel detail, partner alpha), 3 -> 5 (partner totals): guests = persons, not distinct accounts.
  - revenue USD 530 -> 1529, 350 -> 1349 (countries), KZT-only -> KZT + USD 999 (partner owner2, user ranking guest3, regions "unspecified"): revenue = paid - refunded now includes the money kept from the gamma no-show (999 USD); the fixture now creates the payments.
  - query budgets: countries 3 -> 6, regions 4 -> 7, region hotels 5 -> 8, hotel detail 6 -> 15, users 4 -> 6, partner 8 -> 19 (all constant as data grows; refund rule needs payments/refunds queries and one fully-refunded-ids query).
- Full suite after phase 2: `pytest --create-db` (xdist -n 8): 2242 passed, 0 failed, 2 skipped. (An earlier run caught one real failure, fixed: `manage.py check --deploy` drf_spectacular operationId collisions of the new routes, now explicit `operation_id`s.)

## EXPLAIN (50k bookings, 45k payments, 5.7k refunds, scratch DB `tickbron_explain`, dropped afterwards)
Heaviest queries, found by EXPLAIN ANALYZE of the captured SQL:
- Before (first version): the flat hotels list's COUNT with the per-hotel correlated refund rule ran **> 10 minutes** (cancelled by hand). Cause: the "fully refunded" subquery rebuilt for every hotel row / every FILTER clause.
- After: the hotels revenue sort is computed in two grouped queries and sorted in Python (UZS revenue), the refund rule is evaluated once per request (`metrics.fully_refunded_ids`) and passed as an id list, and the subquery itself was rewritten (refunds joined to paid payments, no per-payment correlated lookup: 83 ms -> 31 ms).
- Endpoint totals now: hotels `-revenue` 0.83 s, `-revenue&period=last_30_days` 0.47 s, `period=this_year` 0.72 s; user detail 63 ms (before the fully-refunded-ids change: 417 ms; user with 24 bookings).
- Candidate indexes (property, status, check_in) and (guest, status, check_in) on 50k bookings: hotels 0.83/0.47/0.72 s -> 1.06/0.45/0.67 s (noise or worse), user detail 63 -> 55 ms. No clear gain, so NOT added.

## Security
- Owner endpoints scoped to own hotels (other owner's id -> 404); arrivals expose phone last 4 only, no email; CSV cells neutralised; exports and user views audit-logged with ids/counts only; ordering and status whitelisted.

## API/contract changes
- `.ai/API_CONTRACT.md` "2026-10-06 R12 phase 2 (R12a)". CHANGED meanings: `guests` (persons), `revenue` (paid - refunded; old = `booking_value`).

## Known issues
- Master merge of phase 1 and 2 was refused by the session's permission rules ("merge without review"); the owner must merge `feat/r12-status`.
- "Stayed" numbers of the last NO_SHOW_REPORT_WINDOW_DAYS days can still change (phase 3).
- No dev database on this computer: nothing migrated, `complete_finished_stays` not run.
