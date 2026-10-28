"""
Settings of the web server (gunicorn) in the Docker image. The size comes from the environment (.env):

  WEB_WORKERS  processes, one per CPU core is a good start
  WEB_THREADS  requests each process handles at the same time (the site mostly waits for the database)
  WEB_TIMEOUT  seconds before a stuck request is cut

Every thread holds its own database connection for a minute (CONN_MAX_AGE), so WEB_WORKERS x WEB_THREADS
(plus the Celery worker) must stay well under PostgreSQL's max_connections (100).
"""
import os


def _positive_int(name, default):
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError:
        value = 0
    if value < 1:
        raise ValueError(f'{name} must be a whole number of 1 or more, got {raw!r}')
    return value


bind = '0.0.0.0:8000'
workers = _positive_int('WEB_WORKERS', 3)
threads = _positive_int('WEB_THREADS', 4)
timeout = _positive_int('WEB_TIMEOUT', 30)
accesslog = '-'
