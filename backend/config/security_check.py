"""
Security Foundations Check for TICKBRON Backend Checkpoint 01

This script verifies that the basic security foundations are in place.
"""
import os
from pathlib import Path

def check_security_foundations():
    """Verify basic security foundations are configured."""
    
    print("TICKBRON Backend Security Foundations Check")
    print("=" * 50)
    
    checks = []
    
    # Check 1: Environment-based configuration
    env_file = Path('.env')
    if not env_file.exists():
        checks.append(("PASS", "Environment file not committed (security best practice)"))
    else:
        checks.append(("WARN", "Environment file exists - ensure it's not committed"))
    
    # Check 2: .env.example exists
    env_example = Path('.env.example')
    if env_example.exists():
        checks.append(("PASS", "Environment template exists for setup"))
    else:
        checks.append(("FAIL", "Missing .env.example template"))
    
    # Check 3: .gitignore includes sensitive files
    gitignore = Path('.gitignore')
    if gitignore.exists():
        gitignore_content = gitignore.read_text()
        if '.env' in gitignore_content:
            checks.append(("PASS", ".env in .gitignore"))
        else:
            checks.append(("FAIL", ".env not in .gitignore"))
        
        if '*.pyc' in gitignore_content or '__pycache__' in gitignore_content:
            checks.append(("PASS", "Python cache files in .gitignore"))
        else:
            checks.append(("WARN", "Python cache files not explicitly in .gitignore"))
    else:
        checks.append(("FAIL", "Missing .gitignore"))
    
    # Check 4: Security settings in Django settings
    settings_file = Path('config/settings.py')
    if settings_file.exists():
        settings_content = settings_file.read_text()
        
        if 'SESSION_COOKIE_HTTPONLY = True' in settings_content:
            checks.append(("PASS", "HTTPOnly cookies enabled"))
        else:
            checks.append(("FAIL", "HTTPOnly cookies not enabled"))
        
        if 'CSRF_COOKIE_HTTPONLY = True' in settings_content:
            checks.append(("PASS", "CSRF HTTPOnly cookies enabled"))
        else:
            checks.append(("FAIL", "CSRF HTTPOnly cookies not enabled"))
        
        if 'SESSION_COOKIE_SAMESITE' in settings_content:
            checks.append(("PASS", "SameSite cookie attribute configured"))
        else:
            checks.append(("FAIL", "SameSite cookie attribute not configured"))
        
        if 'CSRF_TRUSTED_ORIGINS' in settings_content:
            checks.append(("PASS", "CSRF trusted origins configured"))
        else:
            checks.append(("FAIL", "CSRF trusted origins not configured"))
        
        if 'CORS_ALLOWED_ORIGINS' in settings_content:
            checks.append(("PASS", "CORS origins configured"))
        else:
            checks.append(("FAIL", "CORS origins not configured"))
        
        if 'SECRET_KEY' in settings_content and 'os.getenv' in settings_content:
            checks.append(("PASS", "SECRET_KEY uses environment variable"))
        else:
            checks.append(("FAIL", "SECRET_KEY not properly configured"))
    else:
        checks.append(("FAIL", "Settings file not found"))
    
    # Check 5: Django security middleware
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'django.middleware.csrf.CsrfViewMiddleware' in settings_content:
            checks.append(("PASS", "CSRF middleware enabled"))
        else:
            checks.append(("FAIL", "CSRF middleware not enabled"))
        
        if 'django.middleware.security.SecurityMiddleware' in settings_content:
            checks.append(("PASS", "Security middleware enabled"))
        else:
            checks.append(("FAIL", "Security middleware not enabled"))
    
    # Print results
    print("\nSecurity Foundations Status:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    warnings = 0
    
    for status, message in checks:
        print(f"{status} {message}")
        if status == "PASS":
            passed += 1
        elif status == "FAIL":
            failed += 1
        else:
            warnings += 1
    
    print("-" * 50)
    print(f"Passed: {passed}, Failed: {failed}, Warnings: {warnings}")
    
    if failed == 0:
        print("\nPASS: Security foundations check PASSED")
        return True
    else:
        print(f"\nFAIL: Security foundations check FAILED ({failed} issues)")
        return False

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    os.chdir(Path(__file__).parent.parent)
    success = check_security_foundations()
    sys.exit(0 if success else 1)
