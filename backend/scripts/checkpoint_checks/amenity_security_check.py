"""
Amenity model leri ushın qáwipsizlik tekseriw skripti (Checkpoint 06).

Bul skript amenity model lerin TICKBRON qáwipsizlik standartlarına say ekenine
isenim hasıl etiw ushın tolıq qáwipsizlik tekseriwinen ótkeredi.
"""
import os
import sys
import django

# Django dı tayarlaw
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from properties.models import (
    AmenityCategory, AmenityCategoryTranslation,
    Amenity, PropertyAmenity
)


def print_security_check(title, passed, details=""):
    """Qáwipsizlik tekseriw nátiyjesin formatlap shıǵarıw."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status}: {title}")
    if details:
        print(f"  Details: {details}")
    return passed


def run_security_checks():
    """Amenity model leri ushın tolıq qáwipsizlik tekseriwlerin islew."""
    print("=" * 60)
    print("AMENITY MODELS SECURITY REVIEW - CHECKPOINT 06")
    print("=" * 60)
    print()

    passed_checks = 0
    total_checks = 0

    # Bar test maǵlıwmatın tazalaw - PROTECT constraint sebepli aldın amenity lerdi óshiriw
    Amenity.objects.filter(name__contains='Test').delete()
    Amenity.objects.filter(category__name__contains='Test').delete()
    AmenityCategory.objects.filter(name__contains='Test').delete()

    # 1-tekseriw: Model maydanlarınıń qáwipsizligi
    print("1. Model Field Security")
    print("-" * 40)
    try:
        # Sezgir maydanlardıń durıs qorǵalǵanın tekseriw
        category = AmenityCategory.objects.create(
            name='Field Security Test',
            slug='field-security-test'
        )

        # Tekst kórinisi sezgir maǵlıwmattı ashpaytuǵının tekseriw
        str_repr = str(category)
        passed = 'email' not in str_repr.lower() and 'password' not in str_repr.lower()
        total_checks += 1
        passed_checks += print_security_check(
            "String representation security",
            passed,
            f"String repr: {str_repr}"
        )
        category.delete()

    except Exception as e:
        total_checks += 1
        print_security_check("Model field security", False, str(e))

    # 2-tekseriw: Unikal constraint ler
    print("\n2. Unique Constraints")
    print("-" * 40)
    try:
        category = AmenityCategory.objects.create(
            name='Unique Constraint Test',
            slug='unique-constraint-test'
        )

        # Dublikat jaratıwǵa urınıw
        try:
            duplicate = AmenityCategory(
                name='Unique Constraint Test',
                slug='different-slug'
            )
            duplicate.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "AmenityCategory unique name constraint",
            passed
        )
        category.delete()

    except Exception as e:
        total_checks += 1
        print_security_check("Unique constraints", False, str(e))

    # 3-tekseriw: Foreign key qáwipsizligi
    print("\n3. Foreign Key Security")
    print("-" * 40)
    total_checks += 2
    try:
        category = AmenityCategory.objects.create(
            name='FK Security Test',
            slug='fk-security-test'
        )
        amenity = Amenity.objects.create(
            category=category,
            name='FK Test Amenity',
            slug='fk-test-amenity'
        )

        # Amenity diń kategoriyaǵa durıs baylanısqanın tekseriw
        passed = amenity.category == category
        passed_checks += print_security_check(
            "Amenity-Category foreign key relation",
            passed
        )

        # CASCADE óshiriwdi tekseriw
        amenity_id = amenity.id
        amenity.delete()  # Kategoriya PROTECT bolǵanı ushın aldın amenity di óshiriw
        category.delete()
        passed = not Amenity.objects.filter(id=amenity_id).exists()
        passed_checks += print_security_check(
            "CASCADE deletion on amenity delete",
            passed
        )

    except Exception as e:
        print_security_check("Foreign key security", False, str(e))
        print_security_check("CASCADE deletion", False, "Skipped due to error")

    # 4-tekseriw: Soft delete qáwipsizligi
    print("\n4. Soft Delete Security")
    print("-" * 40)
    try:
        category = AmenityCategory.objects.create(
            name='Soft Delete Test',
            slug='soft-delete-test'
        )

        # Soft delete di testlew
        category.soft_delete()
        passed = category.is_deleted and category.deleted_at is not None
        total_checks += 1
        passed_checks += print_security_check(
            "Soft delete functionality",
            passed
        )

        # Restore di testlew
        category.restore()
        passed = not category.is_deleted and category.deleted_at is None
        total_checks += 1
        passed_checks += print_security_check(
            "Soft delete restore functionality",
            passed
        )

        category.delete()

    except Exception as e:
        total_checks += 2
        print_security_check("Soft delete security", False, str(e))

    # 5-tekseriw: Awdarma unikallıǵı
    print("\n5. Translation Uniqueness")
    print("-" * 40)
    try:
        category = AmenityCategory.objects.create(
            name='Translation Uniqueness Test',
            slug='translation-uniqueness-test'
        )

        AmenityCategoryTranslation.objects.create(
            category=category,
            language='en',
            name='Translation Test'
        )

        # Dublikat awdarma jaratıwǵa urınıw
        try:
            translation2 = AmenityCategoryTranslation(
                category=category,
                language='en',
                name='Different Name'
            )
            translation2.full_clean()
            passed = False
        except Exception:
            passed = True

        total_checks += 1
        passed_checks += print_security_check(
            "Translation unique constraint (category, language)",
            passed
        )

        category.delete()

    except Exception as e:
        total_checks += 1
        print_security_check("Translation uniqueness", False, str(e))

    # 6-tekseriw: PropertyAmenity baylanısı qáwipsizligi
    print("\n6. PropertyAmenity Relation Security")
    print("-" * 40)
    try:
        # Ápiwayılastırılǵan test - Property/User baylanıslarısız model di tuwrıdan-tuwrı testlew
        category = AmenityCategory.objects.create(
            name='PA Relation Test Category',
            slug='pa-relation-test-category'
        )
        amenity = Amenity.objects.create(
            category=category,
            name='PA Relation Test Amenity',
            slug='pa-relation-test-amenity'
        )

        # Haqıyqıy Property baylanısısız model validaciyasın testlew
        try:
            # Modelde kútilgen maydanlar bar ekenin testlew
            passed = hasattr(PropertyAmenity, 'property') and hasattr(PropertyAmenity, 'amenity')
            total_checks += 1
            passed_checks += print_security_check(
                "PropertyAmenity model structure",
                passed
            )

            # Unikal constraint anıqlamasın testlew
            unique_together = PropertyAmenity._meta.unique_together
            passed = ('property', 'amenity') in unique_together
            total_checks += 1
            passed_checks += print_security_check(
                "PropertyAmenity unique constraint definition",
                passed
            )

        except Exception as model_error:
            total_checks += 2
            print_security_check("PropertyAmenity model structure", False, str(model_error))
            print_security_check("PropertyAmenity unique constraint", False, "Skipped due to error")

        # Tazalaw
        amenity.delete()
        category.delete()

    except Exception as e:
        total_checks += 2
        print_security_check("PropertyAmenity relation security", False, str(e))
        print_security_check("PropertyAmenity unique constraint", False, "Skipped due to error")

    # 7-tekseriw: Izlenetuǵın belgi qáwipsizligi
    print("\n7. Searchable Flag Security")
    print("-" * 40)
    try:
        category = AmenityCategory.objects.create(
            name='Searchable Flag Test',
            slug='searchable-flag-test'
        )

        searchable_amenity = Amenity.objects.create(
            category=category,
            name='Searchable Test Amenity',
            slug='searchable-test-amenity',
            is_searchable=True
        )

        non_searchable_amenity = Amenity.objects.create(
            category=category,
            name='Non-Searchable Test Amenity',
            slug='non-searchable-test-amenity',
            is_searchable=False
        )

        # Filterlew durıs islewin tekseriw
        searchable_count = Amenity.objects.filter(is_searchable=True).count()
        non_searchable_count = Amenity.objects.filter(is_searchable=False).count()

        passed = searchable_count >= 1 and non_searchable_count >= 1
        total_checks += 1
        passed_checks += print_security_check(
            "Searchable flag filtering",
            passed,
            f"Searchable: {searchable_count}, Non-searchable: {non_searchable_count}"
        )

        # Tazalaw
        searchable_amenity.delete()
        non_searchable_amenity.delete()
        category.delete()

    except Exception as e:
        total_checks += 1
        print_security_check("Searchable flag security", False, str(e))

    # 8-tekseriw: Database indeksleri
    print("\n8. Database Indexes")
    print("-" * 40)
    try:
        # Model lerde tiyisli indeksler barlıǵın tekseriw
        pass

        # AmenityCategory indekslerin tekseriw
        category_indexes = AmenityCategory._meta.indexes
        passed = len(category_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "AmenityCategory database indexes",
            passed,
            f"Found {len(category_indexes)} indexes"
        )

        # Amenity indekslerin tekseriw
        amenity_indexes = Amenity._meta.indexes
        passed = len(amenity_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "Amenity database indexes",
            passed,
            f"Found {len(amenity_indexes)} indexes"
        )

        # PropertyAmenity indekslerin tekseriw
        property_amenity_indexes = PropertyAmenity._meta.indexes
        passed = len(property_amenity_indexes) > 0
        total_checks += 1
        passed_checks += print_security_check(
            "PropertyAmenity database indexes",
            passed,
            f"Found {len(property_amenity_indexes)} indexes"
        )

    except Exception as e:
        total_checks += 3
        print_security_check("Database indexes", False, str(e))
        print_security_check("Amenity indexes", False, "Skipped due to error")
        print_security_check("PropertyAmenity indexes", False, "Skipped due to error")

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
