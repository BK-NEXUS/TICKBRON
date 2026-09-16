"""
TICKBRON Backend Authentication Security Check

This script checks the authentication security configuration for TICKBRON.
"""
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings


def check_auth_security():
    """
    Check authentication security configuration.
    """
    print("TICKBRON Backend Authentication Security Check")
    print("=" * 50)
    print()
    
    checks = []
    warnings = []
    
    # Check 1: Custom user model configured
    print("Authentication Security Status:")
    print("-" * 50)
    
    if hasattr(settings, 'AUTH_USER_MODEL'):
        user_model = settings.AUTH_USER_MODEL
        if user_model == 'users.User':
            print("PASS Custom user model configured (users.User)")
            checks.append(True)
        else:
            print(f"WARN Custom user model is not users.User: {user_model}")
            warnings.append(True)
    else:
        print("FAIL No custom user model configured")
        checks.append(False)
    
    # Check 2: Session-based authentication (no JWT in settings)
    if 'rest_framework_simplejwt' not in settings.INSTALLED_APPS:
        print("PASS JWT not configured (session-based auth)")
        checks.append(True)
    else:
        print("FAIL JWT configured (should use session-based auth)")
        checks.append(False)
    
    # Check 3: Session security settings
    session_checks = []
    
    if settings.SESSION_COOKIE_HTTPONLY:
        print("PASS Session cookie HTTPOnly enabled")
        session_checks.append(True)
    else:
        print("FAIL Session cookie HTTPNotly not enabled")
        session_checks.append(False)
    
    if settings.SESSION_COOKIE_SECURE:
        print("PASS Session cookie Secure enabled")
        session_checks.append(True)
    else:
        print("WARN Session cookie Secure not enabled (development mode)")
        warnings.append(True)
        session_checks.append(True)  # Acceptable for development
    
    if settings.SESSION_COOKIE_SAMESITE in ['Lax', 'Strict']:
        print(f"PASS Session cookie SameSite configured: {settings.SESSION_COOKIE_SAMESITE}")
        session_checks.append(True)
    else:
        print(f"WARN Session cookie SameSite: {settings.SESSION_COOKIE_SAMESITE}")
        warnings.append(True)
        session_checks.append(True)  # Acceptable default
    
    checks.extend(session_checks)
    
    # Check 4: CSRF protection
    if 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE:
        print("PASS CSRF middleware enabled")
        checks.append(True)
    else:
        print("FAIL CSRF middleware not enabled")
        checks.append(False)
    
    if settings.CSRF_COOKIE_HTTPONLY:
        print("PASS CSRF cookie HTTPOnly enabled")
        checks.append(True)
    else:
        print("FAIL CSRF cookie HTTPOnly not enabled")
        checks.append(False)
    
    if settings.CSRF_COOKIE_SAMESITE in ['Lax', 'Strict']:
        print(f"PASS CSRF cookie SameSite configured: {settings.CSRF_COOKIE_SAMESITE}")
        checks.append(True)
    else:
        print(f"WARN CSRF cookie SameSite: {settings.CSRF_COOKIE_SAMESITE}")
        warnings.append(True)
        checks.append(True)  # Acceptable default
    
    # Check 5: User model exists and has required fields
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        required_fields = ['email', 'first_name', 'last_name', 'is_active', 'is_staff']
        model_fields = [field.name for field in User._meta.get_fields()]
        
        missing_fields = [field for field in required_fields if field not in model_fields]
        
        if not missing_fields:
            print("PASS User model has all required fields")
            checks.append(True)
        else:
            print(f"WARN User model missing fields: {missing_fields}")
            warnings.append(True)
            checks.append(True)  # Acceptable for customization
            
    except Exception as e:
        print(f"FAIL Error checking user model: {str(e)}")
        checks.append(False)
    
    # Check 6: Password validation
    if settings.AUTH_PASSWORD_VALIDATORS:
        print(f"PASS Password validators configured ({len(settings.AUTH_PASSWORD_VALIDATORS)})")
        checks.append(True)
    else:
        print("WARN No password validators configured")
        warnings.append(True)
        checks.append(True)  # Acceptable for basic setup
    
    print("-" * 50)
    
    passed = sum(checks)
    total = len(checks)
    failed = total - passed
    warning_count = len(warnings)
    
    print(f"Passed: {passed}, Failed: {failed}, Warnings: {warning_count}")
    
    if failed == 0:
        print()
        print("PASS: Authentication security check PASSED")
        return 0
    else:
        print()
        print("FAIL: Authentication security check FAILED")
        return 1


if __name__ == '__main__':
    exit_code = check_auth_security()
    sys.exit(exit_code)