"""
Xona/rate plan/inventory model leri ushın qáwipsizlik tekseriw skripti (Checkpoint 08).

Bul skript xona, rate plan hám inventory model lerin TICKBRON qáwipsizlik
standartlarına say ekenine isenim hasıl etiw ushın tolıq qáwipsizlik tekseriwinen ótkeredi.
"""
import os
import sys
import django

# Django dı tayarlaw
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    """Qáwipsizlik tekseriw nátiyjesin formatlap shıǵarıw."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status}: {title}")
    if details:
        print(f"  Details: {details}")
    return passed


def run_security_checks():
    """Xona/rate plan/inventory model leri ushın tolıq qáwipsizlik tekseriwlerin islew."""
    print("=" * 60)
    print("ROOM/RATE PLAN/INVENTORY SECURITY REVIEW - CHECKPOINT 08")
    print("=" * 60)
    print()

    passed_checks = 0
    total_checks = 0

    # Bar test maǵlıwmatın tazalaw
    User.objects.filter(email__contains='securitytest').delete()
    Property.objects.filter(address_line1__contains='Security Test').delete()
    PropertyType.objects.filter(name__contains='Security Test').delete()
    AmenityCategory.objects.filter(name__contains='Security Test').delete()

    # Test maǵlıwmatın tayarlaw
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

    # 1-tekseriw: RoomType model maydanlarınıń qáwipsizligi
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

        # Tekst kórinisi sezgir maǵlıwmattı ashpaytuǵının tekseriw
        str_repr = str(room_type)
        passed = 'email' not in str_repr.lower() and 'password' not in str_repr.lower()
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType string representation security",
            passed,
            f"String repr: {str_repr}"
        )

        # Sıyımlılıq validaciyasın tekseriw
        invalid_room = RoomType(
            property=property,
            name='Invalid Room',
            slug='invalid-room',
            base_occupancy=4,
            max_occupancy=2,  # Jaramsız: max < base
            base_price=Decimal('80.00')
        )
        try:
            invalid_room.full_clean()
            passed = False
        except Exception:
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

    # 2-tekseriw: RoomType unikal constraint leri
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

        # Sol mehmanxana ushın dublikat slug jaratıwǵa urınıw
        try:
            duplicate = RoomType(
                property=property,
                name='Different Room',
                slug='unique-test-room',  # Birdey slug
                base_occupancy=2,
                max_occupancy=4,
                base_price=Decimal('90.00')
            )
            duplicate.full_clean()
            passed = False
        except Exception:
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

    # 3-tekseriw: RoomPhoto model qáwipsizligi
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

        # Tiykarǵı súwret constraint in tekseriw
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

        # Jańalap, tek biri tiykarǵı ekenin tekseriw
        photo1.refresh_from_db()
        photo2.refresh_from_db()
        passed = not photo1.is_primary and photo2.is_primary
        total_checks += 1
        passed_checks += print_security_check(
            "RoomPhoto primary photo constraint",
            passed
        )

        # Súwret validaciyasın tekseriw
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
        except Exception:
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

    # 4-tekseriw: RoomAmenity model qáwipsizligi
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

        # Dublikat jaratıwǵa urınıw
        try:
            duplicate = RoomAmenity(
                room_type=room_type,
                amenity=amenity,  # Sol xona túri ushın birdey amenity
                is_available=False
            )
            duplicate.full_clean()
            passed = False
        except Exception:
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

    # 5-tekseriw: RatePlan model qáwipsizligi
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

        # Túnler validaciyasın tekseriw
        invalid_rate = RatePlan(
            room_type=room_type,
            name='Invalid Rate',
            slug='invalid-rate',
            min_nights=7,
            max_nights=3,  # Jaramsız: max < min
            base_price=Decimal('80.00')
        )
        try:
            invalid_rate.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan nights validation",
            passed
        )

        # Depozit validaciyasın tekseriw
        invalid_deposit = RatePlan(
            room_type=room_type,
            name='Invalid Deposit Rate',
            slug='invalid-deposit-rate',
            base_price=Decimal('80.00'),
            deposit_required=True,
            deposit_percentage=None  # Jaramsız: deposit_required True bolǵanda kerek
        )
        try:
            invalid_deposit.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan deposit validation",
            passed
        )

        # Unikal constraint ti tekseriw
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
                slug='test-rate',  # Birdey slug
                base_price=Decimal('90.00')
            )
            duplicate.full_clean()
            passed = False
        except Exception:
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

    # 6-tekseriw: DateInventory model qáwipsizligi
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

        # booked_rooms validaciyasın tekseriw
        invalid_inventory = DateInventory(
            rate_plan=rate_plan,
            date=date(2024, 6, 16),
            available_rooms=3,
            booked_rooms=5  # Jaramsız: bos barınan kóp
        )
        try:
            invalid_inventory.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory booked_rooms validation",
            passed
        )

        # Turıw validaciyasın tekseriw
        invalid_stay = DateInventory(
            rate_plan=rate_plan,
            date=date(2024, 6, 17),
            available_rooms=5,
            booked_rooms=2,
            minimum_stay=7,
            maximum_stay=3  # Jaramsız: max < min
        )
        try:
            invalid_stay.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory stay validation",
            passed
        )

        # Unikal constraint ti tekseriw
        inventory = DateInventory.objects.create(
            rate_plan=rate_plan,
            date=date(2024, 6, 15),
            available_rooms=5,
            booked_rooms=0
        )

        try:
            duplicate = DateInventory(
                rate_plan=rate_plan,
                date=date(2024, 6, 15),  # Sol rate plan ushın birdey sana
                available_rooms=3
            )
            duplicate.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory unique constraint (rate_plan, date)",
            passed
        )

        # remaining_rooms qásiyetin tekseriw
        inventory.booked_rooms = 2
        inventory.save()
        passed = inventory.remaining_rooms == 3  # 5 - 2 = 3
        total_checks += 1
        passed_checks += print_security_check(
            "DateInventory remaining_rooms calculation",
            passed,
            f"Available: 5, Booked: 2, Remaining: {inventory.remaining_rooms}"
        )

        # is_available_for_booking metodın tekseriw
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

    # 7-tekseriw: CASCADE óshiriw qáwipsizligi
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

        # Baylanıslı obyektlerdi jaratıw
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

        # Xona túrin óshiriw hám cascade di tekseriw
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

    # 8-tekseriw: Database indeksleri
    print("\n8. Database Indexes")
    print("-" * 40)
    try:
        # RoomType indekslerin tekseriw
        room_type_indexes = RoomType._meta.indexes
        passed = len(room_type_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType database indexes",
            passed,
            f"Found {len(room_type_indexes)} indexes"
        )

        # RatePlan indekslerin tekseriw
        rate_plan_indexes = RatePlan._meta.indexes
        passed = len(rate_plan_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "RatePlan database indexes",
            passed,
            f"Found {len(rate_plan_indexes)} indexes"
        )

        # DateInventory indekslerin tekseriw
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

    # 9-tekseriw: Soft delete qáwipsizligi
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

        # Soft delete di testlew
        room_type.soft_delete()
        passed = room_type.is_deleted and room_type.deleted_at is not None
        total_checks += 1
        passed_checks += print_security_check(
            "RoomType soft delete functionality",
            passed
        )

        # Restore di testlew
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

    # 10-tekseriw: Baha validaciyası qáwipsizligi
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

        # Teris baha validaciyasın tekseriw
        invalid_price_room = RoomType(
            property=property,
            name='Invalid Price Room',
            slug='invalid-price-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('-10.00')  # Jaramsız: teris
        )
        try:
            invalid_price_room.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "RoomType negative price validation",
            passed
        )

        # RatePlan ushın teris bahanı tekseriw
        invalid_price_rate = RatePlan(
            room_type=room_type,
            name='Invalid Price Rate',
            slug='invalid-price-rate',
            base_price=Decimal('-10.00')  # Jaramsız: teris
        )
        try:
            invalid_price_rate.full_clean()
            passed = False
        except Exception:
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

    # Tazalaw
    amenity.delete()
    category.delete()
    property.delete()
    property_type.delete()
    user.delete()

    # Juwmaq
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
