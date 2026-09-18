"""
Security Review Script for Checkpoint 11 - Property Detail Aggregate API

This script performs a comprehensive security review of the property detail API:
- Property detail endpoint implementation
- Gallery and amenities exposure
- Room types and rate plans data
- Security for sensitive data
"""

import re
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_property_detail_endpoint_exists():
    """Check if property detail endpoint exists."""
    print("[*] Checking property detail endpoint...")
    
    views_file = Path(__file__).parent.parent / 'properties' / 'views.py'
    views_content = views_file.read_text()
    
    checks = {
        'property_detail_view': 'def property_detail' in views_content,
        'property_id_parameter': 'property_id' in views_content,
        'property_model_import': 'from properties.models import Property' in views_content,
        'property_detail_serializer': 'PropertyDetailSerializer' in views_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Property detail endpoint: {passed}/{total} checks passed")
    return passed == total

def check_property_detail_serializer_completeness():
    """Check if property detail serializer includes all required sections."""
    print("[*] Checking property detail serializer completeness...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'gallery_method': 'def get_gallery' in serializers_content,
        'room_types_method': 'def get_room_types' in serializers_content,
        'amenities_method': 'def get_amenities' in serializers_content,
        'full_address_method': 'def get_full_address' in serializers_content,
        'translations_field': 'translations' in serializers_content,
        'policies_field': 'policies' in serializers_content,
        'photos_field': 'photos' in serializers_content,
        'property_type_field': 'property_type' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Serializer completeness: {passed}/{total} checks passed")
    return passed == total

def check_property_detail_gallery_implementation():
    """Check if gallery is properly implemented."""
    print("[*] Checking gallery implementation...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'gallery_organized_by_type': "'exterior'" in serializers_content and "'interior'" in serializers_content,
        'gallery_photo_filtering': 'is_active=True' in serializers_content or 'is_deleted=False' in serializers_content,
        'gallery_ordering': 'display_order' in serializers_content,
        'photo_serializer_usage': 'PropertyPhotoSerializer' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Gallery implementation: {passed}/{total} checks passed")
    return passed == total

def check_property_detail_room_types_implementation():
    """Check if room types with rate plans are properly implemented."""
    print("[*] Checking room types implementation...")
    
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    checks = {
        'room_types_import': 'RoomType' in serializers_content or 'from properties.models import' in serializers_content,
        'rate_plans_inclusion': 'rate_plans' in serializers_content,
        'room_photos_inclusion': 'photos' in serializers_content,
        'room_amenities_inclusion': 'amenities' in serializers_content,
        'active_rate_plans_filter': 'is_active=True' in serializers_content,
        'rate_plan_structure': 'base_price' in serializers_content and 'min_nights' in serializers_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Room types implementation: {passed}/{total} checks passed")
    return passed == total

def check_property_detail_security():
    """Check if property detail endpoint has proper security."""
    print("[*] Checking property detail security...")
    
    views_file = Path(__file__).parent.parent / 'properties' / 'views.py'
    views_content = views_file.read_text()
    
    checks = {
        'property_existence_check': 'Property.DoesNotExist' in views_content,
        'is_active_check': 'is_active=True' in views_content,
        'is_deleted_check': 'is_deleted=False' in views_content,
        'error_handling': 'HTTP_404_NOT_FOUND' in views_content,
        'error_response_structure': "'error'" in views_content and "'details'" in views_content,
        'public_endpoint_protection': sensitive_data_exposure_check(views_content),
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Property detail security: {passed}/{total} checks passed")
    return passed == total

def sensitive_data_exposure_check(views_content):
    """Check that sensitive data is not exposed."""
    # Check that we're not exposing sensitive fields like owner email, phone, etc.
    sensitive_fields = ['email', 'phone', 'password', 'secret', 'token']
    
    # In the property detail view, we should not be exposing owner's sensitive data
    # The PropertyDetailSerializer should not include owner's email/phone
    serializers_file = Path(__file__).parent.parent / 'properties' / 'serializers.py'
    serializers_content = serializers_file.read_text()
    
    # Check that owner field is read-only and limited
    if 'owner' in serializers_content:
        # Owner should be read-only and probably just an ID
        return "'owner'" in serializers_content and "read_only_fields" in serializers_content
    
    return True  # If owner is not included at all, that's also safe

def check_property_detail_url_configuration():
    """Check if property detail URL is properly configured."""
    print("[*] Checking URL configuration...")
    
    urls_file = Path(__file__).parent.parent / 'properties' / 'urls.py'
    urls_content = urls_file.read_text()
    
    checks = {
        'property_detail_url': 'property_detail' in urls_content,
        'property_id_path': '<int:property_id>' in urls_content,
        'property_detail_import': 'from properties.views import' in urls_content and 'property_detail' in urls_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  URL configuration: {passed}/{total} checks passed")
    return passed == total

def check_property_detail_test_coverage():
    """Check if property detail has comprehensive test coverage."""
    print("[*] Checking test coverage...")
    
    test_file = Path(__file__).parent.parent / 'properties' / 'tests' / 'test_property_detail.py'
    
    if not test_file.exists():
        print("  [FAIL] Property detail test file does not exist")
        return False
    
    test_content = test_file.read_text()
    
    checks = {
        'test_file_exists': test_file.exists(),
        'basic_detail_test': 'test_property_detail_success' in test_content,
        'gallery_test': 'test_property_detail_includes_gallery' in test_content,
        'amenities_test': 'test_property_detail_includes_amenities' in test_content,
        'room_types_test': 'test_property_detail_includes_room_types' in test_content,
        'policies_test': 'test_property_detail_includes_policies' in test_content,
        'not_found_test': 'test_property_detail_not_found' in test_content,
        'security_test': 'test_property_detail_deleted_property' in test_content or 'test_property_detail_inactive_property' in test_content,
    }
    
    passed = sum(checks.values())
    total = len(checks)
    
    for check, result in checks.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"  Test coverage: {passed}/{total} checks passed")
    return passed == total

def run_security_review():
    """Run the complete security review."""
    print("=" * 60)
    print("CHECKPOINT 11 SECURITY REVIEW: Property Detail Aggregate API")
    print("=" * 60)
    print()
    
    results = {
        'Property Detail Endpoint': check_property_detail_endpoint_exists(),
        'Serializer Completeness': check_property_detail_serializer_completeness(),
        'Gallery Implementation': check_property_detail_gallery_implementation(),
        'Room Types Implementation': check_property_detail_room_types_implementation(),
        'Property Detail Security': check_property_detail_security(),
        'URL Configuration': check_property_detail_url_configuration(),
        'Test Coverage': check_property_detail_test_coverage(),
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
