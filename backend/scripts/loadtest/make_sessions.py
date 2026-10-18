"""
Writes sessions.json: logged-in sessions of fresh load-test guests (DEBUG only; used by locustfile.py)
and adds a USD and EUR exchange rate to the scratch database.

The guests are new accounts without bookings: a guest may hold only a few pending bookings, so booking
users switch to the next session after each booking.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY  # noqa: E402
from django.contrib.sessions.backends.db import SessionStore  # noqa: E402

from django.contrib.auth.hashers import make_password  # noqa: E402

from users.models import User  # noqa: E402

COUNT = 1000
PREFIX = 'loadtest-guest'

if not settings.DEBUG:
    raise SystemExit('Refusing to run without DEBUG=True')

if not User.objects.filter(email__startswith=PREFIX).exists():
    password = make_password('LoadTest#2026')
    User.objects.bulk_create([
        User(email=f'{PREFIX}-{n:04d}@tickbron.demo', full_name=f'Load guest {n}', password=password,
             phone_number=f'+9987{n:06d}', is_active=True)
        for n in range(1, COUNT + 1)], batch_size=500)

# Hotels priced in USD need a CBU rate to take a booking (R6); the scratch database has none
from common.dates import business_today  # noqa: E402
from currency.models import ExchangeRate  # noqa: E402

for code, rate in (('USD', '12700.00'), ('EUR', '14000.00')):
    ExchangeRate.objects.get_or_create(currency=code, rate_date=business_today(), source='cbu.uz', status='accepted',
                                       defaults={'rate': rate})

sessions = []
for user in User.objects.filter(email__startswith=PREFIX).order_by('id')[:COUNT]:
    store = SessionStore()
    store[SESSION_KEY] = str(user.pk)
    store[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    store[HASH_SESSION_KEY] = user.get_session_auth_hash()
    store.create()
    sessions.append(store.session_key)

out = Path(__file__).with_name('sessions.json')
out.write_text(json.dumps(sessions))
print(f'{len(sessions)} sessions written to {out}')
