"""
API Contract Consistency Check for TICKBRON Backend Checkpoint 01

This script verifies that the foundation is consistent with the API contract.
"""
import os
from pathlib import Path

def check_contract_consistency():
    """Verify API contract consistency with foundation setup."""
    
    print("TICKBRON Backend API Contract Consistency Check")
    print("=" * 50)
    
    checks = []
    
    # Check 1: API contract file exists
    contract_file = Path('../.ai/API_CONTRACT.md')
    if contract_file.exists():
        checks.append(("PASS", "API contract file exists"))
        contract_content = contract_file.read_text()
    else:
        checks.append(("FAIL", "API contract file not found"))
        contract_content = ""
    
    # Check 2: Version prefix is defined in contract
    if contract_content:
        if '/api/v1/' in contract_content:
            checks.append(("PASS", "API version prefix /api/v1/ defined in contract"))
        else:
            checks.append(("FAIL", "API version prefix not defined in contract"))
    
    # Check 3: Core endpoints are listed in contract
    if contract_content:
        required_endpoints = [
            'auth/register',
            'auth/login', 
            'auth/refresh',
            'properties/search',
            'bookings',
            'payments'
        ]
        missing_endpoints = []
        for endpoint in required_endpoints:
            if endpoint not in contract_content:
                missing_endpoints.append(endpoint)
        
        if not missing_endpoints:
            checks.append(("PASS", "Core endpoints listed in contract"))
        else:
            checks.append(("WARN", f"Some core endpoints missing from contract: {missing_endpoints}"))
    
    # Check 4: Django REST Framework is configured
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
    
    # Check 5: URL structure supports API versioning
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
    
    # Check 6: No premature API implementation
    # For checkpoint 01, we should NOT have implemented actual API endpoints
    if urls_file.exists():
        urls_content = urls_file.read_text()
        # Check if actual API endpoints are implemented (they shouldn't be for checkpoint 01)
        if 'include(' in urls_content and 'api_v1' in urls_content:
            checks.append(("WARN", "API v1 endpoints may be prematurely implemented"))
        else:
            checks.append(("PASS", "No premature API endpoint implementation (correct for checkpoint 01)"))
    
    # Check 7: Contract rules are followed
    if contract_content:
        if 'OpenAPI documentation is mandatory' in contract_content:
            checks.append(("PASS", "Contract specifies OpenAPI documentation requirement"))
        else:
            checks.append(("WARN", "Contract may not specify OpenAPI documentation requirement"))
        
        if 'Breaking API changes require /api/v2/' in contract_content:
            checks.append(("PASS", "Contract specifies versioning rule for breaking changes"))
        else:
            checks.append(("WARN", "Contract may not specify versioning rules"))
    
    # Print results
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
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    os.chdir(Path(__file__).parent.parent)
    success = check_contract_consistency()
    sys.exit(0 if success else 1)
