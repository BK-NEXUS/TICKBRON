"""
Autentifikaciya endpoint leri ushın rate limit ler.

Bul jerdegi hár limit shaqırıwshı erkin ózgerte almaytuǵın nárse boyınsha kiltlenedi: klient IP si yamasa
kirgen akkaunt.
"""
import os
import sys

from django.conf import settings

from common.throttling import BlockAnonRateThrottle

# Testler islep atırǵanda throttling óshken; limitti tekseretuǵın testler bul flag tı qaytadan False ǵa qoyadı
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')


class IPRateThrottle(BlockAnonRateThrottle):
    """
    Hár shaqırıwshı ushın klient IP si boyınsha kiltlengen throttle.

    DRF tiń AnonRateThrottle ı kirgen paydalanıwshılardı ótkizip jiberedi, sol sebepli waqtınsha
    akkaunt kirisiw hám dizimnen ótiw limitlerin kótergen bolar edi.
    """

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}

    def allow_request(self, request, view):
        # Testler waqtında throttling di óshiriw
        if TESTING:
            return True
        return super().allow_request(request, view)


class LoginRateThrottle(IPRateThrottle):
    """Hár IP ushın kirisiw endpoint i rate throttle i (THROTTLE_LOGIN_RATE, ádetde 10/min)."""
    rate = settings.LOGIN_THROTTLE_RATE
    scope = 'login'


class RegisterRateThrottle(IPRateThrottle):
    """Hár IP ushın dizimnen ótiw endpoint i rate throttle i (THROTTLE_REGISTER_RATE, ádetde 5/min)."""
    rate = settings.REGISTER_THROTTLE_RATE
    scope = 'register'


class PasswordResetRequestThrottle(IPRateThrottle):
    """Bir mánzilden soralatuǵın tiklew e-mail leri: saatına 5."""
    rate = '5/hour'
    scope = 'password_reset_request'


class PasswordResetConfirmThrottle(IPRateThrottle):
    """Bir mánzilden sınap kórilgen tiklew silteme leri: saatına 10."""
    rate = '10/hour'
    scope = 'password_reset_confirm'


class EmailCodeVerifyThrottle(IPRateThrottle):
    """Bir tarmaqtan sınap kórilgen e-mail kodlar: minutına 20 (5 qáte urınıw kodtı tezirek jaǵadı)."""
    rate = '20/min'
    scope = 'email_code_verify'


class EmailCodeSendThrottle(IPRateThrottle):
    """Bir tarmaqtan soralǵan jańa e-mail kodlar: saatına 30 (bir mánzil eń kóbi saatına 5 aladı)."""
    rate = '30/hour'
    scope = 'email_code_send'


class AccountRateThrottle(IPRateThrottle):
    """Kirgen akkaunt boyınsha kiltlengen, klient soraw ishine qoyǵan hesh nárse boyınsha emes."""

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': f'user-{request.user.pk}'}


class PasswordChangeThrottle(AccountRateThrottle):
    """Hár akkaunt ushın parol ózgertiwler (hám qáte házirgi parollar): minutına 5."""
    rate = '5/min'
    scope = 'password_change'


class TwoFactorLoginThrottle(IPRateThrottle):
    """Bir tarmaqtan sınap kórilgen kodlar: minutına 10 (lockout boljawdı tezirek toqtatadı)."""
    rate = '10/min'
    scope = 'two_factor_login'


class TwoFactorSetupThrottle(AccountRateThrottle):
    """Hár akkaunt ushın sazlaw hám tastıyıqlaw shaqırıwları: minutına 10."""
    rate = '10/min'
    scope = 'two_factor_setup'


class TwoFactorResetThrottle(AccountRateThrottle):
    """Super admin óz kodı menen basqa birewdi qayta ornatıw ushın óz-ózin dálillaydı: minutına 5 urınıw."""
    rate = '5/min'
    scope = 'two_factor_reset'
