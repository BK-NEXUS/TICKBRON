"""Session baslaytuǵın ashıq endpoint ler ushın CSRF tekseriwi."""
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import PermissionDenied


class _CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # HttpResponse emes, sebepti qaytarıw, DRF tiń óz SessionAuthentication ı sıyaqlı
        return reason


def enforce_csrf(request):
    """
    Soraw jaramlı CSRF token alıp júrmese 403 kóteriw.

    DRF CSRF di tek session paydalanıwshısı bar sorawda tekseredi, sol sebepli anonim kirisiw,
    dizimnen ótiw yamasa OTP shaqırıwı onı ótkizip jiberdi: basqa saytıń beti ziyanlı betti
    hújimshiniń akkauntına kirgize aladı (login CSRF). SPA hár qáwipsiz emes shaqırıwda X-CSRFToken di ózi jiberedi.
    """
    check = _CSRFCheck(lambda request: None)
    check.process_request(request)
    reason = check.process_view(request, None, (), {})
    if reason:
        raise PermissionDenied(f'CSRF Failed: {reason}')
