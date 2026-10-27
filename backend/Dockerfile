# The TICKBRON API: Django behind gunicorn. The same image runs the web server, the Celery worker and beat
# and the migration job (docker-compose.yml picks the command).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# A normal user: a hole in the app must not be root in the container. media/ is where uploaded photos go
# (a volume in docker-compose.yml), logs/ is where Django's rotating log files go.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /app/media /app/logs \
    && chown -R app:app /app/media /app/logs
USER app

EXPOSE 8000

# 3 workers suit a small server; set GUNICORN_CMD_ARGS to change anything without rebuilding.
# The proxy in front (Caddy) already limits the size of what reaches the app.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "30", "--access-logfile", "-"]
