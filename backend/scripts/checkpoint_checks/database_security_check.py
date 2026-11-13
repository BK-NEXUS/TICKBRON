"""
TICKBRON Backend 02-checkpoint ushın database qáwipsizligin tekseriw

Bul skript database infrastrukturasınıń qáwipsizlik tiykarların tastıyıqlaydı.
"""
import os
from pathlib import Path

def check_database_security():
    """Database qáwipsizligi sazlamaların tastıyıqlaw."""

    print("TICKBRON Backend Database Security Check")
    print("=" * 50)

    checks = []

    # 1-tekseriw: Database sazlaması environment variable lardı paydalanadı
    settings_file = Path('config/settings.py')
    if settings_file.exists():
        settings_content = settings_file.read_text()

        if 'os.getenv' in settings_content and 'DB_' in settings_content:
            checks.append(("PASS", "Database configuration uses environment variables"))
        else:
            checks.append(("FAIL", "Database configuration does not use environment variables"))

        # Kodqa jazılǵan credential lerdi tekseriw
        if 'postgres' in settings_content.lower() and 'password' in settings_content.lower():
            # Bul comment lerde yamasa hújjetlerde me, yamasa haqıyqıy kodta ma, sonı tekseriw
            lines_with_password = [line for line in settings_content.split('\n')
                                 if 'password' in line.lower() and not line.strip().startswith('#')]
            if lines_with_password:
                checks.append(("WARN", "Potential hardcoded database credentials found"))
            else:
                checks.append(("PASS", "No hardcoded database credentials in settings"))
        else:
            checks.append(("PASS", "No hardcoded database credentials detected"))

    # 2-tekseriw: Test database sazlaması
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'test' in settings_content and 'sqlite3' in settings_content and ':memory:' in settings_content:
            checks.append(("PASS", "Test database uses in-memory SQLite"))
        else:
            checks.append(("WARN", "Test database configuration may not be optimal"))

    # 3-tekseriw: Database baylanıs sazlamaları
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'connect_timeout' in settings_content:
            checks.append(("PASS", "Database connection timeout configured"))
        else:
            checks.append(("WARN", "Database connection timeout not configured"))

    # 4-tekseriw: Migration fayllar durıs dúzilgen
    migrations_dir = Path('core/migrations')
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob('*.py'))
        if migration_files:
            checks.append(("PASS", f"Migration files present ({len(migration_files)} files)"))

            # Migration lerde gúmanlı úlgilerdi tekseriw
            suspicious_patterns = ['password', 'secret', 'token', 'key']
            for migration_file in migration_files:
                migration_content = migration_file.read_text()
                for pattern in suspicious_patterns:
                    if pattern in migration_content.lower():
                        # Bul comment lerde me, yamasa haqıyqıy maǵlıwmatta ma, sonı tekseriw
                        if not migration_content.split(pattern)[0].strip().endswith('#'):
                            checks.append(("WARN", f"Potential sensitive data in {migration_file.name}"))
                            break
        else:
            checks.append(("WARN", "No migration files found"))

    # 5-tekseriw: Model maydanlarınıń qáwipsizligi
    models_file = Path('core/models.py')
    if models_file.exists():
        models_content = models_file.read_text()

        # Sezgir maydanlardıń islenisin tekseriw
        if 'JSONField' in models_content:
            checks.append(("INFO", "JSONField usage detected - ensure sensitive data is not stored"))

        # Durıs indekslewdi tekseriw
        if 'db_index=True' in models_content:
            checks.append(("PASS", "Database indexes configured for performance"))

    # 6-tekseriw: Database health check sazlaması
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'DATABASE_HEALTH_CHECK' in settings_content:
            checks.append(("PASS", "Database health check configuration present"))
        else:
            checks.append(("INFO", "Database health check configuration not found (optional)"))

    # Nátiyjelerdi shıǵarıw
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
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    os.chdir(Path(__file__).parent.parent.parent)
    success = check_database_security()
    sys.exit(0 if success else 1)
