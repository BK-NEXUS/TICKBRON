# Sizing the web server and testing the load

## What to set in `.env` (Docker setup)
| Setting | Default | Meaning |
|---|---|---|
| `WEB_WORKERS` | 3 | processes; about one per CPU core (at least 2) |
| `WEB_THREADS` | 4 | requests each process handles at the same time (the site mostly waits for the database) |
| `WEB_TIMEOUT` | 30 | seconds before a stuck request is cut |
| `WEB_KEEPALIVE` | 125 | seconds an idle connection from Caddy stays open; keep it above Caddy's 2 minutes |

The numbers are read by `backend/gunicorn.conf.py` (a bad value stops the start with a clear message). After a change: `docker compose up -d web`.

Every thread holds a database connection for a minute (`CONN_MAX_AGE`), so `WEB_WORKERS x WEB_THREADS` plus the Celery worker must stay well under PostgreSQL's `max_connections` (100). 4 x 4 = 16 is far below; do not go above about 60 without raising it.

## What was measured (2026-10-28)
Locust, 200 users for 90 seconds, 2000 hotels and 10,000 bookings (`seed_demo_bulk`), browsing 80% and booking 20% (`backend/scripts/loadtest/`). One machine with 4 shared cores ran the server **and** the load generator, with DEBUG on, so the absolute numbers are low; the comparison between rows is what counts.

| Server | Requests/s | Failures | Median | p95 |
|---|---|---|---|---|
| 3 workers, one request each (the old setting) | 36 | 0 | 4.0 s | 7.5 s |
| 3 workers x 4 threads | 47 | 0 | 2.2 s | 7.2 s |
| 4 workers x 4 threads | 56 | 0 | 2.7 s | 4.0 s |

- Threads give about **30% more** requests per second on the same machine, 4 x 4 about **55% more**.
- Without a longer keep-alive the first threaded runs lost 30-33 requests of about 4,500 ("connection reset"): gunicorn closed idle connections after 2 s while the client reused them. `WEB_KEEPALIVE=125` removed all of them (0 failures). Caddy reuses upstream connections the same way, so this matters in production.
- 200 users asking every 1-3 s need about 100 requests/s; this machine gave 36-56, so the times above are queueing, not slow code (server-side p95 of search was 163 ms in the earlier R14 run, `.ai/PERFORMANCE_REPORT.md`).

## What this means for the launch
- Roughly 2-3 times the throughput of the first setup is possible with the same code by giving the server more cores: plan **at least 4 dedicated cores** for the web container and set `WEB_WORKERS` to the number of cores.
- A "3000 people on the site" moment is mostly people reading a page: it means a few hundred requests a second at most. Run this test on the real server before the advertisement and size from the numbers (`requests/s` at 0 failures and a p95 you accept).
- Not cached on purpose (R14): the search results carry the paid advertisements and count their views; a cached answer would count them wrongly.

## How to run the test
```bash
# on the server, against the real stack (the throttles are per address: the script sends a different X-Forwarded-For per user,
# which only works while NUM_PROXIES=1 and Caddy is the proxy; never run it against production with real customers on it)
cd backend
DB_NAME=tickbron_perf python manage.py migrate
DB_NAME=tickbron_perf python manage.py seed_demo_bulk --hotels 2000 --guests 300 --bookings 10000 --days 90
DB_NAME=tickbron_perf python scripts/loadtest/make_sessions.py
DB_NAME=tickbron_perf NUM_PROXIES=1 WEB_WORKERS=4 WEB_THREADS=4 gunicorn -c gunicorn.conf.py config.wsgi:application --bind 127.0.0.1:8000
locust -f scripts/loadtest/locustfile.py --headless -u 200 -r 20 -t 90s --host http://127.0.0.1:8000 --csv /tmp/loadtest
```
Use a scratch database (`tickbron_perf`), never the real one. More detail: `backend/scripts/loadtest/README.md`.

