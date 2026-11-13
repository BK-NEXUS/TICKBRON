"""
TICKBRON ushın Celery sazlaması
"""

import os

try:
    from celery import Celery

    # 'celery' baǵdarlaması ushın ádettegi Django sazlama modulin belgilew.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

    app = Celery('tickbron')

    # Sazlamanı Django sazlamalarınan júklew
    app.config_from_object('django.conf:settings', namespace='CELERY')

    # Barlıq ornatılǵan app larda task lardı avtomat tabıw
    app.autodiscover_tasks()
except ImportError:
    # Celery ornatılmaǵan (mısalı eń kishi ortalıq): worker app sız isle
    app = None
