# PLAN R10 — Promotions ("Reklama"): paid placement of hotels (BACKEND)

Status: DRAFT for the owner's approval, 2026-10-09. No code is changed until the owner approves (money, permissions and a migration are involved: approval gate in `.ai/README.md`).
Scope: the promotion part of ROADMAP R10 only. Discounts on rate plans (R10b) and the home page layout are separate. No online payment of advertising in this item: prices are agreed and invoiced outside the platform and the super-admin records the payment.
Author: Kolya's agent. Branch for the work: `feat/be-promotions` from master after the owner merges the open PRs.

## 0. What the client asked for (from the project document)

- Promoted hotels stand at the very top of the normal list with a "Reklama" label (Uzum Market style).
- Only hotels that match the guest's query (city, dates, filters) are shown, not every paid hotel.
- Super-admin manages it; the owner sends a request; there is a price list; views and clicks are counted; expired promotions stop by themselves; optionally by region.
- Open questions are in section 8 with a proposed default for each; the agent builds the defaults and the owner can change them before step S1.

## 1. Audit of the code today (read-only, master `66a77d5` plus the frontend PRs)

- Search: `properties/views.py:45` `property_search` -> `PropertySearchService.search` (`properties/search.py`). `searchable_properties()` = `is_active`, not deleted, `status='active'`. Sorts: `relevance, price_asc, price_desc, rating, reviews, distance`. Response is paginated (`count`, `results`), page size 1-100. Throttle `SearchRateThrottle`.
- Property statuses `draft, pending_approval, active, suspended, rejected` (`properties/models.py:60`): only `active` can be served.
- Geography refs exist on Property (`city_ref`, `region_ref`, `country_ref`, `search.py:GEOGRAPHY_LEVELS`).
- Permissions: `IsSuperAdmin`, `IsSuperAdminOrStaff` (`admin_panel/views.py:42,59`), `IsHotelOwner` (`partner/views.py:30`, owners and staff; staff then see only hotels they own). The permission matrix test is `admin_panel/tests/test_access_matrix.py` (5 roles per endpoint).
- Audit: `AdminAccessLog` (`admin_panel/models.py:64`; ids only, `details` whitelisted, action choices list). New actions need a choices migration.
- Time: `common.dates.business_today()` (Asia/Tashkent). Celery beat already runs `complete-finished-stays` at 00:05 Tashkent (`config/settings.py:346`).
- Redis is already required in production (Celery); `django-ratelimit` and DRF throttles are available.
- Nothing about advertising exists yet (grep `promot|advert` finds only ROADMAP R10).

## 2. Data model (new app `promotions`)

`PromotionPrice` (the price list, super-admin edits it)
- `placement` (`search_top`, `home_carousel`), `days` (7, 14, 30 ...), `amount` Decimal, `currency` (UZS default), `is_active`. Unique (placement, days, currency).

`PromotionRequest` (an owner asks)
- `property` FK (own hotel), `placement`, `days` (one of the active prices), `desired_start` date, `note` (max 500, no contact data), `status` (`pending`, `approved`, `rejected`), `decided_by`, `decided_at`, `reject_reason`, `promotion` FK (set on approval), timestamps.

`Promotion` (what is actually served)
- `property` FK (PROTECT), `placement`, `start_date`, `end_date` (inclusive, business dates), `priority` (0-100, higher first), optional geography scope `country_ref` / `region_ref` / `city_ref` (empty = everywhere),
- money snapshot: `price_amount`, `price_currency` (copied from the price list or a custom amount with a reason), `invoice_reference` (text, e.g. the invoice number), `paid_at` (null until the super-admin records the payment), `paid_marked_by`,
- `status`: `scheduled` (created, waiting for start or payment), `active`, `paused`, `ended`, `cancelled`; `cancelled_reason`; created_by, timestamps, soft delete (BaseModel).
- "Served now" is always computed, never trusted from `status`: `status in (scheduled, active)`, `paid_at` set, `start_date <= business_today() <= end_date`, property `active`. The Celery task below only tidies `status` for the admin lists.
- Rules checked in the service, inside `transaction.atomic()` with `select_for_update()` on the property row: dates (`start_date >= business_today()` on create, `end_date >= start_date`, at most `PROMOTION_MAX_DAYS` = 365), **no overlap** of the same property and placement (cancelled and ended rows ignored). The same overlap rule is the concurrency test target. Defence in depth (PostgreSQL only, needs `btree_gist`): an `ExclusionConstraint`; ask the owner whether the extension may be enabled on the production database before adding it.

