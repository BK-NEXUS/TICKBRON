"""
Database Security Check for TICKBRON Backend Checkpoint 02

This script verifies database infrastructure security foundations.
"""
import os
from pathlib import Path

def check_database_security():
    """Verify database security configurations."""
    
    print("TICKBRON Backend Database Security Check")
    print("=" * 50)
    
    checks = []
    
    # Check 1: Database configuration uses environment variables
    settings_file = Path('config/settings.py')
    if settings_file.exists():
        settings_content = settings_file.read_text()
        
        if 'os.getenv' in settings_content and 'DB_' in settings_content:
            checks.append(("PASS", "Database configuration uses environment variables"))
        else:
            checks.append(("FAIL", "Database configuration does not use environment variables"))
        
        # Check for hardcoded credentials
        if 'postgres' in settings_content.lower() and 'password' in settings_content.lower():
            # Check if it's in comments or documentation vs actual code
            lines_with_password = [line for line in settings_content.split('\n') 
                                 if 'password' in line.lower() and not line.strip().startswith('#')]
            if lines_with_password:
                checks.append(("WARN", "Potential hardcoded database credentials found"))
            else:
                checks.append(("PASS", "No hardcoded database credentials in settings"))
        else:
            checks.append(("PASS", "No hardcoded database credentials detected"))
    
    # Check 2: Test database configuration
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'test' in settings_content and 'sqlite3' in settings_content and ':memory:' in settings_content:
            checks.append(("PASS", "Test database uses in-memory SQLite"))
        else:
            checks.append(("WARN", "Test database configuration may not be optimal"))
    
    # Check 3: Database connection settings
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'connect_timeout' in settings_content:
            checks.append(("PASS", "Database connection timeout configured"))
        else:
            checks.append(("WARN", "Database connection timeout not configured"))
    
    # Check 4: Migration files are properly structured
    migrations_dir = Path('core/migrations')
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob('*.py'))
        if migration_files:
            checks.append(("PASS", f"Migration files present ({len(migration_files)} files)"))
            
            # Check for any suspicious patterns in migrations
            suspicious_patterns = ['password', 'secret', 'token', 'key']
            for migration_file in migration_files:
                migration_content = migration_file.read_text()
                for pattern in suspicious_patterns:
                    if pattern in migration_content.lower():
                        # Check if it's in comments or actual data
                        if not migration_content.split(pattern)[0].strip().endswith('#'):
                            checks.append(("WARN", f"Potential sensitive data in {migration_file.name}"))
                            break
        else:
            checks.append(("WARN", "No migration files found"))
    
    # Check 5: Model field security
    models_file = Path('core/models.py')
    if models_file.exists():
        models_content = models_file.read_text()
        
        # Check for sensitive field handling
        if 'JSONField' in models_content:
            checks.append(("INFO", "JSONField usage detected - ensure sensitive data is not stored"))
        
        # Check for proper indexing
        if 'db_index=True' in models_content:
            checks.append(("PASS", "Database indexes configured for performance"))
    
    # Check 6: Database health check configuration
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'DATABASE_HEALTH_CHECK' in settings_content:
            checks.append(("PASS", "Database health check configuration present"))
        else:
            checks.append(("INFO", "Database health check configuration not found (optional)"))
    
    # Print results
    print("\nDatabase Security Status:")
    print("-" * 50)
    
    passed = 0
    failed = 0
    warnings = 0
    info = 0
    
    for status, message in checks:
        print(f"{status} {message}")
        if status == "PASS":
            passed += 1
        elif status == "FAIL":
            failed += 1
        elif status == "WARN":
            warnings += 1
        else:
            info += 1
    
    print("-" * 50)
    print(f"Passed: {passed}, Failed: {failed}, Warnings: {warnings}, Info: {info}")
    
    if failed == 0:
        print("\nPASS: Database security check PASSED")
        return True
    else:
        print(f"\nFAIL: Database security check FAILED ({failed} issues)")
        return False

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    os.chdir(Path(__file__).parent.parent)
    success = check_database_security()
    sys.exit(0 if success else 1)
