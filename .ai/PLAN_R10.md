# PLAN R10 — Promotions ("Reklama"): paid banner carousel of hotels (BACKEND + layout)

Status: DRAFT v2 for the owner's approval, 2026-10-09. No code is changed until the owner says "ha" (money, permissions and a migration are involved: approval gate in `.ai/README.md`).
Scope: the promotion part of ROADMAP R10 only. Discounts on rate plans (R10b) are separate. No online payment of advertising: the owner of a hotel contacts the super-admin, they agree the price outside the platform, the super-admin switches the promotion on.
Branch for the work: `feat/be-promotions` from master after the owner merges the open PRs.

## 0. Owner's decisions (2026-10-09)

1. Only hotels can be promoted.
2. Reklama = ONE big banner at a time, auto-rotating carousel (like Uzum Market), same on phone and desktop, 8 banners in rotation. It sits at the very top of the search results page, above the filters and the hotel list. The same carousel is on the home page.
3. The hotel list below is exactly 2 columns (phone and desktop) with Booking.com-style filters (left on desktop, "Filtrlar" button on phone).
4. No request flow: the hotel owner phones or writes to the super-admin; the super-admin finds the hotel by name and presses "Reklama qilish". The super-admin alone decides whether a hotel is promoted. A hotel that is not approved or is suspended can be promoted by the admin but is NOT shown while it is not active (see 5).
5. Owners do not need statistics; only the super-admin sees them. Region targeting: yes, optional.

## 1. Layout (frontend contract)

- Banner = the hotel's cover photo (wide crop, no new upload), name, city, star rating, "from" price per night in the guest's currency, small "Reklama" badge, click opens the hotel page. Arrows on desktop, swipe on phone, dots, auto-advance every 5 s, pauses on hover/touch and when the tab is hidden, respects `prefers-reduced-motion` (no auto-advance).
- Search page: banner carousel only shows hotels that match the guest's query (city, dates, filters). Zero matching promoted hotels = the block is not rendered (no empty frame).
- Home page: banners of all active promotions (optionally scoped by region).
- Loading = skeleton of the same height (no layout jump), error = the block is hidden (advertising must never break search).
- Texts are i18n keys (uz/ru/en); "Reklama" is the label (Uzbek law requires advertising to be recognisable as such; the lawyer confirms the exact wording, the key is easy to change).

## 2. Code audit (read-only)

- Search: `properties/views.py:45` `property_search` -> `PropertySearchService.search` (`properties/search.py`); `searchable_properties()` = active, not deleted, `status='active'`. Pagination `count`/`results`, throttle `SearchRateThrottle`.
- Property has `city_ref`, `region_ref`, `country_ref` (`search.py:GEOGRAPHY_LEVELS`).
- Permissions `IsSuperAdmin`, `IsSuperAdminOrStaff` (`admin_panel/views.py:42,59`); access matrix test `admin_panel/tests/test_access_matrix.py` (5 roles per endpoint).
- Audit `AdminAccessLog` (`admin_panel/models.py:64`, action choices -> needs a choices migration).
- `common.dates.business_today()` (Asia/Tashkent); Celery beat already runs `complete-finished-stays` at 00:05 (`config/settings.py:346`); Redis already required.
- Nothing about advertising exists (grep `promot|advert`).

## 3. Data model (new app `promotions`)

`Promotion` (one row = one paid period of one hotel)
- `property` FK (PROTECT), `start_date`, `end_date` (inclusive, business dates, max 365 days), `priority` (0-100, higher first),
- optional scope `country_ref` / `region_ref` / `city_ref` (empty = everywhere),
- `price_amount`, `price_currency` (the agreed price, typed by the super-admin, only a record for the books), `note` (<=500, internal),
- `paid_at` (null until the super-admin records the payment; nothing is shown before), `paid_marked_by`,
- `status`: `scheduled`, `active`, `paused`, `ended`, `cancelled`; `cancelled_reason`; created_by; BaseModel soft delete.
- "Shown now" is always computed, never trusted from `status`: status in (scheduled, active), `paid_at` set, `start_date <= business_today() <= end_date`, property `active`, not deleted.
- Service rules in `transaction.atomic()` + `select_for_update()` on the property row: `end_date >= start_date`, `start_date >= business_today()` on create, no overlap for the same property (cancelled/ended ignored), valid scope. Concurrency test: two simultaneous creates for overlapping dates, exactly one wins. (Optional DB constraint `btree_gist` ExclusionConstraint is NOT added now; the transaction check is the guard.)

