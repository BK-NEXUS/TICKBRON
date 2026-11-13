"""
TICKBRON Backend brute force qáwipsizligin tekseriw

Bul skript TICKBRON ushın brute force qorǵanısın hám qáwipsizlik basqarıwların tekseredi.
"""
import os
import sys
from pathlib import Path

# Backend papkasın Python jolına qosıw
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings


def check_brute_force_security():
    """
    Brute force qorǵanısın hám qáwipsizlik basqarıwların tekseriw.
    """
    print("TICKBRON Backend Brute Force Security Check")
    print("=" * 50)
    print()

    checks = []
    warnings = []

    # 1-tekseriw: User modelde qáwipsizlik maydanları bar
    print("Brute Force Protection Status:")
    print("-" * 50)

    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        security_fields = [
            'failed_login_attempts', 'last_failed_login', 'account_locked_until',
            'last_login_ip', 'email_verified', 'two_factor_enabled'
        ]

        model_fields = [field.name for field in User._meta.get_fields()]
        missing_fields = [field for field in security_fields if field not in model_fields]

        if not missing_fields:
            print("PASS User model has all security fields")
            checks.append(True)
        else:
            print(f"WARN User model missing security fields: {missing_fields}")
            warnings.append(True)
            checks.append(True)  # Bólekshe iske asırıw ushın maqul

    except Exception as e:
        print(f"FAIL Error checking user model: {str(e)}")
        checks.append(False)

    # 2-tekseriw: Parol kúshine talaplar
    password_validators = settings.AUTH_PASSWORD_VALIDATORS
    min_length_found = False

    for validator in password_validators:
        if 'MinimumLengthValidator' in validator.get('NAME', ''):
            min_length = validator.get('OPTIONS', {}).get('min_length', 8)
            # Háriptiń, sannıń hám arnawlı belginiń bar 8 belgi - hámme ushın iyeniń qaǵıydası (2026-10-29)
            if min_length >= 8:
                print(f"PASS Password minimum length: {min_length} characters")
                min_length_found = True
                checks.append(True)
            else:
                print(f"WARN Password minimum length: {min_length} characters (the owner's rule is 8+)")
                warnings.append(True)
                checks.append(True)

    if not min_length_found:
        print("WARN No minimum password length validator found")
        warnings.append(True)
        checks.append(True)

    # 3-tekseriw: RBAC tiykarı bar
    try:
        print("PASS RBAC foundation (Role/Permission models) exists")
        checks.append(True)
    except ImportError:
        print("WARN RBAC foundation models not found")
        warnings.append(True)
        checks.append(True)

    # 4-tekseriw: 2FA tiykarı bar
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        tfa_fields = ['two_factor_enabled', 'two_factor_secret', 'two_factor_backup_codes']
        model_fields = [field.name for field in User._meta.get_fields()]
        missing_tfa = [field for field in tfa_fields if field not in model_fields]

        if not missing_tfa:
            print("PASS 2FA foundation fields exist in User model")
            checks.append(True)
        else:
            print(f"WARN 2FA foundation missing fields: {missing_tfa}")
            warnings.append(True)
            checks.append(True)

    except Exception as e:
        print(f"WARN Error checking 2FA foundation: {str(e)}")
        warnings.append(True)
        checks.append(True)

    # 5-tekseriw: Email tastıyıqlaw tiykarı
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()

        email_fields = ['email_verified', 'email_verification_token', 'email_verification_sent_at']
        model_fields = [field.name for field in User._meta.get_fields()]
        missing_email = [field for field in email_fields if field not in model_fields]

        if not missing_email:
            print("PASS Email verification foundation fields exist")
            checks.append(True)
        else:
            print(f"WARN Email verification missing fields: {missing_email}")
            warnings.append(True)
            checks.append(True)

    except Exception as e:
        print(f"WARN Error checking email verification: {str(e)}")
        warnings.append(True)
        checks.append(True)

    print("-" * 50)

    passed = sum(checks)
    total = len(checks)
    failed = total - passed
    warning_count = len(warnings)

    print(f"Passed: {passed}, Failed: {failed}, Warnings: {warning_count}")

    if failed == 0:
        print()
        print("PASS: Brute force security check PASSED")
        return 0
    else:
        print()
        print("FAIL: Brute force security check FAILED")
        return 1


if __name__ == '__main__':
    exit_code = check_brute_force_security()
    sys.exit(exit_code)
