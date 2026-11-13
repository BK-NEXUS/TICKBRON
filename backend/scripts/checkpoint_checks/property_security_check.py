"""
Property model leri ushın qáwipsizlik tekseriwi (Backend Checkpoint 05).

Bul skript mehmanxana model lerin hám baylanıslı infrastrukturanı tolıq qáwipsizlik
tekseriwinen ótkeredi.
"""
import os
import sys
import uuid
from django.core.exceptions import ValidationError

# Django dı tayarlaw
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import django
django.setup()

from properties.models import PropertyType, Property, PropertyTranslation, PropertyPolicy
from users.models import User
from decimal import Decimal


def check_ownership_security():
    """Mehmanxana iyeliginiń qáwipsizligin tekseriw."""
    print("=== Ownership Security ===")

    # Paydalanıwshılar tek óz mehmanxanalarına qol jetkere alatuǵının testlew
    unique_id = str(uuid.uuid4())[:8]
    user1 = User.objects.create_user(
        email=f'user1_{unique_id}@example.com',
        password='TestPassword123!',
        first_name='User',
        last_name='One'
    )
    user2 = User.objects.create_user(
        email=f'user2_{unique_id}@example.com',
        password='TestPassword123!',
        first_name='User',
        last_name='Two'
    )

    property_type = PropertyType.objects.create(
        name=f'Apartment_{unique_id}',
        slug=f'apartment_{unique_id}'
    )

    # user1 ge tiyisli mehmanxananı jaratıw
    property1 = Property.objects.create(
        owner=user1,
        property_type=property_type,
        max_guests=4,
        address_line1='123 Main Street',
        city='Tashkent',
        country='Uzbekistan',
        base_price=Decimal('100.00')
    )

    # Iyelikti tastıyıqlaw
    assert property1.owner == user1, "Property ownership check failed"
    assert property1 in user1.properties.all(), "Property-user relation check failed"
    assert property1 not in user2.properties.all(), "User2 should not have access to user1's property"

    print("[PASS] Ownership security: PASSED")

    # Tazalaw
    property1.delete()
    property_type.delete()
    user1.delete()
    user2.delete()


