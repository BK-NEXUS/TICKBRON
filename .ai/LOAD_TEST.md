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

## Photos
Photos hotel owners upload are re-saved at most 1600 px on the longest side (same format and file name) and lose the camera's hidden data (place, time, device), `common/images.py`. A phone photo of several MB becomes a few hundred KB, so pages and the server's `/media/` traffic stay light. Photos uploaded before this change keep their size.
