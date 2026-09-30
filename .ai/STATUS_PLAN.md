===== PLAN: Status sections =====
Definitions
- A booking "counts" when its status is confirmed or completed (not pending, not cancelled).
- Revenue = sum of total price of counted bookings (gross booking value). Commission is not defined yet: leave one clearly named place to add it later. If several currencies exist, group totals per currency instead of mixing them.
- Users/guests = distinct guest accounts with counted bookings, plus their booking count.
- Period filter everywhere: a month (YYYY-MM), a year, or all time.
- All aggregation in the database (annotate/aggregate, no Python loops over rows), paginated, with indexes where needed. Admin Status endpoints: staff and super-admin only. Owner Status endpoints: only the owner's own properties. Extend the access-matrix tests for every new endpoint.

Geography
- Inspect the Property model. If there is no region/province field, add a nullable region field with a migration, backfill it from the city where obvious (Tashkent, Samarkand, Bukhara), and let the partner and admin property forms set it. Levels for now: country (text) > region > hotel. Hotels without a region are grouped as "Unspecified". A full Country > Region > City dictionary is a later phase.

Demo data
- Management command seed_demo_stats: DEBUG only, idempotent, clearly marked as demo in code and docs. About 3 countries (Uzbekistan, Kazakhstan, Turkey), about 4 regions, about 12 hotels with owner accounts, about 60 guests, about 250 bookings over the last 12 months with a mix of confirmed, completed and cancelled, realistic prices. Print how to run it.

Backend endpoints under /api/v1/admin-panel/status/ (all accept period and search, and are paginated):
1. countries/ : ranking (top 100) with bookings, guests, revenue, hotel count. Search by country name.
2. countries/{country}/regions/ : top 100 regions, same metrics.
3. countries/{country}/regions/{region}/hotels/ : top 1000 hotels, paginated, same metrics. Search by hotel name.
4. hotels/{id}/ : hotel info (name, address, owner name and contact, registration date), totals, and a monthly series (selectable year): bookings, guests, revenue per month.
5. users/ : top 1000 guests ranked by counted bookings, with name, phone, email, bookings count, total spent, last booking date. Search by first name, last name, phone, email, ID (partial match). Each row links to the existing customer profile.
Owner endpoints under /api/v1/partner/status/: summary since the account was created (bookings, guests, revenue), selectable month or year, a per-property breakdown, and a monthly series.

Frontend
- Admin panel > "Status" with two tiles: Countries and Users.
- Countries > click a row > Regions > click > Hotels > click > Hotel detail with a month/year selector and a simple bar chart (monthly revenue and guests; reuse the chart approach of the existing statistics dashboard, no new heavy dependency).
- Every screen: a search box that searches only inside the current list, a period selector, back button and breadcrumbs (Status > Uzbekistan > Tashkent > Hotel), loading, empty and error states, pagination, numbers with thousand separators.
- Users screen: table with search; clicking a row opens the existing customer profile page.
- Partner panel > "Status" tab: summary cards (guests via TICKBRON, revenue, since date), month/year selector, monthly chart, per-property table.

Steps
S1 backend: region field + seed_demo_stats.
S2 backend: countries, regions, hotels endpoints with tests.
S3 backend: hotel detail + users endpoints with tests.
S4 backend: partner status endpoints with tests.
S5 frontend: admin Status, countries > regions > hotels > hotel detail.
S6 frontend: admin Status, users.
S7 frontend: partner Status tab.
S8 E2E: admin drills down country > region > hotel > detail; searches a user; an owner sees only own numbers.
===== END OF PLAN =====
