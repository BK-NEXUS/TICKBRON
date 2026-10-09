from celery import shared_task


@shared_task
def end_expired_promotions():
    """Scheduled at 00:10 Asia/Tashkent (CELERY_BEAT_SCHEDULE): tidy promotion statuses for the new business day."""
    from promotions.service import tidy_statuses

    return tidy_statuses()
