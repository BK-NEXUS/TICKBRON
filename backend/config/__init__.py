# Bul app tıń Django baslanǵanda hárdayım import etiliwin támiyinleydi,
# sonda shared_task usı app tı paydalanadı.
from .celery import app as celery_app

__all__ = ('celery_app',)
