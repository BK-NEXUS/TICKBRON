from celery import shared_task


@shared_task
def end_expired_promotions():
    """Asia/Tashkent 00:10 de rejelestirilgen (CELERY_BEAT_SCHEDULE): jańa is kúni ushın reklama statuslarin tazalaw."""
    from promotions.service import tidy_statuses

    return tidy_statuses()


@shared_task
def run_ad_renewals():
    """Asia/Tashkent 00:05 te rejelestirilgen, 00:10 tazalawdan aldın: jańalaw sorawların ashıw, múddeti ótken reklamalardı
    alıp taslaw, iyelerge eskertiw."""
    from promotions.renewals import run_daily

    return run_daily()
