"""
Docker image degi web serverdiń (gunicorn) sazlamaları. Ólshem environment ten (.env) keledi:

  WEB_WORKERS  process ler, hár CPU yadrosına bir jaqsı baslama
  WEB_THREADS  hár process bir waqıtta islewge alatuǵın sorawlar (sayt kóbinese database di kútedi)
  WEB_TIMEOUT  qatıp qalǵan sorawdı úziwden aldınǵı sekundlar
  WEB_MAX_REQUESTS  process jańasına almastırılatuǵın sorawlar sanı; 0 (ádetde) hesh qashan almastırmaydı. Jaddı
               90 000 sorawda turaqlı qaldı, hám hár almastırıw sol process ashıq qaldırǵan ulanıwlardı qaytadan basladı
  WEB_KEEPALIVE  proxy den bos ulanıw ashıq saqlanatuǵın sekundlar; ol proxy diń óz bos
               waqtınan uzın bolıwı kerek (Caddy upstream ulanıwların 2 minut saqlaydı), bolmasa proxy app jańa ǵana jawıp
taslaǵan ulanıwdı qayta paydalanadı

Hár thread database ulanıwın bir minut ustaydı (CONN_MAX_AGE), sol sebepli WEB_WORKERS x WEB_THREADS
(hám Celery worker) PostgreSQL diń max_connections (100) tan jaqsı tómen qalıwı kerek.
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
keepalive = _positive_int('WEB_KEEPALIVE', 125)
try:
    max_requests = int(os.getenv('WEB_MAX_REQUESTS', '0'))
except ValueError:
    max_requests = -1
if max_requests < 0:
    raise ValueError(f"WEB_MAX_REQUESTS must be 0 or a whole number above it, got {os.getenv('WEB_MAX_REQUESTS')!r}")
max_requests_jitter = max_requests // 10  # sonda process lerdiń hámmesi bir waqıtta almastırılmaydı
# Konteynerde process ler tiri ekenin aytıw ushın paydalanatuǵın fayllar jaddıda turıwı kerek: sekin disk serverdi qatırıp
# qoyadı
worker_tmp_dir = '/dev/shm'
accesslog = '-'