`PromotionDailyStat`
- `promotion` FK, `date` (business date), `impressions`, `clicks`; unique (promotion, date). Counters change with one atomic `F()` UPDATE (get_or_create then update), never read-modify-write. No personal data, no IP, no user id.

Migrations: `promotions.0001_initial` (all tables, reversible = drop), `admin_panel` choices migration for new audit actions. `pg_dump` of the dev database before applying (CLAUDE.md rule). No existing table gets a column.

## 3. Serving rules

Search (`/api/v1/properties/search/`, additive):
- Page 1 only, and only when the request has no `sort` other than `relevance` (an explicit price/rating sort stays clean): the response gets a new key `sponsored` (list, at most `PROMOTION_SEARCH_SLOTS`, default 3) in front of `results`.
- A sponsored hotel must be inside the SAME filtered result set the guest asked for (query text, city, dates/availability, price, features, amenities, rating, guests) and must match the promotion's geography scope if it has one. That is how "only matching hotels" is guaranteed: the promoted ids are intersected with the filtered queryset, not added to it.
- Order: `priority` desc, then a daily rotation among equal priority (stable hash of the business date and the promotion id, so slots are shared fairly and the order does not flicker within a day).
- A sponsored hotel is removed from `results` (no duplicate); `count` stays the number of organic results, so pagination arithmetic is unchanged.
- Each sponsored item carries `is_sponsored: true`, `promotion_id`; the frontend shows the "Reklama" label (text from i18n). Organic items have `is_sponsored: false`.

Home carousel: `GET /api/v1/promotions/home/` (public, throttled, cacheable 60 s): active `home_carousel` promotions, at most `PROMOTION_HOME_SLOTS` (default 8), optional `?country=<id>` for scoped ones, same card fields as search plus `is_sponsored` and `promotion_id`.

Counting:
- Impression = the item was returned in a response (server side, so no client script is needed). Click = `POST /api/v1/promotions/<id>/click/` (public, throttled, 204), called by the frontend when a sponsored card is opened.
- Dedupe against refresh and scripts: Redis `cache.add("promo:<kind>:<id>:<hash(session or ip)>", 1, 3600)`; only the first event per hour per visitor counts. The key holds a salted hash, not the IP. If the cache is unavailable nothing is counted and a warning is logged (fail closed: a wrong invoice is worse than a missed count).
- Unknown or not-served promotion id on click: 404 without counting.

Expiry: Celery beat daily 00:10 Asia/Tashkent `promotions.tasks.end_expired_promotions` (`end_date < business_today()` -> `ended`; `scheduled -> active` when paid and started). Serving does not depend on it.

## 4. API

Public: `GET /api/v1/promotions/home/`, `POST /api/v1/promotions/<id>/click/`, `sponsored` key in search.

Super-admin (`IsSuperAdmin` for writes, `IsSuperAdminOrStaff` for reads), under `/api/v1/admin-panel/`:
- `promotions/` GET (search by hotel name, filter `status`, `placement`, dates, `paid`; order by start, priority, clicks; paginated) and POST (create from a price-list row or a custom amount with `reason`); `promotions/<id>/` GET, PATCH (priority, dates, scope, invoice reference; dates re-run the overlap check); POST `promotions/<id>/pause/`, `resume/`, `cancel/` (reason), `mark-paid/` (invoice reference); `promotions/<id>/stats/?from=&to=` (daily impressions, clicks, CTR).
- `promotion-requests/` GET; POST `promotion-requests/<id>/approve/` (creates the Promotion, price from the list) and `reject/` (reason).
- `promotion-prices/` GET, POST, PATCH, no delete (set `is_active=false`).

