from celery import shared_task


@shared_task
def end_expired_promotions():
    """Scheduled at 00:10 Asia/Tashkent (CELERY_BEAT_SCHEDULE): tidy promotion statuses for the new business day."""
    from promotions.service import tidy_statuses

    return tidy_statuses()


@shared_task
def run_ad_renewals():
    """Scheduled at 00:05 Asia/Tashkent, before the 00:10 tidy: open the renewal questions, remove overdue ads, remind owners."""
    from promotions.renewals import run_daily

    return run_daily()
