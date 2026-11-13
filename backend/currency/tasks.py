from celery import shared_task

from currency import cbu


@shared_task(bind=True, max_retries=3, default_retry_delay=600)
def fetch_exchange_rates(self):
    """
    Búgingi CBU kurslarin alıw (CELERY_BEAT_SCHEDULE kúnine eki ret rejelestirgen).

    Sátsiz alıw sońǵı qabıllanǵan kursı saqlaydı hám 10 minut aralıq penen 3 ke shekem qayta urınıladı.
    """
    results = cbu.fetch_and_store()
    if any(row is None for row in results.values()):
        raise self.retry()
    return {currency: str(row.rate) for currency, row in results.items()}
