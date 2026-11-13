"""
Parol tiklew silteme leri hám olardı alıp júretuǵın e-mail.

Silteme qol qoyılǵan, bir márte paydalanılatuǵın token di (Django nıń PasswordResetTokenGenerator ı) saqlaydı: ol
parol ózgergennen yamasa paydalanıwshı kirgennen keyin, hám PASSWORD_RESET_TIMEOUT tan keyin islewdi toqtatadı.
"""
import hashlib

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from users.models import User

MAX_REQUESTS_PER_ADDRESS_PER_DAY = 5
ONE_DAY_SECONDS = 24 * 3600
EMAIL_SUBJECT = 'TICKBRON: parolni tiklash / сброс пароля / password reset'


def can_reset_password(user):
    """Tek paroli bar aktiv akkauntlar; tek telefonlı akkaunttı tiklewge hesh nárse joq."""
    return user.is_active and user.has_usable_password()


def daily_request_allowed(email):
    """Bul sorawdı mánzildiń kúnlik shegine sanaw; tawsılsa False."""
    key = 'password_reset_requests:' + hashlib.sha256(email.lower().encode()).hexdigest()
    cache.add(key, 0, ONE_DAY_SECONDS)
    return cache.incr(key) <= MAX_REQUESTS_PER_ADDRESS_PER_DAY


def build_reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f'{settings.FRONTEND_URL.rstrip("/")}/reset-password?uid={uid}&token={token}'


def find_user_for_reset(uid, token):
    """Jaramlı silteme tiyisli paydalanıwshı, yamasa None (belgisiz id, qáte token, múddeti ótken, paydalanılǵan,
    óshirilgen)."""
    try:
        user = User.objects.get(pk=urlsafe_base64_decode(uid).decode())
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None
    if not can_reset_password(user) or not default_token_generator.check_token(user, token):
        return None
    return user


def send_reset_email(user):
    body = render_to_string('users/password_reset_email.txt', {'link': build_reset_link(user)})
    send_mail(EMAIL_SUBJECT, body, None, [user.email])
