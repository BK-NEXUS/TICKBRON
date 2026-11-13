"""
Paydalanıwshı autentifikaciyası hám qáwipsizlik ushın óz validator ları.

Bul modul parol kúshi, e-mail tekseriw hám basqa
qáwipsizlikke baylanıslı tekseriwler ushın óz validator larin óz ishine aladı.
"""
import re
import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

PHONE_NUMBER_ERROR = 'Enter a valid phone number in international format, e.g. +998 90 123 45 67.'

# Adamlar san toparları arasında jazatuǵın bos orınlar, defisler, nuqtalar hám jaqshalar
_PHONE_SEPARATORS = re.compile(r'[\s\-.()]')


def parse_phone_number(value):
    """
    Telefon nomerin E.164 formasında ("+998901234567") qaytarıw, yamasa jaramlı nomer
    bolmasa None.

    Nomer "+" hám mámleket kodınan baslanıwı kerek. San toparları arasındaǵı
    ajıratıwshılarǵa ruxsat, háripler hám basqa belgilerge ruxsat joq.
    """
    compact = _PHONE_SEPARATORS.sub('', str(value or ''))
    if not re.fullmatch(r'\+\d{1,15}', compact):
        return None
    try:
        number = phonenumbers.parse(compact, None)
    except phonenumbers.NumberParseException:
        return None
    if not phonenumbers.is_valid_number(number):
        return None
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.E164)


class StrongPasswordValidator:
    """
    Kúshli parol talapları ushın óz parol validator ı.

    Májbúrleydi:
    - Eń kem uzınlıq 8 belgi
    - Eń keminde bir háripti (qálegen register, qálegen alfavit)
    - Eń keminde bir sandı
    - Eń keminde bir arnawlı belgini (háripti, sandı yamasa bos orındı emes)
    - Ulıwma úlgiler yamasa izbe-izlik joq
    """

    def __init__(self, min_length=8, forbid_sequences=True):
        self.min_length = min_length
        # AUTH_PASSWORD_VALIDATORS ta óshirilgen: hár "abc"/"456" izbe-izligi
        # uzın tosınarlıq parol jumlalardı da biykar etedi, hám uzınlıq + blok dizim kóbirek áhmiyetli
        self.forbid_sequences = forbid_sequences

    def validate(self, password, user=None):
        """
        Parol kúshin tekseriw.
        """
        if len(password) < self.min_length:
            raise ValidationError(
                _("Password must be at least %(min_length)d characters long."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

        if not any(char.isalpha() for char in password):
            raise ValidationError(
                _("Password must contain at least one letter."),
                code='password_no_letter',
            )

        if not any(char.isdigit() for char in password):
            raise ValidationError(
                _("Password must contain at least one digit."),
                code='password_no_digit',
            )

        if not any(not char.isalnum() and not char.isspace() for char in password):
            raise ValidationError(
                _("Password must contain at least one special character."),
                code='password_no_special',
            )

        # Ulıwma úlgilerdi tekseriw
        common_patterns = [
            r'123456', r'qwerty', r'password', r'admin', r'letmein',
            r'welcome', r'monkey', r'football', r'abc123', r'111111'
        ]

        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                raise ValidationError(
                    _("Password contains common patterns and is not secure."),
                    code='password_common_pattern',
                )

        # Izbe-iz belgilerdi tekseriw
        if self.forbid_sequences and self._has_sequential_chars(password):
            raise ValidationError(
                _("Password contains sequential characters and is not secure."),
                code='password_sequential',
            )

    def _has_sequential_chars(self, password):
        """Parolda izbe-iz belgiler barlıǵın tekseriw."""
        password_lower = password.lower()
        for i in range(len(password_lower) - 2):
            if (ord(password_lower[i+1]) == ord(password_lower[i]) + 1 and
                ord(password_lower[i+2]) == ord(password_lower[i]) + 2):
                return True
        return False

    def get_help_text(self):
        """
        Parol talapları ushın járdem tekstin qaytarıw.
        """
        return _(
            "Your password must be at least %(min_length)d characters long, "
            "contain at least one letter, one digit, and one special character. "
            "Avoid common patterns and sequential characters."
        ) % {'min_length': self.min_length}


class EmailFormatValidator:
    """
    Keńeytilgen e-mail format validator ı.

    E-mail formatın Django nıń ádetdegisinen qattıraq qaǵıydalar menen tekseredi.
    """

    def validate(self, email):
        """
        E-mail formatın tekseriw.
        """
        if not email:
            raise ValidationError(_("Email address is required."))

        # Ápiwayı format tekseriwi
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValidationError(_("Invalid email format."))

        # Waqtınsha e-mail domenlerin tekseriw (ápiwayı dizim)
        disposable_domains = [
            'tempmail.com', 'throwaway.com', 'guerrillamail.com',
            'mailinator.com', '10minutemail.com'
        ]

        domain = email.split('@')[1].lower()
        if any(disposable in domain for disposable in disposable_domains):
            raise ValidationError(
                _("Disposable email addresses are not allowed."),
                code='disposable_email',
            )

    def get_help_text(self):
        """
        E-mail talapları ushın járdem tekstin qaytarıw.
        """
        return _("Enter a valid email address. Disposable email addresses are not allowed.")
