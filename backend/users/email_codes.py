"""
Mánzilge e-mail penen jiberiletuǵın altı sanlı kodlar, klaviatura artındaǵı adamda poshta qutısı barlıǵın kórsetiw ushın:
dizimnen ótkende (akkaunt
kod terilgennen keyin ǵana jaratıladı) hám mehmann yamasa mehmanxana iyesiniń hár kirisiwinde (paroldan keyin,
session baslanbastan aldın). Reje: .ai/PLAN_EMAIL_CODES.md.

- Kod tosınarlıq (`secrets`), 10 minut jasaydı, bir márte isleydi hám keshte tek kiltli hash retinde saqlanadı.
- 5 qáte urınıw onı jaǵıp jiberedi. Jańa kod bir minuttan keyin soralıwı múmkin, bir mánzilge saatına eń kóbi 5 xat.
- Kútip turǵan dizimnen ótiw terilgen maǵlıwmattı, aldınan hash langan paroldi usı 10 minut keshte saqlaydı.
- E-mail soraw ishinde jiberiledi, task náwbeti arqalı emes, sol sebepli kod hesh qashan náwbet log larınan ótpeydi.
"""
import hashlib
import hmac
import secrets
import time

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import salted_hmac

CODE_LENGTH = 6
LIFETIME_SECONDS = 10 * 60
MAX_ATTEMPTS = 5
RESEND_AFTER_SECONDS = 60
MAX_SENDS_PER_HOUR = 5
HOUR_SECONDS = 60 * 60
EMAIL_SUBJECT = 'TICKBRON: tasdiqlash kodi / код подтверждения / verification code'
LOGIN_PENDING_KEY = 'email_code_login'


class SendFailed(Exception):
    """E-mail server xattı qabıllamadı."""


class TooSoon(Exception):
    """Jańa kod júdá erte yamasa júdá kóp soraldı; `retry_after` sekundlarda."""

    def __init__(self, retry_after):
        super().__init__(retry_after)
        self.retry_after = retry_after


def _now():
    return time.time()


def new_code():
    return f'{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}'


def looks_like_a_code(value):
    return isinstance(value, str) and len(value) == CODE_LENGTH and value.isascii() and value.isdigit()


def hint(email):
    """"o***@gmail.com": adam óz mánzilin tanıw ushın jeterli."""
    name, _, domain = email.partition('@')
    return f'{name[:1]}***@{domain}'


def _fingerprint(*parts):
    return hashlib.sha256(':'.join(parts).encode('utf-8', 'surrogatepass')).hexdigest()


def entry_key(purpose, ident):
    return f'email_code:{purpose}:{_fingerprint(purpose, ident)}'


def _tries_key(purpose, ident):
    return f'email_code_tries:{purpose}:{_fingerprint(purpose, ident)}'


def _sends_key(purpose, ident):
    return f'email_code_sends:{purpose}:{_fingerprint(purpose, ident)}'


def _digest(purpose, ident, code):
    return salted_hmac('tickbron.email_code', f'{purpose}:{ident}:{code}', algorithm='sha256').hexdigest()


def _count_send(purpose, ident):
    key = _sends_key(purpose, ident)
    cache.add(key, 0, HOUR_SECONDS)
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, HOUR_SECONDS)
        return 1


def _check_may_send(purpose, ident):
    entry = cache.get(entry_key(purpose, ident))
    if entry is not None:
        wait = entry['sent_at'] + RESEND_AFTER_SECONDS - _now()
        if wait > 0:
            raise TooSoon(int(wait) + 1)
    if (cache.get(_sends_key(purpose, ident)) or 0) >= MAX_SENDS_PER_HOUR:
        raise TooSoon(HOUR_SECONDS)


def _send(email, code):
    body = render_to_string('users/email_code_email.txt', {'code': code, 'minutes': LIFETIME_SECONDS // 60})
    try:
        send_mail(EMAIL_SUBJECT, body, None, [email])
    except Exception as error:  # SMTP qátelikleri kóp túrli: hámmesi "jiberilmedi" degendi bildiredi
        raise SendFailed(type(error).__name__) from error


def issue(purpose, ident, email, payload=None, keep_payload_of=None):
    """
    `ident` ushın jańa kod jasaw, onıń hash in saqlaw, `email` ge jiberiw. TooSoon yamasa SendFailed kóteredi; sátsiz
    e-mail
    hesh nárse kútip turmaydı. `keep_payload_of`: `payload` tıń ornına aldınǵı kodtıń (qayta jiberiw) kútip turǵan
    maǵlıwmatın qayta paydalanıw.
    """
    _check_may_send(purpose, ident)
    if keep_payload_of is not None:
        earlier = cache.get(entry_key(purpose, keep_payload_of))
        if earlier is None:
            raise LookupError('nothing waiting')
        payload = earlier['payload']
    code = new_code()
    now = _now()
    cache.set(entry_key(purpose, ident), {
        'digest': _digest(purpose, ident, code), 'sent_at': now, 'expires_at': now + LIFETIME_SECONDS,
        'payload': payload,
    }, LIFETIME_SECONDS)
    cache.delete(_tries_key(purpose, ident))
    try:
        _send(email, code)
    except SendFailed:
        cache.delete(entry_key(purpose, ident))
        raise
    _count_send(purpose, ident)


def waiting(purpose, ident):
    """`ident` ushın kod berilgen hám múddeti ótpegen yamasa tawsılmaǵansha True."""
    entry = cache.get(entry_key(purpose, ident))
    return entry is not None and entry['expires_at'] > _now()


def verify(purpose, ident, code):
    """
    `code` `ident` tiń tiri kodı bolsa kodtıń maǵlıwmatı (joq bolsa {}), bolmasa None. Durıs kod
    paydalanılıp bitedi. Qáte urınıwlar atomic túrde sanaladı; besinshisi kodtı jaǵadı.
    """
    key = entry_key(purpose, ident)
    entry = cache.get(key)
    if entry is None or entry['expires_at'] <= _now() or not looks_like_a_code(code):
        return None
    tries_key = _tries_key(purpose, ident)
    cache.add(tries_key, 0, LIFETIME_SECONDS)
    try:
        tries = cache.incr(tries_key)
    except ValueError:
        tries = 1
        cache.set(tries_key, 1, LIFETIME_SECONDS)
    if tries > MAX_ATTEMPTS:
        cache.delete(key)
        return None
    if not hmac.compare_digest(entry['digest'], _digest(purpose, ident, code)):
        if tries >= MAX_ATTEMPTS:
            cache.delete(key)
        return None
    # Jazbanı haqıyqatında alıp taslaǵan soraw ǵana kodtıń iyesi; birdey durıs kodlı paralel sorawlar jeńiledi
    if not cache.delete(key):
        return None
    cache.delete(tries_key)
    return entry['payload'] or {}


def needs_code_at_login(user):
    """Mehmanlar hám mehmanxana iyeleri: staff ta authenticator ilovası bar (users.two_factor) hám olardan bul hesh qashan
    soralmaydı."""
    return settings.EMAIL_LOGIN_CODE_REQUIRED and not (user.is_staff or user.is_superuser or user.two_factor_enabled)


def remember_login_step(request, user):
    request.session[LOGIN_PENDING_KEY] = {'user': user.pk, 'at': _now()}


def forget_login_step(request):
    request.session.pop(LOGIN_PENDING_KEY, None)


def pending_login_user_id(request):
    pending = request.session.get(LOGIN_PENDING_KEY)
    if not pending or _now() - pending['at'] > LIFETIME_SECONDS:
        return None
    return pending['user']
