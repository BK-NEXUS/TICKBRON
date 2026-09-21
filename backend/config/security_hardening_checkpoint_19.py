"""
Security review and hardening for Checkpoint 19.

This script performs security checks and provides recommendations
for TICKBRON backend security hardening.
"""
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from permissions.models import Role

User = get_user_model()

def check_security_settings():
    """Check security settings configuration."""
    print("=== Security Settings Review ===")
    
    checks = {
        'DEBUG': settings.DEBUG,
        'SECURE_SSL_REDIRECT': getattr(settings, 'SECURE_SSL_REDIRECT', False),
        'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
        'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
        'SESSION_COOKIE_HTTPONLY': getattr(settings, 'SESSION_COOKIE_HTTPONLY', True),
        'CSRF_COOKIE_HTTPONLY': getattr(settings, 'CSRF_COOKIE_HTTPONLY', True),
        'HSTS_ENABLED': getattr(settings, 'SECURE_SSL_REDIRECT', False),
    }
    
    for setting, value in checks.items():
        status = "[PASS]" if value else "[FAIL]"
        print(f"{status} {setting}: {value}")
    
    print()


def check_middleware_configuration():
    """Check middleware configuration."""
    print("=== Middleware Configuration Review ===")
    
    required_middleware = [
        'django.middleware.security.SecurityMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'common.middleware.SecurityHeadersMiddleware',
        'common.middleware.RequestLoggingMiddleware',
        'common.middleware.PerformanceMonitoringMiddleware',
    ]
    
    for middleware in required_middleware:
        if middleware in settings.MIDDLEWARE:
            print(f"[PASS] {middleware}")
        else:
            print(f"[FAIL] {middleware} - MISSING")
    
    print()


def check_cors_configuration():
    """Check CORS configuration."""
    print("=== CORS Configuration Review ===")
    
    cors_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
    cors_credentials = getattr(settings, 'CORS_ALLOW_CREDENTIALS', False)
    
    print(f"CORS Allowed Origins: {cors_origins}")
    print(f"CORS Allow Credentials: {cors_credentials}")
    
    if cors_origins:
        print("[PASS] CORS origins configured")
    else:
        print("[FAIL] No CORS origins configured")
    
    print()


def check_rate_limiting():
    """Check rate limiting configuration."""
    print("=== Rate Limiting Review ===")
    
    rate_limit_enabled = getattr(settings, 'RATELIMIT_ENABLE', True)
    drf_throttling = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_CLASSES', [])
    drf_rates = settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {})
    
    print(f"Rate Limiting Enabled: {rate_limit_enabled}")
    print(f"DRF Throttling Classes: {drf_throttling}")
    print(f"DRF Throttling Rates: {drf_rates}")
    
    if drf_throttling:
        print("[PASS] DRF rate limiting configured")
    else:
        print("[FAIL] No DRF rate limiting configured")
    
    print()


def check_permission_classes():
    """Check permission classes in DRF."""
    print("=== Permission Classes Review ===")
    
    default_permissions = settings.REST_FRAMEWORK.get('DEFAULT_PERMISSION_CLASSES', [])
    
    print(f"Default Permission Classes: {default_permissions}")
    
    if 'rest_framework.permissions.IsAuthenticated' in default_permissions:
        print("[PASS] Authentication required by default")
    else:
        print("[FAIL] Authentication not required by default")
    
    print()


def check_logging_configuration():
    """Check logging configuration."""
    print("=== Logging Configuration Review ===")
    
    logging_config = getattr(settings, 'LOGGING', {})
    
    if logging_config:
        print("[PASS] Logging configured")
        handlers = logging_config.get('handlers', {})
        print(f"  Handlers: {list(handlers.keys())}")
        
        loggers = logging_config.get('loggers', {})
        print(f"  Loggers: {list(loggers.keys())}")
    else:
        print("[FAIL] No logging configuration")
    
    print()


def check_database_security():
    """Check database security settings."""
    print("=== Database Security Review ===")
    
    db_config = settings.DATABASES.get('default', {})
    
    conn_max_age = db_config.get('CONN_MAX_AGE', 0)
    print(f"Connection Max Age: {conn_max_age}")
    
    if conn_max_age > 0:
        print("[PASS] Persistent connections enabled")
    else:
        print("[FAIL] No persistent connections")
    
    print()


def check_password_security():
    """Check password security settings."""
    print("=== Password Security Review ===")
    
    password_validators = settings.AUTH_PASSWORD_VALIDATORS
    
    print(f"Password Validators: {len(password_validators)}")
    for validator in password_validators:
        print(f"  - {validator['NAME']}")
    
    # Check minimum length
    for validator in password_validators:
        if 'MinimumLengthValidator' in validator['NAME']:
            min_length = validator.get('OPTIONS', {}).get('min_length', 8)
            print(f"  Minimum Password Length: {min_length}")
            if min_length >= 12:
                print("  [PASS] Strong password requirement")
            else:
                print("  [FAIL] Weak password requirement")
    
    print()


def main():
    """Run all security checks."""
    print("\n" + "="*50)
    print("TICKBRON Security Review - Checkpoint 19")
    print("="*50 + "\n")
    
    check_security_settings()
    check_middleware_configuration()
    check_cors_configuration()
    check_rate_limiting()
    check_permission_classes()
    check_logging_configuration()
    check_database_security()
    check_password_security()
    
    print("="*50)
    print("Security Review Complete")
    print("="*50)


if __name__ == '__main__':
    main()
