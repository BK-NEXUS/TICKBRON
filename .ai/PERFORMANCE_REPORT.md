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