## 3000 visitors in 10 minutes (2026-10-31)
What was done to carry it, and the measurements (same 4-core box that also ran the load generator, so a real server does better):
- **Short copies of public answers** (`common/public_cache.py`, `PUBLIC_CACHE_SECONDS`, default 30, 0 = off): hotel page, free rooms (half as long), search results, search filters, suggestions, geography lists. Not copied: price quotes (what a guest pays), the paid banners and their view counter (still counted for every visitor), anything for one account, any error. A price or a free-room count on a list can be up to 30 s old; booking always checks again. A Redis that is down never breaks a page: after one failure the pages stop asking it for 15 s.
- The search card built two serializers per hotel (DRF reads the model each time): now built once; the search page does 30% less work on its own.
- The built files of the site (`/assets/*`, hashed names) are cached by the browser for a year, the photos for a day, `index.html` is revalidated (Caddyfile and nginx example); Redis has a 512 MB cap that only drops expiring keys. (A web process can be replaced after N requests with `WEB_MAX_REQUESTS`, off by default: in the last run it cut 29 connections of 92,000 and slowed the tail, and memory was flat anyway.)
- Test: 3000 simulated visitors, ramp 30/s, each clicks every 40-80 s (a click = search, hotel page, free rooms, price quote; 20% also book), 12 minutes, `LOADTEST_WAIT_MIN=40 LOADTEST_WAIT_MAX=80`, production-like server (DEBUG off, `LOADTEST_ORIGIN` set), 4 workers x 4 threads, 2000 hotels, 10,000 bookings. About 130 requests/s the whole time.

| Run | Requests | Failures | Visitor-side median / p95 | Server-side p50 / p95 / p99 |
|---|---|---|---|---|
| 1, copies on | 94,272 | 0 | 53 ms / 380 ms | not measured |
| 2, copies on | 93,421 | 0 | 65 ms / 1.1 s | 28 / 243 / 394 ms |
| 3, copies on, bookings fixed | 94,931 | 0 real (103 "no rooms left" quotes, an answer, not a failure) | 58 ms / 520 ms | 28 / 234 / 350 ms (1,059 bookings made) |
| Final code, copies on, 12 min (the box was slower than in runs 1-3: load average 8.8) | 91,992 | 0 | 160 ms / 2.6 s | 37 / 307 / 480 ms |
| Copies **off**, same load, 6 min | 30,313 | 0 | **10 s** / 23 s | (queueing) |
| Twice the load (click every 20-40 s), copies on, 6 min | 63,805 | 0 | 5 s / 9 s (queueing, the box is full at about 177 requests/s) | 44 / 305 / 447 ms |

- An earlier run of the final code had 29 failed requests of 92,000 ("connection reset"): the new `WEB_MAX_REQUESTS` replaced web processes while visitors' connections were open. Memory was flat, so it is now off by default and the failures are gone.
- With the copies the box serves the 3000-visitor load with room to spare; without them it tops out at about 84 requests/s and every visitor waits seconds. At double the load nothing failed, pages just waited their turn.
- The visitor-side numbers include the load generator's own CPU use on the same box; the server-side numbers (gunicorn's request time) are the honest ones.
- A login or a sign-up costs about 0.4 s of one CPU core (PBKDF2, Django's own strength). 3000 people signing in within 10 minutes is about 2 cores for those 10 minutes; a normal day is a fraction of that. Do not lower the strength to save CPU.
- Behind a mobile operator many phones share one address and the limits are per address (`THROTTLE_ANON_RATE` 2000/hour, `THROTTLE_SEARCH_RATE` 100/min). If the logs show "429" for ordinary visitors on a busy day, raise them in `.env`.
- **Sizing for the launch:** 4 dedicated cores for the web container (`WEB_WORKERS=4`, `WEB_THREADS=4`), PostgreSQL and Redis on the same or another machine with its own core, Redis (the cache) switched on. For a 5 times bigger crowd add cores to the web container first (about 45 requests/s per core). Run the test again on the real server before the advertisement: `LOADTEST_ORIGIN=https://<an allowed origin>` makes the script behave like an https visitor.

## Photos
Photos hotel owners upload are re-saved at most 1600 px on the longest side (same format and file name) and lose the camera's hidden data (place, time, device), `common/images.py`. A phone photo of several MB becomes a few hundred KB, so pages and the server's `/media/` traffic stay light. Photos uploaded before this change keep their size.