`PromotionDailyStat`: `promotion`, `date`, `impressions`, `clicks`; unique (promotion, date); one atomic `F()` UPDATE. No IP, no user id.

No price list, no request table, no owner endpoints (decision 4). Migrations: `promotions.0001_initial` (reversible), `admin_panel` choices migration; `pg_dump` first. No existing table gets a column.

## 4. Serving rules

- Search `/api/v1/properties/search/` gets an additive key `promoted` (list, at most 8): promotions whose hotel is inside the SAME filtered set the guest asked for (the promoted ids are intersected with the filtered queryset, never added to it) and that match the geography scope. Only on page 1. The normal `results` and `count` are untouched (a promoted hotel may also appear in the list; the banner is a separate block).
- Order: `priority` desc, then a daily rotation among equal priority (stable hash of business date and promotion id), so everyone gets shown fairly and the order does not flicker within a day. The carousel shows the first 8.
- Home: `GET /api/v1/promotions/home/` (public, throttled, cache 60 s): up to 8, optional `?country=<id>` for scoped ones.
- Item fields: card fields of the hotel (id, name, city, cover image, stars, rating, from-price in the hotel's currency) + `promotion_id`.
- Counting: impression = item returned in a response; click = `POST /api/v1/promotions/<id>/click/` (public, throttled, 204; unknown or not-shown id = 404, nothing counted). Dedupe against refresh and scripts: Redis `cache.add("promo:<kind>:<id>:<salted hash of session or ip>", 1, 3600)`, one event per visitor per hour; cache down = nothing counted + a warning (fail closed). Only the hash is in the key.
- Expiry: Celery beat 00:10 Asia/Tashkent `promotions.tasks.end_expired_promotions` (`end_date < business_today()` -> `ended`; scheduled -> active when paid and started). Serving never depends on it.

## 5. Super-admin API (`/api/v1/admin-panel/`; writes `IsSuperAdmin`, reads `IsSuperAdminOrStaff`)

- `promotion-hotels/?q=` : search hotels by name (id, name, city, status, has-active-promotion flag) for the "find the hotel" box.
- `promotions/` GET (filters: hotel name, status, paid, dates; ordered by start/priority; paginated) and POST (hotel, dates, priority, scope, price, currency, note; "Reklama qilish" button).
- `promotions/<id>/` GET, PATCH (dates re-run the overlap check, priority, scope, price, note); POST `pause/`, `resume/`, `cancel/` (reason), `mark-paid/`.
- `promotions/<id>/stats/?from=&to=`: daily impressions, clicks, CTR.
- A promotion whose hotel is not active is listed with `blocked_reason = "hotel_not_active"`.

## 6. Security and audit

- Access matrix row per endpoint for anonymous, guest, hotel-owner, staff, super-admin (owners and guests get 403 on all admin endpoints).
- Audit in `AdminAccessLog` (ids and non-personal facts only): `promotion_create`, `promotion_update`, `promotion_pause`, `promotion_resume`, `promotion_cancel`, `promotion_mark_paid`.
- Every input validated (dates, enums, lengths, scope refs exist); free text is length-limited, never HTML.
- Throttles on click and home endpoints. A suspended/rejected/draft hotel is never served even if paid.
- Money: amounts are only a record typed by the super-admin; nothing in booking or payment reads them.

## 7. Steps (each: tests first, full `pytest --create-db`, commit, push)

- S0 This plan; the owner says "ha". WAIT.
- S1 Models, service (overlap, shown-now query, rotation), migrations, tests.
- S2 Search `promoted` key (filters, dates, scope, page 1 only); tests.
- S3 Home endpoint, impressions/clicks with Redis dedupe, tests incl. cache down.
- S4 Super-admin endpoints + hotel search + audit + stats + access-matrix rows.
- S5 Celery task + beat (00:10), tests at 00:30 and 23:30 Tashkent.
- S6 Concurrency test, EXPLAIN of the queries, demo data.
- S7 `API_CONTRACT.md`, `HANDOFF.md`, `RELEASE_CHECKLIST.md`, then `READY FOR FRONTEND: R10 promotions`.
- Frontend after that (separate item): banner carousel component, search page re-layout (2-column list, filters), admin "Reklama" screen (hotel search, create, list, stats).

## 8. Left to the client / lawyer

- Exact wording of the "Reklama" label and advertising-law requirements in Uzbekistan (lawyer).
- Prices and invoices: outside the platform.
- Early cancellation refunds: settled outside the platform; the admin cancels with a reason.

## 9. Out of scope

Online payment of advertising, owner requests and price list, bidding, discounts (R10b), banners for non-hotels, uploading custom banner images, A/B tests.
