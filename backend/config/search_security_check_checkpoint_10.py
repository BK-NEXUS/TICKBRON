"""
Security Review Script for Checkpoint 10 - Search API Standardization

This script performs a comprehensive security review of the search API improvements:
- Standardized filtering
- Standardized sorting  
- Standardized pagination
- Improved error handling and validation
"""

import re
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_search_parameter_validation():
    """Check if search parameters are properly validated."""
    print("[*] Checking search parameter validation...")
    
    search_file = Path(__file__).parent.parent / 'properties' / 'search.py'
    search_content = search_file.read_text()
    
    checks = {
        'query_length_validation': 'len(q) > 500' in search_content,
        'location_length_validation': 'len(location) > 200' in search_content,
        'latitude_validation': '-90 <= lat <= 90' in search_content,
        'longitude_validation': '-180 <= lng <= 180' in search_content,
        'radius_validation': '1 <= radius <= 100' in search_content,
        'price_validation': 'min_price < 0' in search_content or 'max_price < 0' in search_content,
        'guest_validation': 'min_guests < 1' in search_content or 'max_guests < 1' in search_content,
        'amenity_count_validation': 'len(amenities) > 20' in search_content,
        'page_size_validation': 'page_size < 1 or page_size > 100' in search_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Parameter validation: {passed}/{total} checks passed")
    return passed == total

def check_input_sanitization():
    """Check if user input is properly sanitized."""
    print("[*] Checking input sanitization...")
    
    search_file = Path(__file__).parent.parent / 'properties' / 'search.py'
    search_content = search_file.read_text()
    
    checks = {
        'html_tag_removal': "re.sub(r'[<>\"\\']', '', q)" in search_content,
        'query_stripping': "str(search_params['q']).strip()" in search_content or 'str(search_params["q"]).strip()' in search_content,
        'location_stripping': "str(search_params['location']).strip()" in search_content or 'str(search_params["location"]).strip()' in search_content,
        'type_conversion': 'str(search_params' in search_content or 'float(search_params' in search_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Input sanitization: {passed}/{total} checks passed")
    return passed == total

def check_error_handling():
    """Check if error handling is comprehensive."""
    print("[*] Checking error handling...")
    
    views_file = Path(__file__).parent.parent / 'properties' / 'views.py'
    views_content = views_file.read_text()
    
    search_file = Path(__file__).parent.parent / 'properties' / 'search.py'
    search_content = search_file.read_text()
    
    checks = {
        'value_error_handling': 'ValueError' in views_content,
        'generic_error_handling': 'Exception' in views_content,
        'standardized_error_response': "'error'" in views_content and "'details'" in views_content,
        'service_layer_validation': 'ValueError' in search_content,
        'pagination_error_handling': 'EmptyPage' in search_content or 'PageNotAnInteger' in search_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Error handling: {passed}/{total} checks passed")
    return passed == total

def check_pagination_security():
    """Check if pagination is secure."""
    print("[*] Checking pagination security...")
    
    search_file = Path(__file__).parent.parent / 'properties' / 'search.py'
    search_content = search_file.read_text()
    
    checks = {
        'page_size_limit': 'page_size > 100' in search_content,
        'page_minimum': 'page < 1' in search_content,
        'pagination_error_recovery': 'page = 1' in search_content,
        'pagination_metadata': "'total_pages'" in search_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Pagination security: {passed}/{total} checks passed")
    return passed == total

def check_sql_injection_prevention():
    """Check if SQL injection is prevented."""
    print("[*] Checking SQL injection prevention...")
    
    search_file = Path(__file__).parent.parent / 'properties' / 'search.py'
    search_content = search_file.read_text()
    
    checks = {
        'orm_usage': 'Q(' in search_content or 'filter(' in search_content,
        'no_raw_sql': 'raw(' not in search_content and 'execute(' not in search_content,
        'parameterized_queries': 'filter(' in search_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  SQL injection prevention: {passed}/{total} checks passed")
    return passed == total

def check_serializer_validation():
    """Check if serializer validation is comprehensive."""
    print("[*] Checking serializer validation...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'max_length_constraints': 'max_length=' in serializers_content,
        'min_value_constraints': 'min_value=' in serializers_content,
        'max_value_constraints': 'max_value=' in serializers_content,
        'choice_validation': 'ChoiceField' in serializers_content,
        'custom_validation': 'def validate' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Serializer validation: {passed}/{total} checks passed")
    return passed == total

def check_rate_limiting_considerations():
    """Check if rate limiting considerations are addressed."""
    print("[*] Checking rate limiting considerations...")
    
    views_file = Path(__file__).parent.parent / 'properties' / 'views.py'
    views_content = views_file.read_text()
    
    checks = {
        'pagination_limits': 'page_size' in views_content,
        'query_complexity_limits': 'amenities' in views_content or 'page_size' in views_content,
        'public_endpoint_awareness': 'AllowAny' in views_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Rate limiting considerations: {passed}/{total} checks passed")
    return passed == total

def run_security_review():
    """Run the complete security review."""
    print("=" * 60)
    print("CHECKPOINT 10 SECURITY REVIEW: Search API Standardization")
    print("=" * 60)
    print()
    
    results = {
        'Parameter Validation': check_search_parameter_validation(),
        'Input Sanitization': check_input_sanitization(),
        'Error Handling': check_error_handling(),
        'Pagination Security': check_pagination_security(),
        'SQL Injection Prevention': check_sql_injection_prevention(),
        'Serializer Validation': check_serializer_validation(),
        'Rate Limiting Considerations': check_rate_limiting_considerations(),
    }
    
    print()
    print("=" * 60)
    print("SECURITY REVIEW SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for category, result in results.items():
        status = "[PASS] PASSED" if result else "[FAIL] FAILED"
        print(f"{status}: {category}")
    
    print()
    print(f"Overall: {passed}/{total} categories passed")
    
    if passed == total:
        print("[SUCCESS] All security checks passed!")
        return True
    else:
        print("[WARNING] Some security checks failed. Review needed.")
        return False

if __name__ == '__main__':
    success = run_security_review()
    sys.exit(0 if success else 1)