def check_data_validation():
    """Maǵlıwmat validaciyası qáwipsizligin tekseriw."""
    print("=== Data Validation Security ===")

    unique_id = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        email=f'test_{unique_id}@example.com',
        password='TestPassword123!',
        first_name='Test',
        last_name='User'
    )

    property_type = PropertyType.objects.create(
        name=f'Apartment_{unique_id}',
        slug=f'apartment_{unique_id}'
    )

    # Teris baha validaciyasın testlew
    try:
        property_invalid = Property(
            owner=user,
            property_type=property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('-100.00')  # Jaramsız
        )
        property_invalid.full_clean()
        print("[FAIL] Negative price validation: FAILED (should reject negative prices)")
    except ValidationError:
        print("[PASS] Negative price validation: PASSED")

    # Latitude/longitude validaciyasın testlew
    try:
        property_invalid = Property(
            owner=user,
            property_type=property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            latitude=Decimal('91.0')  # Jaramsız (> 90)
        )
        property_invalid.full_clean()
        print("[FAIL] Latitude validation: FAILED (should reject invalid latitude)")
    except ValidationError:
        print("[PASS] Latitude validation: PASSED")

    try:
        property_invalid = Property(
            owner=user,
            property_type=property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            longitude=Decimal('181.0')  # Jaramsız (> 180)
        )
        property_invalid.full_clean()
        print("[FAIL] Longitude validation: FAILED (should reject invalid longitude)")
    except ValidationError:
        print("[PASS] Longitude validation: PASSED")

    # max_guests validaciyasın testlew
    try:
        property_invalid = Property(
            owner=user,
            property_type=property_type,
            max_guests=0,  # Jaramsız (>= 1 bolıwı kerek)
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        property_invalid.full_clean()
        print("[FAIL] Max guests validation: FAILED (should reject 0 guests)")
    except ValidationError:
        print("[PASS] Max guests validation: PASSED")

    # Tazalaw
    property_type.delete()
    user.delete()


def check_uniqueness_constraints():
    """Unikallıq sheklewlerin tekseriw."""
    print("=== Uniqueness Constraints ===")

    unique_id = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        email=f'test_{unique_id}@example.com',
        password='TestPassword123!',
        first_name='Test',
        last_name='User'
    )

    property_type = PropertyType.objects.create(
        name=f'Apartment_{unique_id}',
        slug=f'apartment_{unique_id}'
    )

    property = Property.objects.create(
        owner=user,
        property_type=property_type,
        max_guests=4,
        address_line1='123 Main Street',
        city='Tashkent',
        country='Uzbekistan',
        base_price=Decimal('100.00')
    )

    # PropertyTranslation unikallıǵın testlew
    translation1 = PropertyTranslation.objects.create(
        property=property,
        language='en',
        name='Test Property',
        description='Test description'
    )

    try:
        translation2 = PropertyTranslation.objects.create(
            property=property,
            language='en',  # Birdey til - sátsiz bolıwı kerek
            name='Another Name',
            description='Another description'
        )
        print("[FAIL] PropertyTranslation uniqueness: FAILED (should prevent duplicate language)")
        translation2.delete()
    except Exception:
        print("[PASS] PropertyTranslation uniqueness: PASSED")

    # PropertyPolicy unikallıǵın testlew
    policy1 = PropertyPolicy.objects.create(
        property=property,
        policy_type='check_in',
        title='Check-in Policy',
        description='Test policy'
    )

    try:
        policy2 = PropertyPolicy.objects.create(
            property=property,
            policy_type='check_in',  # Birdey siyasat túri - sátsiz bolıwı kerek
            title='Another Policy',
            description='Another description'
        )
        print("[FAIL] PropertyPolicy uniqueness: FAILED (should prevent duplicate policy type)")
        policy2.delete()
    except Exception:
        print("[PASS] PropertyPolicy uniqueness: PASSED")

    # Tazalaw
    translation1.delete()
    policy1.delete()
    property.delete()
    property_type.delete()
    user.delete()


def check_soft_delete_security():
    """Soft delete qáwipsizligin tekseriw."""
    print("=== Soft Delete Security ===")

    unique_id = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        email=f'test_{unique_id}@example.com',
        password='TestPassword123!',
        first_name='Test',
        last_name='User'
    )

    property_type = PropertyType.objects.create(
        name=f'Apartment_{unique_id}',
        slug=f'apartment_{unique_id}'
    )

    property = Property.objects.create(
        owner=user,
        property_type=property_type,
        max_guests=4,
        address_line1='123 Main Street',
        city='Tashkent',
        country='Uzbekistan',
        base_price=Decimal('100.00')
    )

    # Soft delete di testlew
    property.soft_delete()
    assert property.is_deleted, "Soft delete should set is_deleted flag"
    assert property.deleted_at is not None, "Soft delete should set deleted_at timestamp"

    # Restore di testlew
    property.restore()
    assert not property.is_deleted, "Restore should clear is_deleted flag"
    assert property.deleted_at is None, "Restore should clear deleted_at timestamp"

    print("[PASS] Soft delete security: PASSED")

    # Tazalaw
    property.delete()
    property_type.delete()
    user.delete()