Owner (`IsHotelOwner`, own hotels only; a foreign id answers 404):
- `partner/promotion-prices/` GET; `partner/promotion-requests/` GET, POST (property must be the owner's and `active`); `partner/promotions/` GET (own, with dates, status, paid flag and stats if question 6 stays "yes").

Errors use the existing uniform envelope. Money is only ever written by the backend; the owner never sends an amount.

## 5. Security and audit

- Access matrix: every new endpoint gets a row for anonymous, guest, hotel-owner, staff, super-admin (`test_access_matrix.py`).
- Owner isolation: requests, promotions and stats of another owner are never listed and answer 404.
- Audit rows in `AdminAccessLog` (new actions, ids and non-personal facts only): `promotion_create`, `promotion_update`, `promotion_pause`, `promotion_resume`, `promotion_cancel`, `promotion_mark_paid`, `promotion_request_approve`, `promotion_request_reject`, `promotion_price_change`. `details` hold ids, dates, amount and currency, never names or contact data.
- Validation of every input (dates, enums, lengths); free text (`note`, `reason`) is length-limited and never rendered as HTML by the API.
- Throttles: click and home endpoints (anonymous scope), owner request creation (user scope, a few per hour).
- A suspended, rejected or draft hotel is never served even if paid; the admin list marks such a promotion "blocked: hotel not active".

## 6. Implementation steps (each: tests first, full `pytest --create-db`, commit, push)

- S0 This plan; the owner approves or changes section 8. WAIT.
- S1 Models, services (overlap check, "served now" query, rotation, price snapshot), migrations (reversible), `pg_dump` first; model and service tests.
- S2 Search integration: `sponsored` key, intersection with the filtered set, page 1 only, no duplicates, geography scope; tests incl. filters, dates, sort, pagination.
- S3 Home carousel endpoint; impressions and clicks with the Redis dedupe; tests incl. cache down.
- S4 Super-admin endpoints (promotions, requests, prices) + audit actions + stats; tests incl. access matrix rows.
- S5 Owner endpoints; owner isolation tests.
- S6 Celery task, beat entry (00:10 Tashkent), tests with the business date at 00:30 and 23:30.
- S7 Concurrency test (two requests for overlapping dates, one wins), EXPLAIN of the search and home queries, demo data (`seed_demo_stats`: a few paid and expired promotions).
- S8 `API_CONTRACT.md` section, `HANDOFF.md` note, `RELEASE_CHECKLIST.md` (Celery beat required, Redis required), then `READY FOR FRONTEND: R10 promotions`.

## 7. Frontend (not part of this item; for the contract)

Search results: sponsored cards first with the "Reklama" label and a `click` call on open. Home: carousel from the home endpoint. Admin: promotion list with search, create/edit, requests queue, price list, stats. Owner: "Reklama" tab (request form with the price list, own promotions and numbers). The label text is an i18n key (uz/ru/en); its legal wording is question 9.

## 8. Decisions needed from the client (agent default in brackets; change before S1)

1. Who may advertise: hotels only [yes; restaurants or other businesses would need their own entity and are a later item].
2. Where: search top and home carousel [both; region landing pages later].
3. Price model: a flat price per placement and period from a price list [yes; per-click or per-view bidding is not planned]. The price list values (in so'm) and the invoice and payment process [offline: the super-admin issues the invoice and records `paid_at`; nothing is served before it].
4. Slots and rotation: 3 in search, 8 on the home page, equal priority rotates daily [yes].
5. Region targeting [optional per promotion].
6. Owners see views and clicks of their own promotions [yes].
7. Cancelling a paid promotion early: money back [not handled by the system: the super-admin cancels and settles outside the platform].
8. May a hotel that is not approved or is suspended be promoted [no].
9. The exact "Reklama" label wording and any legal requirement for advertising marks in Uzbekistan [the lawyer confirms; the label is an i18n key].
10. Production database: may the `btree_gist` extension be enabled for the overlap constraint [if not, the transaction check alone is used].

## 9. Out of scope

Online payment of advertising, bidding or auctions, discounts on rate plans (R10b), banners for non-hotel businesses, A/B tests, frontend work, performance caching of the active-promotions list (R14 if needed).
