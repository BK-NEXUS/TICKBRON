"""
config proekti ushın ASGI sazlaması.

Ol ASGI shaqırılatuǵın obyektti modul dárejesindegi ``application`` ózgeriwshisi retinde usınadı.

Bul fayl haqqında kóbirek maǵlıwmat ushın qarań:
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
