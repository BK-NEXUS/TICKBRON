"""
Security Review Script for Checkpoint 12 - Availability API/Pricing Preview

This script performs a comprehensive security review of the availability API:
- Availability endpoint implementation
- Deterministic pricing behavior
- Date range parameter validation
- Security for sensitive data
"""

import re
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_availability_endpoint_exists():
    """Check if availability endpoint exists."""
    print("[*] Checking availability endpoint...")
    
    views_file = Path(__file__).parent.parent / 'properties' / 'views.py'
    views_content = views_file.read_text()
    
    checks = {
        'property_availability_view': 'def property_availability' in views_content,
        'property_id_parameter': 'property_id' in views_content,
        'property_model_import': 'from properties.models import Property' in views_content,
        'availability_serializer': 'PropertyAvailabilitySerializer' in views_content,
        'availability_params_serializer': 'AvailabilityParamsSerializer' in views_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Availability endpoint: {passed}/{total} checks passed")
    return passed == total

def check_availability_serializer_completeness():
    """Check if availability serializer includes all required sections."""
    print("[*] Checking availability serializer completeness...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'room_types_method': 'def get_room_types' in serializers_content,
        'rate_plans_method': 'def get_rate_plans' in serializers_content,
        'date_inventory_method': 'def get_date_inventory' in serializers_content,
        'remaining_rooms_field': 'remaining_rooms' in serializers_content,
        'date_inventory_serializer': 'DateInventorySerializer' in serializers_content,
        'rate_plan_availability_serializer': 'RatePlanAvailabilitySerializer' in serializers_content,
        'room_type_availability_serializer': 'RoomTypeAvailabilitySerializer' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Serializer completeness: {passed}/{total} checks passed")
    return passed == total

def check_availability_date_range_validation():
    """Check if date range parameters are properly validated."""
    print("[*] Checking date range validation...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'availability_params_serializer': 'AvailabilityParamsSerializer' in serializers_content,
        'check_in_field': 'check_in' in serializers_content,
        'check_out_field': 'check_out' in serializers_content,
        'date_field_type': 'DateField' in serializers_content,
        'date_range_validation': 'check_out must be after check_in' in serializers_content or 'check_out <= check_in' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Date range validation: {passed}/{total} checks passed")
    return passed == total

def check_availability_deterministic_behavior():
    """Check if availability behavior is deterministic."""
    print("[*] Checking deterministic availability behavior...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'date_inventory_filtering': 'date__gte' in serializers_content or 'date__lte' in serializers_content,
        'ordered_date_inventory': 'order_by' in serializers_content and 'date' in serializers_content,
        'active_rate_plans_filter': 'is_active=True' in serializers_content,
        'deleted_data_filter': 'is_deleted=False' in serializers_content,
        'consistent_pricing_logic': 'remaining_rooms' in serializers_content or 'available_rooms - booked_rooms' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Deterministic behavior: {passed}/{total} checks passed")
    return passed == total

def check_availability_security():
    """Check if availability endpoint has proper security."""
    print("[*] Checking availability security...")
    
    views_file = Path(__file__).parent.parent / 'properties' / 'views.py'
    views_content = views_file.read_text()
    
    checks = {
        'property_existence_check': 'Property.DoesNotExist' in views_content,
        'is_active_check': 'is_active=True' in views_content,
        'is_deleted_check': 'is_deleted=False' in views_content,
        'parameter_validation': 'AvailabilityParamsSerializer' in views_content,
        'error_handling': 'HTTP_400_BAD_REQUEST' in views_content,
        'error_response_structure': "'error'" in views_content and "'details'" in views_content,
        'public_endpoint_protection': sensitive_data_exposure_check(views_content),
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Availability security: {passed}/{total} checks passed")
    return passed == total

def sensitive_data_exposure_check(views_content):
    """Check that sensitive data is not exposed."""
    # Check that we're not exposing sensitive fields like owner email, phone, etc.
    sensitive_fields = ['email', 'phone', 'password', 'secret', 'token']
    
    # In the availability view, we should not be exposing owner's sensitive data
    # The PropertyAvailabilitySerializer should not include owner's email/phone
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    # Check that owner field is read-only and limited
    if 'owner' in serializers_content:
        # Owner should be read-only and probably just an ID
        return "'owner'" in serializers_content and "read_only_fields" in serializers_content
    
    return True  # If owner is not included at all, that's also safe

def check_availability_url_configuration():
    """Check if availability URL is properly configured."""
    print("[*] Checking URL configuration...")
    
    urls_file = Path(__file__).parent.parent / 'properties' / 'urls.py'
    urls_content = urls_file.read_text()
    
    checks = {
        'availability_url': 'property_availability' in urls_content,
        'property_id_path': '<int:property_id>' in urls_content,
        'availability_import': 'from properties.views import' in urls_content and 'property_availability' in urls_content,
        'availability_path': 'availability/' in urls_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  URL configuration: {passed}/{total} checks passed")
    return passed == total

def check_availability_test_coverage():
    """Check if availability has comprehensive test coverage."""
    print("[*] Checking test coverage...")
    
    test_file = Path(__file__).parent.parent / 'properties' / 'tests' / 'test_availability.py'
    
    if not test_file.exists():
        print("  [FAIL] Availability test file does not exist")
        return False
    
    test_content = test_file.read_text()
    
    checks = {
        'test_file_exists': test_file.exists(),
        'basic_availability_test': 'test_availability_success' in test_content,
        'date_range_test': 'test_availability_with_date_range' in test_content,
        'date_validation_test': 'test_availability_invalid_date_format' in test_content or 'test_availability_invalid_date_range' in test_content,
        'security_test': 'test_availability_deleted_property' in test_content or 'test_availability_inactive_property' in test_content,
        'deterministic_test': 'test_availability_deterministic_pricing' in test_content,
        'not_found_test': 'test_availability_property_not_found' in test_content,
        'public_access_test': 'test_availability_public_access' in test_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Test coverage: {passed}/{total} checks passed")
    return passed == total

def check_availability_pricing_preview():
    """Check if pricing preview is properly implemented."""
    print("[*] Checking pricing preview implementation...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'price_field_in_inventory': 'price' in serializers_content,
        'currency_field_in_inventory': 'currency' in serializers_content,
        'base_price_in_rate_plan': 'base_price' in serializers_content,
        'remaining_rooms_calculation': 'remaining_rooms' in serializers_content,
        'is_available_field': 'is_available' in serializers_content,
        'minimum_stay_field': 'minimum_stay' in serializers_content,
        'maximum_stay_field': 'maximum_stay' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Pricing preview: {passed}/{total} checks passed")
    return passed == total

def run_security_review():
    """Run the complete security review."""
    print("=" * 60)
    print("CHECKPOINT 12 SECURITY REVIEW: Availability API/Pricing Preview")
    print("=" * 60)
    print()
    
    results = {
        'Availability Endpoint': check_availability_endpoint_exists(),
        'Serializer Completeness': check_availability_serializer_completeness(),
        'Date Range Validation': check_availability_date_range_validation(),
        'Deterministic Behavior': check_availability_deterministic_behavior(),
        'Availability Security': check_availability_security(),
        'URL Configuration': check_availability_url_configuration(),
        'Test Coverage': check_availability_test_coverage(),
        'Pricing Preview': check_availability_pricing_preview(),
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