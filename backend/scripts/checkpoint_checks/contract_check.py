"""
TICKBRON Backend 01-checkpoint ushın API shártnama izbe-izligin tekseriw

Bul skript tiykardıń API shártnamasına say ekenin tastıyıqlaydı.
"""
import os
from pathlib import Path

def check_contract_consistency():
    """API shártnama izbe-izligin tiykar sazlawı menen tastıyıqlaw."""

    print("TICKBRON Backend API Contract Consistency Check")
    print("=" * 50)

    checks = []

    # 1-tekseriw: API shártnama faylı bar
    contract_file = Path('../.ai/API_CONTRACT.md')
    if contract_file.exists():
        checks.append(("PASS", "API contract file exists"))
        contract_content = contract_file.read_text()
    else:
        checks.append(("FAIL", "API contract file not found"))
        contract_content = ""

    # 2-tekseriw: Versiya prefiksi shártnamada anıqlanǵan
    if contract_content:
        if '/api/v1/' in contract_content:
            checks.append(("PASS", "API version prefix /api/v1/ defined in contract"))
        else:
            checks.append(("FAIL", "API version prefix not defined in contract"))

    # 3-tekseriw: Tiykarǵı endpoint ler shártnamada kórsetilgen
    if contract_content:
        required_endpoints = [
            'auth/register',
            'auth/login',
            'auth/refresh',
            'properties/search',
            'bookings'
        ]
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in contract_content:
                missing_endpoints.append(endpoint)

        if not missing_endpoints:
            checks.append(("PASS", "Core endpoints listed in contract"))
        else:
            checks.append(("WARN", f"Some core endpoints missing from contract: {missing_endpoints}"))

    # 4-tekseriw: Django REST Framework sazlanǵan
    settings_file = Path('config/settings.py')
    if settings_file.exists():
        settings_content = settings_file.read_text()
        if 'rest_framework' in settings_content:
            checks.append(("PASS", "Django REST Framework configured"))
        else:
            checks.append(("FAIL", "Django REST Framework not configured"))

        if 'drf_spectacular' in settings_content:
            checks.append(("PASS", "OpenAPI documentation (drf-spectacular) configured"))
        else:
            checks.append(("FAIL", "OpenAPI documentation not configured"))
    else:
        checks.append(("FAIL", "Settings file not found"))

    # 5-tekseriw: URL dúzilisi API versiyalawdı qollap-quwatlaydı
    urls_file = Path('config/urls.py')
    if urls_file.exists():
        urls_content = urls_file.read_text()
        if 'api/' in urls_content:
            checks.append(("PASS", "URL structure configured for API endpoints"))
        else:
            checks.append(("WARN", "URL structure may not support API versioning"))

        if 'SpectacularAPIView' in urls_content:
            checks.append(("PASS", "API documentation endpoints configured"))
        else:
            checks.append(("FAIL", "API documentation endpoints not configured"))
    else:
        checks.append(("FAIL", "URLs file not found"))

    # 6-tekseriw: Erte API iske asırıwı joq
    # 01-checkpoint ushın haqıyqıy API endpoint leri iske asırılmawı kerek
    if urls_file.exists():
        urls_content = urls_file.read_text()
        # Haqıyqıy API endpoint leri iske asırılǵanın tekseriw (01-checkpoint ushın olar bolmawı kerek)
        if 'include(' in urls_content and 'api_v1' in urls_content:
            checks.append(("WARN", "API v1 endpoints may be prematurely implemented"))
        else:
            checks.append(("PASS", "No premature API endpoint implementation (correct for checkpoint 01)"))

    # 7-tekseriw: Shártnama qaǵıydalarına ámel etilgen
    if contract_content:
        if 'OpenAPI documentation is mandatory' in contract_content:
            checks.append(("PASS", "Contract specifies OpenAPI documentation requirement"))
        else:
            checks.append(("WARN", "Contract may not specify OpenAPI documentation requirement"))

        if 'Breaking API changes require /api/v2/' in contract_content:
            checks.append(("PASS", "Contract specifies versioning rule for breaking changes"))
        else:
            checks.append(("WARN", "Contract may not specify versioning rules"))

    # Nátiyjelerdi shıǵarıw
    print("\nContract Consistency Status:")
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
        print("\nPASS: Contract consistency check PASSED")
        return True
    else:
        print(f"\nFAIL: Contract consistency check FAILED ({failed} issues)")
        return False

if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

    os.chdir(Path(__file__).parent.parent.parent)
    success = check_contract_consistency()
    sys.exit(0 if success else 1)