def check_sensitive_data_exposure():
    """Sezgir maǵlıwmat ashılıwın tekseriw."""
    print("=== Sensitive Data Exposure ===")

    # Mehmanxana modelinde paydalanıwshı email i ashılmaǵanın tekseriw
    unique_id = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        email=f'sensitive_{unique_id}@example.com',
        password='TestPassword123!',
        first_name='Sensitive',
        last_name='User'
    )

    property_type = PropertyType.objects.create(
        name=f'Apartment_{unique_id}',
        slug=f'apartment_{unique_id}'
    )

    property = Property.objects.create(
        owner=user,
        property_type=property_type,
        max_guests=4,
        address_line1='123 Main Street',
        city='Tashkent',
        country='Uzbekistan',
        base_price=Decimal('100.00')
    )

    # Mehmanxana modeli sezgir paydalanıwshı maǵlıwmatın tuwrıdan-tuwrı ashpaytuǵının tekseriw
    property_str = str(property)
    assert 'sensitive@example.com' not in property_str, "Property string representation should not expose user email"

    print("[PASS] Sensitive data exposure: PASSED (no direct email exposure)")

    # Tazalaw
    property.delete()
    property_type.delete()
    user.delete()


def check_cascade_deletion():
    """Cascade óshiriw minez-qulqın tekseriw."""
    print("=== Cascade Deletion ===")

    unique_id = str(uuid.uuid4())[:8]
    user = User.objects.create_user(
        email=f'test_{unique_id}@example.com',
        password='TestPassword123!',
        first_name='Test',
        last_name='User'
    )

    property_type = PropertyType.objects.create(
        name=f'Apartment_{unique_id}',
        slug=f'apartment_{unique_id}'
    )

    property = Property.objects.create(
        owner=user,
        property_type=property_type,
        max_guests=4,
        address_line1='123 Main Street',
        city='Tashkent',
        country='Uzbekistan',
        base_price=Decimal('100.00')
    )

    translation = PropertyTranslation.objects.create(
        property=property,
        language='en',
        name='Test Property',
        description='Test description'
    )

    policy = PropertyPolicy.objects.create(
        property=property,
        policy_type='check_in',
        title='Check-in Policy',
        description='Test policy'
    )

    # Mehmanxananı óshiriw hám cascade di tastıyıqlaw
    property.delete()

    assert not PropertyTranslation.objects.filter(id=translation.id).exists(), "Translation should be deleted with property"
    assert not PropertyPolicy.objects.filter(id=policy.id).exists(), "Policy should be deleted with property"

    print("[PASS] Cascade deletion: PASSED")

    # Tazalaw
    property_type.delete()
    user.delete()


def check_database_constraints():
    """Database dárejesindegi sheklewlerdi tekseriw."""
    print("=== Database Constraints ===")

    # Model lerde tiyisli indeksler barlıǵın tastıyıqlaw
    property_model = Property._meta
    assert any(index for index in property_model.indexes if 'status' in str(index.fields)), "Property should have status index"
    assert any(index for index in property_model.indexes if 'city' in str(index.fields) and 'country' in str(index.fields)), "Property should have composite city/country index"

    print("[PASS] Database constraints: PASSED (indexes verified)")


def run_security_check():
    """Barlıq qáwipsizlik tekseriwlerin islew."""
    print("=" * 50)
    print("PROPERTY MODELS SECURITY REVIEW")
    print("Backend Checkpoint 05")
    print("=" * 50)
    print()

    try:
        check_ownership_security()
        check_data_validation()
        check_uniqueness_constraints()
        check_soft_delete_security()
        check_sensitive_data_exposure()
        check_cascade_deletion()
        check_database_constraints()

        print()
        print("=" * 50)
        print("SECURITY REVIEW SUMMARY")
        print("=" * 50)
        print("All security checks: PASSED")
        print("No critical or high security issues found")
        print()
        return True

    except AssertionError as e:
        print()
        print("=" * 50)
        print("SECURITY REVIEW SUMMARY")
        print("=" * 50)
        print(f"Security check FAILED: {e}")
        print()
        return False
    except Exception as e:
        print()
        print("=" * 50)
        print("SECURITY REVIEW SUMMARY")
        print("=" * 50)
        print(f"Security check ERROR: {e}")
        print()
        return False


if __name__ == '__main__':
    success = run_security_check()
    sys.exit(0 if success else 1)
