from celery import shared_task

from currency import cbu


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def fetch_exchange_rates(self):
    """
    Fetch today's CBU rates (scheduled by CELERY_BEAT_SCHEDULE twice a day).

    A failed fetch keeps the last accepted rate and is retried up to 3 times, 10 minutes apart.
    """
    results = cbu.fetch_and_store()
    if any(row is None for row in results.values()):
        raise self.retry()
    return {currency: str(row.rate) for currency, row in results.items()}
