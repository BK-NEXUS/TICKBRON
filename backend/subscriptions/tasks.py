from celery import shared_task


@shared_task
def run_daily_fees():
    """Scheduled at 06:00 Asia/Tashkent (CELERY_BEAT_SCHEDULE): start free periods, create the month's fees, send reminders."""
    from subscriptions.services import run_daily

    return run_daily()
