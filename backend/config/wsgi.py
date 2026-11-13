"""
config proekti ushın WSGI sazlaması.

Ol WSGI shaqırılatuǵın obyektti modul dárejesindegi ``application`` ózgeriwshisi retinde usınadı.

Bul fayl haqqında kóbirek maǵlıwmat ushın qarań:
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
