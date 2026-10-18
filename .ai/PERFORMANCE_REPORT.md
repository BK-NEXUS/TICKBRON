# Performance report (R14), 2026-10-12

Measured in-process (no network) on a scratch database: 2,000 hotels, 4,000 room types, 8,000 rate plans, 10,000 bookings,
300 guests (`seed_demo_bulk`, DEBUG only). Median of 5 calls after one warm-up. The guest has 637 bookings, the owner 200 hotels.

| Endpoint | Queries before | Queries after | Median ms before | Median ms after |
|---|---|---|---|---|
| Search page (20 hotels) | 47-48 | 6-7 | 153-251 | 56-162 |
| Hotel page | 18 | 11 | 51 | 25 |
| Guest bookings list (637 bookings) | 1279 | 5 | 1769 | 245 |
| Guest favorites (20) | 25 | 6 | 47 | 20 |
| Owner bookings (200 hotels) | 93 | 6 | 214 | 15 |
| Everything else measured (filter-options, suggestions, availability, quote, promotions home, owner properties/status, admin status/customers/properties) | unchanged | unchanged | 5-235 | 5-228 |

## What changed
- Search, hotel page, favorites, guest bookings, owner bookings: the serializers re-queried rows the view had already prefetched
  (`.filter()` on a prefetched relation ignores the prefetch). Filters now run inside the `Prefetch` queryset, so the query
  count no longer depends on the number of rows. Each has a constant-query-count test (`bookings/tests/test_perf_queries.py`,
  `properties/tests/test_perf_queries.py`).
- Favorites never showed a photo: the serializer read `photo.photo_url`, which does not exist on the model, and a bare `except`
  hid the error. It now returns the photo URL.

## Measured and left alone
- Caching (filter-options 18 ms, suggestions 16 ms, promotions home 6 ms): not worth the invalidation risk.
- Promotions `ordered()` sorts in Python because the daily rotation uses a hash of (date, id); the set it sorts is the running paid promotions only (6 ms for the home call).
- No new indexes or migrations: no measured endpoint is slow because of a missing index. Slowest remaining: text search 162 ms and admin status hotels 228 ms.
- `pg_trgm`/GIN for text search: not needed at this volume; needs the extension (database privilege), so it is for the owner to decide if volume grows.

## Needs the owner's decision
- The guest bookings list is not paginated: 691 KB for a guest with 637 bookings. Paginating changes the API contract (the frontend `BookingsPage` expects an array). Normal guests have a few bookings; proposed only if this is a real case.

## Load test, 2026-10-18 (R14)
Tool: Locust (`backend/scripts/loadtest/`, README there). 200 simulated users for 2 minutes (ramp 20/s), 80% browsing (search, hotel page, availability, quote, filter options, suggestions, geography) and 20% booking (the same, then a pending booking). Data: the same 2,000 hotels / 10,000 bookings. Server: gunicorn, 4 workers, PostgreSQL, throttles ON (each simulated visitor has its own address via `NUM_PROXIES=1`), request logging ON, in-process cache (no Redis). **One 4-core container ran the server, the database and the load generator together**, so the numbers are a floor, not what a dedicated server gives.

Result: 10,289 requests, **0 failures**, 85.7 requests/s (161 bookings created, all 201).

| Endpoint | Requests | Time in the server, median | **p95 in the server** |
|---|---|---|---|
| Search (20 hotels, dates + city) | 2,195 | 111 ms | **163 ms** |
| Hotel page | 2,165 | 26 ms | 36 ms |
| Availability | 1,976 | 43 ms | 61 ms |
| Quote | 1,949 | 8 ms | 12 ms |
| Create booking | 161 | 28 ms | 36 ms |
| Filter options / suggestions / geography | 862 / 417 / 377 | 16 / 14 / 4 ms | 24 / 21 / 7 ms |

What the client saw: median 1.5 s, **p95 2.1 s**, for every endpoint alike (the cheap ones too). That is queueing, not slow code: 200 users asking every 1-3 s need about 100 requests/s and the box delivers about 86, so requests wait for a free worker. Search is 45% of all server time (2,195 x 111 ms), the rest is small.

What we learned
- No errors, no booking failures, throttles behaved (the earlier runs hit the per-address search limit of 100/min and the pending-bookings cap, as designed).
- The code is not the limit here; the number of workers/cores is. For 200 users at this pace the production server needs more than 4 shared cores (or 8+ workers on dedicated cores).
- Search is the one endpoint worth watching: 6 queries (48 ms in the database) + about 65 ms of Python (serialising 20 hotels). A 30-60 s cache of search results would roughly halve the load, but a listing could then show a slightly old price or availability (the booking itself always re-checks), so it is **not** done; the owner decided on 2026-10-18 to measure first. Revisit if a dedicated server shows search p95 above the target.
- Found while testing: a USD/EUR-priced hotel cannot be booked while the database has no CBU rate (503 `exchange_rate_unavailable`, by design, R6). The scratch database needs a rate; `make_sessions.py` adds one.

Frontend bundle (from `npm run build`, gzip): app 85 KB + React 59 KB on the first load; map 44 KB loads only on pages with a map; every page is its own lazy chunk (largest: admin 22 KB, owner 19 KB, search 15 KB). Brand images are WebP (94 KB largest). Nothing to cut.

Not done in R14, by decision: Redis cache (see above) and image thumbnails (owners cannot upload photos yet; do it together with that feature).
