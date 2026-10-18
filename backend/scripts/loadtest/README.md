# Load test (R14)

Locust script for the guest paths: search, filter options, hotel page, availability, quote, and booking creation.
Local development only: it needs the bulk demo data and spoofs `X-Forwarded-For`, so never point it at production.

```bash
# 1. scratch database with volume (DEBUG only)
DB_NAME=tickbron_perf python manage.py migrate
DB_NAME=tickbron_perf python manage.py seed_demo_bulk --hotels 2000 --guests 300 --bookings 10000 --days 90

# 2. 1000 fresh guests and their sessions (writes scripts/loadtest/sessions.json, git-ignored)
DB_NAME=tickbron_perf python scripts/loadtest/make_sessions.py

# 3. server like production: several workers behind one proxy hop, so every simulated visitor has an own address
# (the throttles stay ON: they are per address)
DB_NAME=tickbron_perf NUM_PROXIES=1 gunicorn config.wsgi -w 4 -b 127.0.0.1:8000

# 4. 200 users, 2 minutes, CSV + summary
locust -f scripts/loadtest/locustfile.py --headless -u 200 -r 20 -t 2m --host http://127.0.0.1:8000 --csv /tmp/loadtest
```

Browsing users (weight 8) search, open a hotel, check availability and ask for a quote. Booking users (weight 2) do the same
and then create a pending booking with a session from `sessions.json`. A booking user takes a new guest after every booking. A refusal that is a business rule (400/409/429: too many pending
bookings, no rooms left, throttle) counts as a success of the endpoint and is reported under its own name.
