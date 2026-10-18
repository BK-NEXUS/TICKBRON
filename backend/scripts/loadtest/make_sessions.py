"""Writes sessions.json: one logged-in session per bulk guest (DEBUG only; used by locustfile.py)."""
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

from users.models import User  # noqa: E402

COUNT = 200

if not settings.DEBUG:
    raise SystemExit('Refusing to run without DEBUG=True')

sessions = []
for user in User.objects.filter(email__startswith='bulk-guest-').order_by('id')[:COUNT]:
    store = SessionStore()
    store[SESSION_KEY] = str(user.pk)
    store[BACKEND_SESSION_KEY] = settings.AUTHENTICATION_BACKENDS[0]
    store[HASH_SESSION_KEY] = user.get_session_auth_hash()
    store.create()
    sessions.append(store.session_key)

out = Path(__file__).with_name('sessions.json')
out.write_text(json.dumps(sessions))
print(f'{len(sessions)} sessions written to {out}')
