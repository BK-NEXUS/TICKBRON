"""
Security review script for room/rate plan/inventory models (Checkpoint 08).

This script performs a comprehensive security review of the room, rate plan, 
and inventory models to ensure they meet TICKBRON security standards.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from properties.models import (
    RoomType, RoomPhoto, RoomAmenity, RatePlan, DateInventory,
    Property, PropertyType, AmenityCategory, Amenity
)
from users.models import User
from decimal import Decimal
from datetime import date


def print_security_check(title, passed, details=""):
    """Print formatted security check result."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status}: {title}")
    if details:
        print(f"  Details: {details}")
    return passed


def run_security_checks():
    """Run comprehensive security checks for room/rate plan/inventory models."""
    print("=" * 60)
    print("ROOM/RATE PLAN/INVENTORY SECURITY REVIEW - CHECKPOINT 08")
    print("=" * 60)
    print()
    
    passed_checks = 0
    total_checks = 0
    
    # Clean up any existing test data
    User.objects.filter(email__contains='securitytest').delete()
    Property.objects.filter(address_line1__contains='Security Test').delete()
    PropertyType.objects.filter(name__contains='Security Test').delete()
    AmenityCategory.objects.filter(name__contains='Security Test').delete()
    
    # Set up test data
    user = User.objects.create_user(
        email='securitytest@example.com',
        password='TestPassword123!',
        first_name='Security',
        last_name='Test'
    )
    property_type = PropertyType.objects.create(
        name='Security Test Property Type',
        slug='security-test-property-type'
    )
    property = Property.objects.create(
        owner=user,
        property_type=property_type,
        max_guests=4,
        address_line1='Security Test Address',
        city='Test City',
        country='Test Country',
        base_price=Decimal('100.00')
    )
    category = AmenityCategory.objects.create(
        name='Security Test Category',
        slug='security-test-category'
    )
    amenity = Amenity.objects.create(
        category=category,
        name='Security Test Amenity',
        slug='security-test-amenity'
    )
    
    # Check 1: RoomType model field security
    print("1. RoomType Model Field Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Security Test Room',
            slug='security-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        # Check string representation doesn't expose sensitive data
        str_repr = str(room_type)
        passed = 'email' not in str_repr.lower() and 'password' not in str_repr.lower()
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType string representation security",
            passed,
            f"String repr: {str_repr}"
        )
        
        # Check validation for occupancy
        invalid_room = RoomType(
            property=property,
            name='Invalid Room',
            slug='invalid-room',
            base_occupancy=4,
            max_occupancy=2,  # Invalid: max < base
            base_price=Decimal('80.00')
        )
        try:
            invalid_room.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType occupancy validation",
            passed
        )
        
        room_type.delete()
        
    except Exception as e:
        total_checks += 2
        print_security_check("RoomType field security", False, str(e))
        print_security_check("RoomType occupancy validation", False, "Skipped due to error")
    
    # Check 2: RoomType unique constraints
    print("\n2. RoomType Unique Constraints")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Unique Test Room',
            slug='unique-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        # Try to create duplicate slug for same property
        try:
            duplicate = RoomType(
                property=property,
                name='Different Room',
                slug='unique-test-room',  # Same slug
                base_occupancy=2,
                max_occupancy=4,
                base_price=Decimal('90.00')
            )
            duplicate.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType unique constraint (property, slug)",
            passed
        )
        
        room_type.delete()
        
    except Exception as e:
        total_checks += 1
        print_security_check("RoomType unique constraints", False, str(e))
    
    # Check 3: RoomPhoto model security
    print("\n3. RoomPhoto Model Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Photo Test Room',
            slug='photo-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        # Check primary photo constraint
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = SimpleUploadedFile(
            name='test_photo.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        photo1 = RoomPhoto.objects.create(
            room_type=room_type,
            photo=image,
            is_primary=True
        )
        
        photo2 = RoomPhoto.objects.create(
            room_type=room_type,
            photo=image,
            is_primary=True
        )
        
        # Refresh and check only one is primary
        photo1.refresh_from_db()
        photo2.refresh_from_db()
        passed = not photo1.is_primary and photo2.is_primary
        total_checks += 1
        passed_checks += print_security_check(
            "RoomPhoto primary photo constraint",
            passed
        )
        
        # Check image validation
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        invalid_photo = RoomPhoto(
            room_type=room_type,
            photo=invalid_file
        )
        try:
            invalid_photo.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RoomPhoto image validation",
            passed
        )
        
        photo1.delete()
        photo2.delete()
        room_type.delete()
        
    except Exception as e:
        total_checks += 2
        print_security_check("RoomPhoto primary constraint", False, str(e))
        print_security_check("RoomPhoto image validation", False, "Skipped due to error")
    
    # Check 4: RoomAmenity model security
    print("\n4. RoomAmenity Model Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Amenity Test Room',
            slug='amenity-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        room_amenity = RoomAmenity.objects.create(
            room_type=room_type,
            amenity=amenity,
            is_available=True
        )
        
        # Try to create duplicate
        try:
            duplicate = RoomAmenity(
                room_type=room_type,
                amenity=amenity,  # Same amenity for same room type
                is_available=False
            )
            duplicate.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RoomAmenity unique constraint (room_type, amenity)",
            passed
        )
        
        room_amenity.delete()
        room_type.delete()
        
    except Exception as e:
        total_checks += 1
        print_security_check("RoomAmenity unique constraints", False, str(e))
    
    # Check 5: RatePlan model security
    print("\n5. RatePlan Model Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Rate Test Room',
            slug='rate-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        # Check nights validation
        invalid_rate = RatePlan(
            room_type=room_type,
            name='Invalid Rate',
            slug='invalid-rate',
            min_nights=7,
            max_nights=3,  # Invalid: max < min
            base_price=Decimal('80.00')
        )
        try:
            invalid_rate.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan nights validation",
            passed
        )
        
        # Check deposit validation
        invalid_deposit = RatePlan(
            room_type=room_type,
            name='Invalid Deposit Rate',
            slug='invalid-deposit-rate',
            base_price=Decimal('80.00'),
            deposit_required=True,
            deposit_percentage=None  # Invalid: required when deposit_required is True
        )
        try:
            invalid_deposit.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan deposit validation",
            passed
        )
        
        # Check unique constraint
        rate_plan = RatePlan.objects.create(
            room_type=room_type,
            name='Test Rate',
            slug='test-rate',
            base_price=Decimal('80.00')
        )
        
        try:
            duplicate = RatePlan(
                room_type=room_type,
                name='Different Rate',
                slug='test-rate',  # Same slug
                base_price=Decimal('90.00')
            )
            duplicate.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan unique constraint (room_type, slug)",
            passed
        )
        
        rate_plan.delete()
        room_type.delete()
        
    except Exception as e:
        total_checks += 3
        print_security_check("RatePlan nights validation", False, str(e))
        print_security_check("RatePlan deposit validation", False, "Skipped due to error")
        print_security_check("RatePlan unique constraint", False, "Skipped due to error")
    
    # Check 6: DateInventory model security
    print("\n6. DateInventory Model Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Inventory Test Room',
            slug='inventory-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        rate_plan = RatePlan.objects.create(
            room_type=room_type,
            name='Test Rate',
            slug='test-rate',
            base_price=Decimal('80.00')
        )
        
        # Check booked_rooms validation
        invalid_inventory = DateInventory(
            rate_plan=rate_plan,
            date=date(2024, 6, 16),
            available_rooms=3,
            booked_rooms=5  # Invalid: more than available
        )
        try:
            invalid_inventory.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory booked_rooms validation",
            passed
        )
        
        # Check stay validation
        invalid_stay = DateInventory(
            rate_plan=rate_plan,
            date=date(2024, 6, 17),
            available_rooms=5,
            booked_rooms=2,
            minimum_stay=7,
            maximum_stay=3  # Invalid: max < min
        )
        try:
            invalid_stay.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory stay validation",
            passed
        )
        
        # Check unique constraint
        inventory = DateInventory.objects.create(
            rate_plan=rate_plan,
            date=date(2024, 6, 15),
            available_rooms=5,
            booked_rooms=0
        )
        
        try:
            duplicate = DateInventory(
                rate_plan=rate_plan,
                date=date(2024, 6, 15),  # Same date for same rate plan
                available_rooms=3
            )
            duplicate.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory unique constraint (rate_plan, date)",
            passed
        )
        
        # Check remaining_rooms property
        inventory.booked_rooms = 2
        inventory.save()
        passed = inventory.remaining_rooms == 3  # 5 - 2 = 3
        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory remaining_rooms calculation",
            passed,
            f"Available: 5, Booked: 2, Remaining: {inventory.remaining_rooms}"
        )
        
        # Check is_available_for_booking method
        passed = inventory.is_available_for_booking(nights=5)
        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory availability check",
            passed
        )
        
        inventory.delete()
        rate_plan.delete()
        room_type.delete()
        
    except Exception as e:
        total_checks += 5
        print_security_check("DateInventory booked validation", False, str(e))
        print_security_check("DateInventory stay validation", False, "Skipped due to error")
        print_security_check("DateInventory unique constraint", False, "Skipped due to error")
        print_security_check("DateInventory remaining_rooms", False, "Skipped due to error")
        print_security_check("DateInventory availability check", False, "Skipped due to error")
    
    # Check 7: CASCADE deletion security
    print("\n7. CASCADE Deletion Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Cascade Test Room',
            slug='cascade-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        # Create related objects
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = SimpleUploadedFile(
            name='test_photo.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        photo = RoomPhoto.objects.create(
            room_type=room_type,
            photo=image
        )
        photo_id = photo.id
        
        room_amenity = RoomAmenity.objects.create(
            room_type=room_type,
            amenity=amenity
        )
        room_amenity_id = room_amenity.id
        
        rate_plan = RatePlan.objects.create(
            room_type=room_type,
            name='Cascade Test Rate',
            slug='cascade-test-rate',
            base_price=Decimal('80.00')
        )
        rate_plan_id = rate_plan.id
        
        inventory = DateInventory.objects.create(
            rate_plan=rate_plan,
            date=date(2024, 6, 15),
            available_rooms=5
        )
        inventory_id = inventory.id
        
        # Delete room type and check cascade
        room_type.delete()
        
        passed = not RoomPhoto.objects.filter(id=photo_id).exists()
        total_checks += 1
        passed_checks += print_security_check(
            "CASCADE deletion: RoomType -> RoomPhoto",
            passed
        )
        
        passed = not RoomAmenity.objects.filter(id=room_amenity_id).exists()
        total_checks += 1
        passed_checks += print_security_check(
            "CASCADE deletion: RoomType -> RoomAmenity",
            passed
        )
        
        passed = not RatePlan.objects.filter(id=rate_plan_id).exists()
        total_checks += 1
        passed_checks += print_security_check(
            "CASCADE deletion: RoomType -> RatePlan",
            passed
        )
        
        passed = not DateInventory.objects.filter(id=inventory_id).exists()
        total_checks += 1
        passed_checks += print_security_check(
            "CASCADE deletion: RatePlan -> DateInventory",
            passed
        )
        
    except Exception as e:
        total_checks += 4
        print_security_check("CASCADE deletion: RoomType -> RoomPhoto", False, str(e))
        print_security_check("CASCADE deletion: RoomType -> RoomAmenity", False, "Skipped due to error")
        print_security_check("CASCADE deletion: RoomType -> RatePlan", False, "Skipped due to error")
        print_security_check("CASCADE deletion: RatePlan -> DateInventory", False, "Skipped due to error")
    
    # Check 8: Database indexes
    print("\n8. Database Indexes")
    print("-" * 40)
    try:
        # Check RoomType indexes
        room_type_indexes = RoomType._meta.indexes
        passed = len(room_type_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType database indexes",
            passed,
            f"Found {len(room_type_indexes)} indexes"
        )
        
        # Check RatePlan indexes
        rate_plan_indexes = RatePlan._meta.indexes
        passed = len(rate_plan_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan database indexes",
            passed,
            f"Found {len(rate_plan_indexes)} indexes"
        )
        
        # Check DateInventory indexes
        date_inventory_indexes = DateInventory._meta.indexes
        passed = len(date_inventory_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory database indexes",
            passed,
            f"Found {len(date_inventory_indexes)} indexes"
        )
        
    except Exception as e:
        total_checks += 3
        print_security_check("Database indexes", False, str(e))
        print_security_check("RatePlan indexes", False, "Skipped due to error")
        print_security_check("DateInventory indexes", False, "Skipped due to error")
    
    # Check 9: Soft delete security
    print("\n9. Soft Delete Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Soft Delete Test Room',
            slug='soft-delete-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        # Test soft delete
        room_type.soft_delete()
        passed = room_type.is_deleted and room_type.deleted_at is not None
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType soft delete functionality",
            passed
        )
        
        # Test restore
        room_type.restore()
        passed = not room_type.is_deleted and room_type.deleted_at is None
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType soft delete restore functionality",
            passed
        )
        
        room_type.delete()
        
    except Exception as e:
        total_checks += 2
        print_security_check("Soft delete security", False, str(e))
        print_security_check("Soft delete restore", False, "Skipped due to error")
    
    # Check 10: Price validation security
    print("\n10. Price Validation Security")
    print("-" * 40)
    try:
        room_type = RoomType.objects.create(
            property=property,
            name='Price Test Room',
            slug='price-test-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        
        # Check negative price validation
        invalid_price_room = RoomType(
            property=property,
            name='Invalid Price Room',
            slug='invalid-price-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('-10.00')  # Invalid: negative
        )
        try:
            invalid_price_room.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType negative price validation",
            passed
        )
        
        # Check negative price for RatePlan
        invalid_price_rate = RatePlan(
            room_type=room_type,
            name='Invalid Price Rate',
            slug='invalid-price-rate',
            base_price=Decimal('-10.00')  # Invalid: negative
        )
        try:
            invalid_price_rate.full_clean()
            passed = False
        except:
            passed = True
        
        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan negative price validation",
            passed
        )
        
        room_type.delete()
        
    except Exception as e:
        total_checks += 2
        print_security_check("RoomType price validation", False, str(e))
        print_security_check("RatePlan price validation", False, "Skipped due to error")
    
    # Cleanup
    amenity.delete()
    category.delete()
    property.delete()
    property_type.delete()
    user.delete()
    
    # Summary
    print("\n" + "=" * 60)
    print("SECURITY REVIEW SUMMARY")
    print("=" * 60)
    print(f"Total checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Success rate: {(passed_checks/total_checks)*100:.1f}%")
    print("=" * 60)
    
    return passed_checks == total_checks


if __name__ == '__main__':
    success = run_security_checks()
    sys.exit(0 if success else 1)