"""
Tests for property models.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from datetime import date
from properties.models import (
    PropertyType, Property, PropertyTranslation, PropertyPolicy,
    AmenityCategory, AmenityCategoryTranslation, Amenity, AmenityTranslation, PropertyAmenity,
    PropertyPhoto, RoomType, RoomPhoto, RoomAmenity, RatePlan, DateInventory
)
from users.models import User


class PropertyTypeModelTest(TestCase):
    """Test cases for PropertyType model."""
    
    def setUp(self):
        """Set up test data."""
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment',
            description='A modern apartment',
            icon='🏢'
        )
    
    def test_property_type_creation(self):
        """Test PropertyType creation."""
        self.assertEqual(self.property_type.name, 'Apartment')
        self.assertEqual(self.property_type.slug, 'apartment')
        self.assertEqual(self.property_type.icon, '🏢')
        self.assertTrue(self.property_type.is_active)
    
    def test_property_type_str(self):
        """Test PropertyType string representation."""
        self.assertEqual(str(self.property_type), 'Apartment')
    
    def test_property_type_unique_name(self):
        """Test that PropertyType name must be unique."""
        with self.assertRaises(Exception):
            PropertyType.objects.create(
                name='Apartment',
                slug='apartment-different'
            )
    
    def test_property_type_unique_slug(self):
        """Test that PropertyType slug must be unique."""
        with self.assertRaises(Exception):
            PropertyType.objects.create(
                name='Different Apartment',
                slug='apartment'
            )
    
    def test_property_type_soft_delete(self):
        """Test PropertyType soft delete functionality."""
        self.property_type.soft_delete()
        self.assertTrue(self.property_type.is_deleted)
        self.assertIsNotNone(self.property_type.deleted_at)
    
    def test_property_type_restore(self):
        """Test PropertyType restore functionality."""
        self.property_type.soft_delete()
        self.property_type.restore()
        self.assertFalse(self.property_type.is_deleted)
        self.assertIsNone(self.property_type.deleted_at)


class PropertyModelTest(TestCase):
    """Test cases for Property model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            currency='USD'
        )
    
    def test_property_creation(self):
        """Test Property creation."""
        self.assertEqual(self.property.owner, self.user)
        self.assertEqual(self.property.property_type, self.property_type)
        self.assertEqual(self.property.status, 'draft')
        self.assertEqual(self.property.max_guests, 4)
        self.assertEqual(self.property.city, 'Tashkent')
        self.assertEqual(self.property.country, 'Uzbekistan')
        self.assertEqual(self.property.base_price, Decimal('100.00'))
    
    def test_property_str(self):
        """Test Property string representation."""
        expected = f"Property {self.property.id} - Tashkent, Uzbekistan"
        self.assertEqual(str(self.property), expected)
    
    def test_property_status_choices(self):
        """Test Property status field choices."""
        valid_statuses = ['draft', 'pending_approval', 'active', 'suspended', 'rejected']
        for status in valid_statuses:
            property = Property.objects.create(
                owner=self.user,
                property_type=self.property_type,
                status=status,
                max_guests=2,
                address_line1='Test Address',
                city='Test City',
                country='Test Country',
                base_price=Decimal('50.00')
            )
            self.assertEqual(property.status, status)
    
    def test_property_max_guests_validation(self):
        """Test Property max_guests validation."""
        # Test minimum value
        with self.assertRaises(ValidationError):
            property = Property(
                owner=self.user,
                property_type=self.property_type,
                max_guests=0,  # Invalid
                address_line1='Test Address',
                city='Test City',
                country='Test Country',
                base_price=Decimal('50.00')
            )
            property.full_clean()
        
        # Test maximum value
        with self.assertRaises(ValidationError):
            property = Property(
                owner=self.user,
                property_type=self.property_type,
                max_guests=51,  # Invalid
                address_line1='Test Address',
                city='Test City',
                country='Test Country',
                base_price=Decimal('50.00')
            )
            property.full_clean()
    
    def test_property_bedrooms_validation(self):
        """Test Property bedrooms validation."""
        # Test minimum value
        with self.assertRaises(ValidationError):
            property = Property(
                owner=self.user,
                property_type=self.property_type,
                max_guests=2,
                bedrooms=-1,  # Invalid
                address_line1='Test Address',
                city='Test City',
                country='Test Country',
                base_price=Decimal('50.00')
            )
            property.full_clean()
    
    def test_property_latitude_validation(self):
        """Test Property latitude validation."""
        # Test valid latitude
        self.property.latitude = Decimal('45.0')
        self.property.save()
        self.assertEqual(self.property.latitude, Decimal('45.0'))
        
        # Test invalid latitude (too high)
        with self.assertRaises(ValidationError):
            self.property.latitude = Decimal('91.0')
            self.property.full_clean()
        
        # Test invalid latitude (too low)
        with self.assertRaises(ValidationError):
            self.property.latitude = Decimal('-91.0')
            self.property.full_clean()
    
    def test_property_longitude_validation(self):
        """Test Property longitude validation."""
        # Test valid longitude
        self.property.longitude = Decimal('120.0')
        self.property.save()
        self.assertEqual(self.property.longitude, Decimal('120.0'))
        
        # Test invalid longitude (too high)
        with self.assertRaises(ValidationError):
            self.property.longitude = Decimal('181.0')
            self.property.full_clean()
        
        # Test invalid longitude (too low)
        with self.assertRaises(ValidationError):
            self.property.longitude = Decimal('-181.0')
            self.property.full_clean()
    
    def test_property_base_price_validation(self):
        """Test Property base_price validation."""
        # Test negative price
        with self.assertRaises(ValidationError):
            property = Property(
                owner=self.user,
                property_type=self.property_type,
                max_guests=2,
                address_line1='Test Address',
                city='Test City',
                country='Test Country',
                base_price=Decimal('-10.00')  # Invalid
            )
            property.full_clean()
    
    def test_property_get_full_address(self):
        """Test Property get_full_address method."""
        self.property.address_line2 = 'Apt 4B'
        self.property.state = 'Tashkent Region'
        self.property.postal_code = '100000'
        self.property.save()
        
        full_address = self.property.get_full_address()
        expected = '123 Main Street, Apt 4B, Tashkent, Tashkent Region, 100000, Uzbekistan'
        self.assertEqual(full_address, expected)
    
    def test_property_ownership_relation(self):
        """Test Property ownership relation."""
        self.assertEqual(self.property.owner, self.user)
        self.assertIn(self.property, self.user.properties.all())
    
    def test_property_type_relation(self):
        """Test Property type relation."""
        self.assertEqual(self.property.property_type, self.property_type)
        self.assertIn(self.property, self.property_type.properties.all())
    
    def test_property_soft_delete(self):
        """Test Property soft delete functionality."""
        self.property.soft_delete()
        self.assertTrue(self.property.is_deleted)
        self.assertIsNotNone(self.property.deleted_at)
    
    def test_property_restore(self):
        """Test Property restore functionality."""
        self.property.soft_delete()
        self.property.restore()
        self.assertFalse(self.property.is_deleted)
        self.assertIsNone(self.property.deleted_at)
    
    def test_property_default_boolean_fields(self):
        """Test Property default boolean field values."""
        self.assertFalse(self.property.has_elevator)
        self.assertFalse(self.property.has_parking)
        self.assertFalse(self.property.has_wifi)
        self.assertFalse(self.property.has_ac)
        self.assertFalse(self.property.has_heating)


class PropertyTranslationModelTest(TestCase):
    """Test cases for PropertyTranslation model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.translation = PropertyTranslation.objects.create(
            property=self.property,
            language='en',
            name='Beautiful Apartment',
            description='A beautiful apartment in the city center'
        )
    
    def test_translation_creation(self):
        """Test PropertyTranslation creation."""
        self.assertEqual(self.translation.property, self.property)
        self.assertEqual(self.translation.language, 'en')
        self.assertEqual(self.translation.name, 'Beautiful Apartment')
    
    def test_translation_str(self):
        """Test PropertyTranslation string representation."""
        expected = f"{self.property.id} - en: Beautiful Apartment"
        self.assertEqual(str(self.translation), expected)
    
    def test_translation_language_choices(self):
        """Test PropertyTranslation language field choices."""
        valid_languages = ['en', 'ru', 'uz']
        for language in valid_languages:
            # Create a new property for each language to avoid unique constraint violation
            new_property = Property.objects.create(
                owner=self.user,
                property_type=self.property_type,
                max_guests=2,
                address_line1='Test Address',
                city='Test City',
                country='Test Country',
                base_price=Decimal('50.00')
            )
            translation = PropertyTranslation.objects.create(
                property=new_property,
                language=language,
                name=f'Test Name {language}',
                description=f'Test description {language}'
            )
            self.assertEqual(translation.language, language)
    
    def test_translation_unique_constraint(self):
        """Test PropertyTranslation unique constraint on property and language."""
        # Creating duplicate translation for same property and language should fail
        with self.assertRaises(Exception):
            PropertyTranslation.objects.create(
                property=self.property,
                language='en',  # Same language as existing translation
                name='Another Name',
                description='Another description'
            )
    
    def test_translation_multiple_languages(self):
        """Test that a property can have translations in multiple languages."""
        russian_translation = PropertyTranslation.objects.create(
            property=self.property,
            language='ru',
            name='Красивая квартира',
            description='Красивая квартира в центре города'
        )
        uzbek_translation = PropertyTranslation.objects.create(
            property=self.property,
            language='uz',
            name='Chiroyli kvartira',
            description='Shahar markazidagi chiroyli kvartira'
        )
        
        self.assertEqual(self.property.translations.count(), 3)  # en, ru, uz
        self.assertIn(self.translation, self.property.translations.all())
        self.assertIn(russian_translation, self.property.translations.all())
        self.assertIn(uzbek_translation, self.property.translations.all())
    
    def test_translation_relation(self):
        """Test PropertyTranslation relation to Property."""
        self.assertEqual(self.translation.property, self.property)
        self.assertIn(self.translation, self.property.translations.all())
    
    def test_translation_soft_delete(self):
        """Test PropertyTranslation soft delete functionality."""
        self.translation.soft_delete()
        self.assertTrue(self.translation.is_deleted)
        self.assertIsNotNone(self.translation.deleted_at)


class PropertyPolicyModelTest(TestCase):
    """Test cases for PropertyPolicy model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.policy = PropertyPolicy.objects.create(
            property=self.property,
            policy_type='check_in',
            title='Check-in Policy',
            description='Check-in is available from 2:00 PM to 10:00 PM'
        )
    
    def test_policy_creation(self):
        """Test PropertyPolicy creation."""
        self.assertEqual(self.policy.property, self.property)
        self.assertEqual(self.policy.policy_type, 'check_in')
        self.assertEqual(self.policy.title, 'Check-in Policy')
        self.assertFalse(self.policy.is_strict)
    
    def test_policy_str(self):
        """Test PropertyPolicy string representation."""
        expected = f"{self.property.id} - Check-in Policy"
        self.assertEqual(str(self.policy), expected)
    
    def test_policy_type_choices(self):
        """Test PropertyPolicy policy_type field choices."""
        valid_types = [
            'check_in', 'check_out', 'cancellation', 'children',
            'pets', 'smoking', 'age_restriction', 'payment', 'house_rules'
        ]
        for policy_type in valid_types:
            # Create a new property for each policy type to avoid unique constraint violation
            new_property = Property.objects.create(
                owner=self.user,
                property_type=self.property_type,
                max_guests=2,
                address_line1='Test Address',
                city='Test City',
                country='Test Country',
                base_price=Decimal('50.00')
            )
            policy = PropertyPolicy.objects.create(
                property=new_property,
                policy_type=policy_type,
                title=f'{policy_type.title()} Policy',
                description=f'Test {policy_type} policy'
            )
            self.assertEqual(policy.policy_type, policy_type)
    
    def test_policy_unique_constraint(self):
        """Test PropertyPolicy unique constraint on property and policy_type."""
        # Creating duplicate policy type for same property should fail
        with self.assertRaises(Exception):
            PropertyPolicy.objects.create(
                property=self.property,
                policy_type='check_in',  # Same policy type as existing
                title='Another Check-in Policy',
                description='Another check-in policy'
            )
    
    def test_policy_multiple_policies(self):
        """Test that a property can have multiple policies."""
        checkout_policy = PropertyPolicy.objects.create(
            property=self.property,
            policy_type='check_out',
            title='Check-out Policy',
            description='Check-out is until 11:00 AM'
        )
        cancellation_policy = PropertyPolicy.objects.create(
            property=self.property,
            policy_type='cancellation',
            title='Cancellation Policy',
            description='Free cancellation up to 24 hours before check-in'
        )
        
        self.assertEqual(self.property.policies.count(), 3)  # check_in, check_out, cancellation
        self.assertIn(self.policy, self.property.policies.all())
        self.assertIn(checkout_policy, self.property.policies.all())
        self.assertIn(cancellation_policy, self.property.policies.all())
    
    def test_policy_strict_flag(self):
        """Test PropertyPolicy is_strict flag."""
        strict_policy = PropertyPolicy.objects.create(
            property=self.property,
            policy_type='smoking',
            title='No Smoking Policy',
            description='Smoking is strictly prohibited',
            is_strict=True
        )
        self.assertTrue(strict_policy.is_strict)
    
    def test_policy_relation(self):
        """Test PropertyPolicy relation to Property."""
        self.assertEqual(self.policy.property, self.property)
        self.assertIn(self.policy, self.property.policies.all())
    
    def test_policy_soft_delete(self):
        """Test PropertyPolicy soft delete functionality."""
        self.policy.soft_delete()
        self.assertTrue(self.policy.is_deleted)
        self.assertIsNotNone(self.policy.deleted_at)


class PropertyModelIntegrationTest(TestCase):
    """Integration tests for property models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
    
    def test_complete_property_workflow(self):
        """Test complete property creation with translations and policies."""
        # Create property
        property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            bedrooms=2,
            bathrooms=1,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00'),
            currency='USD'
        )
        
        # Add translations
        en_translation = PropertyTranslation.objects.create(
            property=property,
            language='en',
            name='Beautiful Apartment',
            description='A beautiful apartment in the city center'
        )
        ru_translation = PropertyTranslation.objects.create(
            property=property,
            language='ru',
            name='Красивая квартира',
            description='Красивая квартира в центре города'
        )
        
        # Add policies
        checkin_policy = PropertyPolicy.objects.create(
            property=property,
            policy_type='check_in',
            title='Check-in Policy',
            description='Check-in from 2:00 PM'
        )
        checkout_policy = PropertyPolicy.objects.create(
            property=property,
            policy_type='check_out',
            title='Check-out Policy',
            description='Check-out until 11:00 AM'
        )
        
        # Verify all relations
        self.assertEqual(property.translations.count(), 2)
        self.assertEqual(property.policies.count(), 2)
        self.assertIn(en_translation, property.translations.all())
        self.assertIn(ru_translation, property.translations.all())
        self.assertIn(checkin_policy, property.policies.all())
        self.assertIn(checkout_policy, property.policies.all())
        
        # Verify ownership
        self.assertEqual(property.owner, self.user)
        self.assertIn(property, self.user.properties.all())
        
        # Verify property type
        self.assertEqual(property.property_type, self.property_type)
        self.assertIn(property, self.property_type.properties.all())
    
    def test_property_deletion_cascade(self):
        """Test that deleting a property cascades to translations and policies."""
        property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
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
        
        # Delete property
        property.delete()
        
        # Verify cascade deletion
        self.assertFalse(PropertyTranslation.objects.filter(id=translation.id).exists())
        self.assertFalse(PropertyPolicy.objects.filter(id=policy.id).exists())
    
    def test_property_status_workflow(self):
        """Test property status workflow from draft to active."""
        property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            status='draft',
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        
        # Draft -> Pending Approval
        property.status = 'pending_approval'
        property.save()
        self.assertEqual(property.status, 'pending_approval')
        
        # Pending Approval -> Active
        property.status = 'active'
        property.approved_at = timezone.now()
        property.approved_by = self.user
        property.save()
        self.assertEqual(property.status, 'active')
        self.assertIsNotNone(property.approved_at)
        self.assertEqual(property.approved_by, self.user)


class AmenityCategoryModelTest(TestCase):
    """Test cases for AmenityCategory model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen',
            description='Kitchen amenities',
            icon='🍳',
            sort_order=1
        )
    
    def test_amenity_category_creation(self):
        """Test AmenityCategory creation."""
        self.assertEqual(self.category.name, 'Kitchen')
        self.assertEqual(self.category.slug, 'kitchen')
        self.assertEqual(self.category.icon, '🍳')
        self.assertEqual(self.category.sort_order, 1)
        self.assertTrue(self.category.is_active)
    
    def test_amenity_category_str(self):
        """Test AmenityCategory string representation."""
        self.assertEqual(str(self.category), 'Kitchen')
    
    def test_amenity_category_unique_name(self):
        """Test that AmenityCategory name must be unique."""
        with self.assertRaises(Exception):
            AmenityCategory.objects.create(
                name='Kitchen',
                slug='kitchen-different'
            )
    
    def test_amenity_category_unique_slug(self):
        """Test that AmenityCategory slug must be unique."""
        with self.assertRaises(Exception):
            AmenityCategory.objects.create(
                name='Different Kitchen',
                slug='kitchen'
            )
    
    def test_amenity_category_sort_order(self):
        """Test AmenityCategory sort ordering."""
        category2 = AmenityCategory.objects.create(
            name='Bathroom',
            slug='bathroom',
            sort_order=2
        )
        category3 = AmenityCategory.objects.create(
            name='Entertainment',
            slug='entertainment',
            sort_order=0
        )
        
        categories = list(AmenityCategory.objects.all())
        self.assertEqual(categories[0], category3)  # sort_order=0
        self.assertEqual(categories[1], self.category)  # sort_order=1
        self.assertEqual(categories[2], category2)  # sort_order=2
    
    def test_amenity_category_soft_delete(self):
        """Test AmenityCategory soft delete functionality."""
        self.category.soft_delete()
        self.assertTrue(self.category.is_deleted)
        self.assertIsNotNone(self.category.deleted_at)
    
    def test_amenity_category_restore(self):
        """Test AmenityCategory restore functionality."""
        self.category.soft_delete()
        self.category.restore()
        self.assertFalse(self.category.is_deleted)
        self.assertIsNone(self.category.deleted_at)


class AmenityCategoryTranslationModelTest(TestCase):
    """Test cases for AmenityCategoryTranslation model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        self.translation = AmenityCategoryTranslation.objects.create(
            category=self.category,
            language='en',
            name='Kitchen',
            description='Kitchen amenities'
        )
    
    def test_translation_creation(self):
        """Test AmenityCategoryTranslation creation."""
        self.assertEqual(self.translation.category, self.category)
        self.assertEqual(self.translation.language, 'en')
        self.assertEqual(self.translation.name, 'Kitchen')
    
    def test_translation_str(self):
        """Test AmenityCategoryTranslation string representation."""
        expected = f"{self.category.name} - en: Kitchen"
        self.assertEqual(str(self.translation), expected)
    
    def test_translation_language_choices(self):
        """Test AmenityCategoryTranslation language field choices."""
        valid_languages = ['en', 'ru', 'uz']
        for language in valid_languages:
            # Create a new category for each language to avoid unique constraint violation
            new_category = AmenityCategory.objects.create(
                name=f'Category {language}',
                slug=f'category-{language}'
            )
            translation = AmenityCategoryTranslation.objects.create(
                category=new_category,
                language=language,
                name=f'Category Name {language}',
                description=f'Description {language}'
            )
            self.assertEqual(translation.language, language)
    
    def test_translation_unique_constraint(self):
        """Test AmenityCategoryTranslation unique constraint on category and language."""
        with self.assertRaises(Exception):
            AmenityCategoryTranslation.objects.create(
                category=self.category,
                language='en',  # Same language as existing translation
                name='Another Name',
                description='Another description'
            )
    
    def test_translation_multiple_languages(self):
        """Test that a category can have translations in multiple languages."""
        russian_translation = AmenityCategoryTranslation.objects.create(
            category=self.category,
            language='ru',
            name='Кухня',
            description='Кухонные удобства'
        )
        uzbek_translation = AmenityCategoryTranslation.objects.create(
            category=self.category,
            language='uz',
            name='Oshxona',
            description='Oshxona qulayliklari'
        )
        
        self.assertEqual(self.category.translations.count(), 3)  # en, ru, uz
        self.assertIn(self.translation, self.category.translations.all())
        self.assertIn(russian_translation, self.category.translations.all())
        self.assertIn(uzbek_translation, self.category.translations.all())
    
    def test_translation_relation(self):
        """Test AmenityCategoryTranslation relation to AmenityCategory."""
        self.assertEqual(self.translation.category, self.category)
        self.assertIn(self.translation, self.category.translations.all())
    
    def test_translation_soft_delete(self):
        """Test AmenityCategoryTranslation soft delete functionality."""
        self.translation.soft_delete()
        self.assertTrue(self.translation.is_deleted)
        self.assertIsNotNone(self.translation.deleted_at)


class AmenityModelTest(TestCase):
    """Test cases for Amenity model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        self.amenity = Amenity.objects.create(
            category=self.category,
            name='Microwave',
            slug='microwave',
            description='Microwave oven',
            icon='🧊',
            is_searchable=True,
            sort_order=1
        )
    
    def test_amenity_creation(self):
        """Test Amenity creation."""
        self.assertEqual(self.amenity.category, self.category)
        self.assertEqual(self.amenity.name, 'Microwave')
        self.assertEqual(self.amenity.slug, 'microwave')
        self.assertEqual(self.amenity.icon, '🧊')
        self.assertTrue(self.amenity.is_searchable)
        self.assertEqual(self.amenity.sort_order, 1)
    
    def test_amenity_str(self):
        """Test Amenity string representation."""
        expected = f"{self.category.name} - {self.amenity.name}"
        self.assertEqual(str(self.amenity), expected)
    
    def test_amenity_unique_name(self):
        """Test that Amenity name must be unique."""
        with self.assertRaises(Exception):
            Amenity.objects.create(
                category=self.category,
                name='Microwave',
                slug='microwave-different'
            )
    
    def test_amenity_unique_slug(self):
        """Test that Amenity slug must be unique."""
        with self.assertRaises(Exception):
            Amenity.objects.create(
                category=self.category,
                name='Different Microwave',
                slug='microwave'
            )
    
    def test_amenity_is_searchable(self):
        """Test Amenity is_searchable field."""
        searchable_amenity = Amenity.objects.create(
            category=self.category,
            name='Oven',
            slug='oven',
            is_searchable=True
        )
        non_searchable_amenity = Amenity.objects.create(
            category=self.category,
            name='Secret Feature',
            slug='secret-feature',
            is_searchable=False
        )
        
        self.assertTrue(searchable_amenity.is_searchable)
        self.assertFalse(non_searchable_amenity.is_searchable)
    
    def test_amenity_sort_order(self):
        """Test Amenity sort ordering within category."""
        amenity2 = Amenity.objects.create(
            category=self.category,
            name='Refrigerator',
            slug='refrigerator',
            sort_order=2
        )
        amenity3 = Amenity.objects.create(
            category=self.category,
            name='Dishwasher',
            slug='dishwasher',
            sort_order=0
        )
        
        amenities = list(Amenity.objects.filter(category=self.category))
        self.assertEqual(amenities[0], amenity3)  # sort_order=0
        self.assertEqual(amenities[1], self.amenity)  # sort_order=1
        self.assertEqual(amenities[2], amenity2)  # sort_order=2
    
    def test_amenity_category_relation(self):
        """Test Amenity relation to AmenityCategory."""
        self.assertEqual(self.amenity.category, self.category)
        self.assertIn(self.amenity, self.category.amenities.all())
    
    def test_amenity_soft_delete(self):
        """Test Amenity soft delete functionality."""
        self.amenity.soft_delete()
        self.assertTrue(self.amenity.is_deleted)
        self.assertIsNotNone(self.amenity.deleted_at)
    
    def test_amenity_restore(self):
        """Test Amenity restore functionality."""
        self.amenity.soft_delete()
        self.amenity.restore()
        self.assertFalse(self.amenity.is_deleted)
        self.assertIsNone(self.amenity.deleted_at)


class AmenityTranslationModelTest(TestCase):
    """Test cases for AmenityTranslation model."""
    
    def setUp(self):
        """Set up test data."""
        self.category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        self.amenity = Amenity.objects.create(
            category=self.category,
            name='Microwave',
            slug='microwave'
        )
        self.translation = AmenityTranslation.objects.create(
            amenity=self.amenity,
            language='en',
            name='Microwave',
            description='Microwave oven'
        )
    
    def test_translation_creation(self):
        """Test AmenityTranslation creation."""
        self.assertEqual(self.translation.amenity, self.amenity)
        self.assertEqual(self.translation.language, 'en')
        self.assertEqual(self.translation.name, 'Microwave')
    
    def test_translation_str(self):
        """Test AmenityTranslation string representation."""
        expected = f"{self.amenity.name} - en: Microwave"
        self.assertEqual(str(self.translation), expected)
    
    def test_translation_language_choices(self):
        """Test AmenityTranslation language field choices."""
        valid_languages = ['en', 'ru', 'uz']
        for language in valid_languages:
            # Create a new amenity for each language to avoid unique constraint violation
            new_amenity = Amenity.objects.create(
                category=self.category,
                name=f'Amenity {language}',
                slug=f'amenity-{language}'
            )
            translation = AmenityTranslation.objects.create(
                amenity=new_amenity,
                language=language,
                name=f'Amenity Name {language}',
                description=f'Description {language}'
            )
            self.assertEqual(translation.language, language)
    
    def test_translation_unique_constraint(self):
        """Test AmenityTranslation unique constraint on amenity and language."""
        with self.assertRaises(Exception):
            AmenityTranslation.objects.create(
                amenity=self.amenity,
                language='en',  # Same language as existing translation
                name='Another Name',
                description='Another description'
            )
    
    def test_translation_multiple_languages(self):
        """Test that an amenity can have translations in multiple languages."""
        russian_translation = AmenityTranslation.objects.create(
            amenity=self.amenity,
            language='ru',
            name='Микроволновка',
            description='Микроволновая печь'
        )
        uzbek_translation = AmenityTranslation.objects.create(
            amenity=self.amenity,
            language='uz',
            name='Mikroto\'lqin',
            description='Mikroto\'lqin pech'
        )
        
        self.assertEqual(self.amenity.translations.count(), 3)  # en, ru, uz
        self.assertIn(self.translation, self.amenity.translations.all())
        self.assertIn(russian_translation, self.amenity.translations.all())
        self.assertIn(uzbek_translation, self.amenity.translations.all())
    
    def test_translation_relation(self):
        """Test AmenityTranslation relation to Amenity."""
        self.assertEqual(self.translation.amenity, self.amenity)
        self.assertIn(self.translation, self.amenity.translations.all())
    
    def test_translation_soft_delete(self):
        """Test AmenityTranslation soft delete functionality."""
        self.translation.soft_delete()
        self.assertTrue(self.translation.is_deleted)
        self.assertIsNotNone(self.translation.deleted_at)


class PropertyAmenityModelTest(TestCase):
    """Test cases for PropertyAmenity model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        self.amenity = Amenity.objects.create(
            category=self.category,
            name='Microwave',
            slug='microwave'
        )
        self.property_amenity = PropertyAmenity.objects.create(
            property=self.property,
            amenity=self.amenity,
            is_available=True,
            notes='Brand new microwave'
        )
    
    def test_property_amenity_creation(self):
        """Test PropertyAmenity creation."""
        self.assertEqual(self.property_amenity.property, self.property)
        self.assertEqual(self.property_amenity.amenity, self.amenity)
        self.assertTrue(self.property_amenity.is_available)
        self.assertEqual(self.property_amenity.notes, 'Brand new microwave')
    
    def test_property_amenity_str(self):
        """Test PropertyAmenity string representation."""
        expected = f"{self.property.id} - {self.amenity.name} (Available)"
        self.assertEqual(str(self.property_amenity), expected)
    
    def test_property_amenity_unique_constraint(self):
        """Test PropertyAmenity unique constraint on property and amenity."""
        with self.assertRaises(Exception):
            PropertyAmenity.objects.create(
                property=self.property,
                amenity=self.amenity,  # Same amenity for same property
                is_available=False
            )
    
    def test_property_amenity_is_available(self):
        """Test PropertyAmenity is_available field."""
        available_amenity = PropertyAmenity.objects.create(
            property=self.property,
            amenity=Amenity.objects.create(
                category=self.category,
                name='Oven',
                slug='oven'
            ),
            is_available=True
        )
        unavailable_amenity = PropertyAmenity.objects.create(
            property=self.property,
            amenity=Amenity.objects.create(
                category=self.category,
                name='Dishwasher',
                slug='dishwasher'
            ),
            is_available=False
        )
        
        self.assertTrue(available_amenity.is_available)
        self.assertFalse(unavailable_amenity.is_available)
    
    def test_property_amenity_notes(self):
        """Test PropertyAmenity notes field."""
        property_amenity_with_notes = PropertyAmenity.objects.create(
            property=self.property,
            amenity=Amenity.objects.create(
                category=self.category,
                name='Refrigerator',
                slug='refrigerator'
            ),
            notes='Large capacity refrigerator'
        )
        self.assertEqual(property_amenity_with_notes.notes, 'Large capacity refrigerator')
    
    def test_property_amenity_property_relation(self):
        """Test PropertyAmenity relation to Property."""
        self.assertEqual(self.property_amenity.property, self.property)
        self.assertIn(self.property_amenity, self.property.property_amenities.all())
    
    def test_property_amenity_amenity_relation(self):
        """Test PropertyAmenity relation to Amenity."""
        self.assertEqual(self.property_amenity.amenity, self.amenity)
        self.assertIn(self.property_amenity, self.amenity.property_amenities.all())
    
    def test_property_amenity_soft_delete(self):
        """Test PropertyAmenity soft delete functionality."""
        self.property_amenity.soft_delete()
        self.assertTrue(self.property_amenity.is_deleted)
        self.assertIsNotNone(self.property_amenity.deleted_at)
    
    def test_property_amenity_multiple_amenities(self):
        """Test that a property can have multiple amenities."""
        amenity2 = Amenity.objects.create(
            category=self.category,
            name='Oven',
            slug='oven'
        )
        amenity3 = Amenity.objects.create(
            category=self.category,
            name='Refrigerator',
            slug='refrigerator'
        )
        
        property_amenity2 = PropertyAmenity.objects.create(
            property=self.property,
            amenity=amenity2
        )
        property_amenity3 = PropertyAmenity.objects.create(
            property=self.property,
            amenity=amenity3
        )
        
        self.assertEqual(self.property.property_amenities.count(), 3)
        self.assertIn(self.property_amenity, self.property.property_amenities.all())
        self.assertIn(property_amenity2, self.property.property_amenities.all())
        self.assertIn(property_amenity3, self.property.property_amenities.all())
    
    def test_property_amenity_cascade_deletion(self):
        """Test that deleting a property cascades to property amenities."""
        property_amenity_id = self.property_amenity.id
        
        # Delete property
        self.property.delete()
        
        # Verify cascade deletion
        self.assertFalse(PropertyAmenity.objects.filter(id=property_amenity_id).exists())
    
    def test_property_amenity_amenity_cascade_deletion(self):
        """Test that deleting an amenity cascades to property amenities."""
        property_amenity_id = self.property_amenity.id
        
        # Delete amenity
        self.amenity.delete()
        
        # Verify cascade deletion
        self.assertFalse(PropertyAmenity.objects.filter(id=property_amenity_id).exists())


class AmenityModelIntegrationTest(TestCase):
    """Integration tests for amenity models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
    
    def test_complete_amenity_workflow(self):
        """Test complete amenity workflow with translations and property relations."""
        # Create amenity category
        category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen',
            description='Kitchen amenities',
            icon='🍳'
        )
        
        # Add category translations
        category_translation_en = AmenityCategoryTranslation.objects.create(
            category=category,
            language='en',
            name='Kitchen',
            description='Kitchen amenities'
        )
        category_translation_ru = AmenityCategoryTranslation.objects.create(
            category=category,
            language='ru',
            name='Кухня',
            description='Кухонные удобства'
        )
        
        # Create amenity
        amenity = Amenity.objects.create(
            category=category,
            name='Microwave',
            slug='microwave',
            description='Microwave oven',
            icon='🧊',
            is_searchable=True
        )
        
        # Add amenity translations
        amenity_translation_en = AmenityTranslation.objects.create(
            amenity=amenity,
            language='en',
            name='Microwave',
            description='Microwave oven'
        )
        amenity_translation_ru = AmenityTranslation.objects.create(
            amenity=amenity,
            language='ru',
            name='Микроволновка',
            description='Микроволновая печь'
        )
        
        # Link amenity to property
        property_amenity = PropertyAmenity.objects.create(
            property=self.property,
            amenity=amenity,
            is_available=True,
            notes='Brand new microwave'
        )
        
        # Verify all relations
        self.assertEqual(category.translations.count(), 2)
        self.assertEqual(amenity.translations.count(), 2)
        self.assertEqual(self.property.property_amenities.count(), 1)
        
        self.assertIn(category_translation_en, category.translations.all())
        self.assertIn(category_translation_ru, category.translations.all())
        self.assertIn(amenity_translation_en, amenity.translations.all())
        self.assertIn(amenity_translation_ru, amenity.translations.all())
        self.assertIn(property_amenity, self.property.property_amenities.all())
        
        # Verify category-amenity relation
        self.assertEqual(amenity.category, category)
        self.assertIn(amenity, category.amenities.all())
        
        # Verify property-amenity relation
        self.assertEqual(property_amenity.property, self.property)
        self.assertEqual(property_amenity.amenity, amenity)
    
    def test_searchable_amenities_filter(self):
        """Test filtering searchable amenities."""
        category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        
        searchable_amenity = Amenity.objects.create(
            category=category,
            name='Microwave',
            slug='microwave',
            is_searchable=True
        )
        non_searchable_amenity = Amenity.objects.create(
            category=category,
            name='Secret Feature',
            slug='secret-feature',
            is_searchable=False
        )
        
        # Filter searchable amenities
        searchable_amenities = Amenity.objects.filter(is_searchable=True)
        self.assertIn(searchable_amenity, searchable_amenities)
        self.assertNotIn(non_searchable_amenity, searchable_amenities)
        
        # Filter non-searchable amenities
        non_searchable_amenities = Amenity.objects.filter(is_searchable=False)
        self.assertIn(non_searchable_amenity, non_searchable_amenities)
        self.assertNotIn(searchable_amenity, non_searchable_amenities)
    
    def test_available_property_amenities_filter(self):
        """Test filtering available property amenities."""
        category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        
        amenity1 = Amenity.objects.create(
            category=category,
            name='Microwave',
            slug='microwave'
        )
        amenity2 = Amenity.objects.create(
            category=category,
            name='Oven',
            slug='oven'
        )
        
        available_amenity = PropertyAmenity.objects.create(
            property=self.property,
            amenity=amenity1,
            is_available=True
        )
        unavailable_amenity = PropertyAmenity.objects.create(
            property=self.property,
            amenity=amenity2,
            is_available=False
        )
        
        # Filter available property amenities
        available_amenities = PropertyAmenity.objects.filter(is_available=True)
        self.assertIn(available_amenity, available_amenities)
        self.assertNotIn(unavailable_amenity, available_amenities)
        
        # Filter unavailable property amenities
        unavailable_amenities = PropertyAmenity.objects.filter(is_available=False)
        self.assertIn(unavailable_amenity, unavailable_amenities)
        self.assertNotIn(available_amenity, unavailable_amenities)


class PropertyPhotoModelTest(TestCase):
    """Test cases for PropertyPhoto model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        # Create a mock image file for testing
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.image = SimpleUploadedFile(
            name='test_photo.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
    
    def test_property_photo_creation(self):
        """Test PropertyPhoto creation."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            photo_type='exterior',
            caption='Beautiful exterior view',
            is_primary=True,
            display_order=1,
            alt_text='Exterior photo of the property'
        )
        self.assertEqual(photo.property, self.property)
        self.assertEqual(photo.photo_type, 'exterior')
        self.assertEqual(photo.caption, 'Beautiful exterior view')
        self.assertTrue(photo.is_primary)
        self.assertEqual(photo.display_order, 1)
        self.assertEqual(photo.alt_text, 'Exterior photo of the property')
    
    def test_property_photo_str(self):
        """Test PropertyPhoto string representation."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            photo_type='interior'
        )
        expected = f"Photo {photo.id} - Property {self.property.id} (Interior)"
        self.assertEqual(str(photo), expected)
    
    def test_property_photo_type_choices(self):
        """Test PropertyPhoto photo_type field choices."""
        valid_types = ['exterior', 'interior', 'amenity', 'room', 'other']
        for photo_type in valid_types:
            photo = PropertyPhoto.objects.create(
                property=self.property,
                photo=self.image,
                photo_type=photo_type
            )
            self.assertEqual(photo.photo_type, photo_type)
    
    def test_property_photo_primary_constraint(self):
        """Test that only one primary photo is allowed per property."""
        # Create first primary photo
        primary_photo1 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            is_primary=True
        )
        
        # Create second photo as primary - should make first one non-primary
        primary_photo2 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            is_primary=True
        )
        
        # Refresh from database
        primary_photo1.refresh_from_db()
        primary_photo2.refresh_from_db()
        
        # Only the second should be primary
        self.assertFalse(primary_photo1.is_primary)
        self.assertTrue(primary_photo2.is_primary)
    
    def test_property_photo_display_order(self):
        """Test PropertyPhoto display ordering."""
        photo1 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            display_order=2
        )
        photo2 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            display_order=0
        )
        photo3 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            display_order=1
        )
        
        photos = list(PropertyPhoto.objects.filter(property=self.property))
        self.assertEqual(photos[0], photo2)  # display_order=0
        self.assertEqual(photos[1], photo3)  # display_order=1
        self.assertEqual(photos[2], photo1)  # display_order=2
    
    def test_property_photo_validation_invalid_file_type(self):
        """Test PropertyPhoto validation with invalid file type."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        photo = PropertyPhoto(
            property=self.property,
            photo=invalid_file
        )
        
        with self.assertRaises(ValidationError):
            photo.full_clean()
    
    def test_property_photo_validation_file_too_large(self):
        """Test PropertyPhoto validation with file too large."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        # Create a file larger than 10MB
        large_file = SimpleUploadedFile(
            name='large.jpg',
            content=b'x' * (11 * 1024 * 1024),  # 11MB
            content_type='image/jpeg'
        )
        
        photo = PropertyPhoto(
            property=self.property,
            photo=large_file
        )
        
        with self.assertRaises(ValidationError):
            photo.full_clean()
    
    def test_property_photo_soft_delete(self):
        """Test PropertyPhoto soft delete functionality."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image
        )
        photo.soft_delete()
        self.assertTrue(photo.is_deleted)
        self.assertIsNotNone(photo.deleted_at)
    
    def test_property_photo_restore(self):
        """Test PropertyPhoto restore functionality."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image
        )
        photo.soft_delete()
        photo.restore()
        self.assertFalse(photo.is_deleted)
        self.assertIsNone(photo.deleted_at)
    
    def test_property_photo_property_relation(self):
        """Test PropertyPhoto relation to Property."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image
        )
        self.assertEqual(photo.property, self.property)
        self.assertIn(photo, self.property.photos.all())
    
    def test_property_photo_cascade_deletion(self):
        """Test that deleting a property cascades to photos."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image
        )
        photo_id = photo.id
        
        # Delete property
        self.property.delete()
        
        # Verify cascade deletion
        self.assertFalse(PropertyPhoto.objects.filter(id=photo_id).exists())
    
    def test_property_photo_get_absolute_url(self):
        """Test PropertyPhoto get_absolute_url method."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image
        )
        url = photo.get_absolute_url()
        self.assertIsNotNone(url)
        self.assertIn('media', url)
    
    def test_property_photo_multiple_photos(self):
        """Test that a property can have multiple photos."""
        photo1 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            photo_type='exterior',
            display_order=1
        )
        photo2 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            photo_type='interior',
            display_order=2
        )
        photo3 = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image,
            photo_type='amenity',
            display_order=3
        )
        
        self.assertEqual(self.property.photos.count(), 3)
        self.assertIn(photo1, self.property.photos.all())
        self.assertIn(photo2, self.property.photos.all())
        self.assertIn(photo3, self.property.photos.all())
    
    def test_property_photo_optional_fields(self):
        """Test PropertyPhoto optional fields (caption, alt_text)."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image
        )
        self.assertIsNone(photo.caption)
        self.assertIsNone(photo.alt_text)
    
    def test_property_photo_default_values(self):
        """Test PropertyPhoto default field values."""
        photo = PropertyPhoto.objects.create(
            property=self.property,
            photo=self.image
        )
        self.assertEqual(photo.photo_type, 'other')
        self.assertFalse(photo.is_primary)
        self.assertEqual(photo.display_order, 0)


class RoomTypeModelTest(TestCase):
    """Test cases for RoomType model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            description='A comfortable standard room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00'),
            currency='USD',
            total_rooms=5,
            bed_configuration='1 Queen Bed',
            room_size=25
        )
    
    def test_room_type_creation(self):
        """Test RoomType creation."""
        self.assertEqual(self.room_type.property, self.property)
        self.assertEqual(self.room_type.name, 'Standard Room')
        self.assertEqual(self.room_type.slug, 'standard-room')
        self.assertEqual(self.room_type.base_occupancy, 2)
        self.assertEqual(self.room_type.max_occupancy, 4)
        self.assertEqual(self.room_type.base_price, Decimal('80.00'))
        self.assertEqual(self.room_type.currency, 'USD')
        self.assertEqual(self.room_type.total_rooms, 5)
    
    def test_room_type_str(self):
        """Test RoomType string representation."""
        expected = f"{self.property.id} - Standard Room"
        self.assertEqual(str(self.room_type), expected)
    
    def test_room_type_unique_slug(self):
        """Test that RoomType slug must be unique per property."""
        with self.assertRaises(Exception):
            RoomType.objects.create(
                property=self.property,
                name='Different Room',
                slug='standard-room',  # Same slug
                base_occupancy=2,
                max_occupancy=4,
                base_price=Decimal('90.00')
            )
    
    def test_room_type_occupancy_validation(self):
        """Test RoomType occupancy validation."""
        # Test max_occupancy < base_occupancy
        room_type = RoomType(
            property=self.property,
            name='Invalid Room',
            slug='invalid-room',
            base_occupancy=4,
            max_occupancy=2,  # Invalid: less than base_occupancy
            base_price=Decimal('80.00')
        )
        
        with self.assertRaises(ValidationError):
            room_type.full_clean()
    
    def test_room_type_property_relation(self):
        """Test RoomType relation to Property."""
        self.assertEqual(self.room_type.property, self.property)
        self.assertIn(self.room_type, self.property.room_types.all())
    
    def test_room_type_soft_delete(self):
        """Test RoomType soft delete functionality."""
        self.room_type.soft_delete()
        self.assertTrue(self.room_type.is_deleted)
        self.assertIsNotNone(self.room_type.deleted_at)
    
    def test_room_type_restore(self):
        """Test RoomType restore functionality."""
        self.room_type.soft_delete()
        self.room_type.restore()
        self.assertFalse(self.room_type.is_deleted)
        self.assertIsNone(self.room_type.deleted_at)
    
    def test_room_type_multiple_room_types(self):
        """Test that a property can have multiple room types."""
        room_type2 = RoomType.objects.create(
            property=self.property,
            name='Deluxe Room',
            slug='deluxe-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('120.00'),
            total_rooms=3
        )
        room_type3 = RoomType.objects.create(
            property=self.property,
            name='Suite',
            slug='suite',
            base_occupancy=4,
            max_occupancy=6,
            base_price=Decimal('200.00'),
            total_rooms=2
        )
        
        self.assertEqual(self.property.room_types.count(), 3)
        self.assertIn(self.room_type, self.property.room_types.all())
        self.assertIn(room_type2, self.property.room_types.all())
        self.assertIn(room_type3, self.property.room_types.all())
    
    def test_room_type_cascade_deletion(self):
        """Test that deleting a property cascades to room types."""
        room_type_id = self.room_type.id
        
        # Delete property
        self.property.delete()
        
        # Verify cascade deletion
        self.assertFalse(RoomType.objects.filter(id=room_type_id).exists())


class RoomPhotoModelTest(TestCase):
    """Test cases for RoomPhoto model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        # Create a mock image file for testing
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.image = SimpleUploadedFile(
            name='test_room_photo.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
    
    def test_room_photo_creation(self):
        """Test RoomPhoto creation."""
        photo = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image,
            photo_type='bedroom',
            caption='Comfortable bedroom',
            is_primary=True,
            display_order=1,
            alt_text='Bedroom photo'
        )
        self.assertEqual(photo.room_type, self.room_type)
        self.assertEqual(photo.photo_type, 'bedroom')
        self.assertEqual(photo.caption, 'Comfortable bedroom')
        self.assertTrue(photo.is_primary)
        self.assertEqual(photo.display_order, 1)
    
    def test_room_photo_str(self):
        """Test RoomPhoto string representation."""
        photo = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image,
            photo_type='bathroom'
        )
        expected = f"Photo {photo.id} - Standard Room (Bathroom)"
        self.assertEqual(str(photo), expected)
    
    def test_room_photo_type_choices(self):
        """Test RoomPhoto photo_type field choices."""
        valid_types = ['bedroom', 'bathroom', 'living_area', 'kitchen', 'view', 'other']
        for photo_type in valid_types:
            photo = RoomPhoto.objects.create(
                room_type=self.room_type,
                photo=self.image,
                photo_type=photo_type
            )
            self.assertEqual(photo.photo_type, photo_type)
    
    def test_room_photo_primary_constraint(self):
        """Test that only one primary photo is allowed per room type."""
        # Create first primary photo
        primary_photo1 = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image,
            is_primary=True
        )
        
        # Create second photo as primary - should make first one non-primary
        primary_photo2 = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image,
            is_primary=True
        )
        
        # Refresh from database
        primary_photo1.refresh_from_db()
        primary_photo2.refresh_from_db()
        
        # Only the second should be primary
        self.assertFalse(primary_photo1.is_primary)
        self.assertTrue(primary_photo2.is_primary)
    
    def test_room_photo_display_order(self):
        """Test RoomPhoto display ordering."""
        photo1 = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image,
            display_order=2
        )
        photo2 = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image,
            display_order=0
        )
        photo3 = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image,
            display_order=1
        )
        
        photos = list(RoomPhoto.objects.filter(room_type=self.room_type))
        self.assertEqual(photos[0], photo2)  # display_order=0
        self.assertEqual(photos[1], photo3)  # display_order=1
        self.assertEqual(photos[2], photo1)  # display_order=2
    
    def test_room_photo_validation_invalid_file_type(self):
        """Test RoomPhoto validation with invalid file type."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        invalid_file = SimpleUploadedFile(
            name='test.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        
        photo = RoomPhoto(
            room_type=self.room_type,
            photo=invalid_file
        )
        
        with self.assertRaises(ValidationError):
            photo.full_clean()
    
    def test_room_photo_soft_delete(self):
        """Test RoomPhoto soft delete functionality."""
        photo = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image
        )
        photo.soft_delete()
        self.assertTrue(photo.is_deleted)
        self.assertIsNotNone(photo.deleted_at)
    
    def test_room_photo_room_type_relation(self):
        """Test RoomPhoto relation to RoomType."""
        photo = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image
        )
        self.assertEqual(photo.room_type, self.room_type)
        self.assertIn(photo, self.room_type.photos.all())
    
    def test_room_photo_cascade_deletion(self):
        """Test that deleting a room type cascades to photos."""
        photo = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image
        )
        photo_id = photo.id
        
        # Delete room type
        self.room_type.delete()
        
        # Verify cascade deletion
        self.assertFalse(RoomPhoto.objects.filter(id=photo_id).exists())
    
    def test_room_photo_get_absolute_url(self):
        """Test RoomPhoto get_absolute_url method."""
        photo = RoomPhoto.objects.create(
            room_type=self.room_type,
            photo=self.image
        )
        url = photo.get_absolute_url()
        self.assertIsNotNone(url)
        self.assertIn('media', url)


class RoomAmenityModelTest(TestCase):
    """Test cases for RoomAmenity model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        self.category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        self.amenity = Amenity.objects.create(
            category=self.category,
            name='Microwave',
            slug='microwave'
        )
        self.room_amenity = RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=self.amenity,
            is_available=True,
            notes='Room-specific microwave'
        )
    
    def test_room_amenity_creation(self):
        """Test RoomAmenity creation."""
        self.assertEqual(self.room_amenity.room_type, self.room_type)
        self.assertEqual(self.room_amenity.amenity, self.amenity)
        self.assertTrue(self.room_amenity.is_available)
        self.assertEqual(self.room_amenity.notes, 'Room-specific microwave')
    
    def test_room_amenity_str(self):
        """Test RoomAmenity string representation."""
        expected = f"Standard Room - Microwave (Available)"
        self.assertEqual(str(self.room_amenity), expected)
    
    def test_room_amenity_unique_constraint(self):
        """Test RoomAmenity unique constraint on room_type and amenity."""
        with self.assertRaises(Exception):
            RoomAmenity.objects.create(
                room_type=self.room_type,
                amenity=self.amenity,  # Same amenity for same room type
                is_available=False
            )
    
    def test_room_amenity_is_available(self):
        """Test RoomAmenity is_available field."""
        available_amenity = RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=Amenity.objects.create(
                category=self.category,
                name='Oven',
                slug='oven'
            ),
            is_available=True
        )
        unavailable_amenity = RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=Amenity.objects.create(
                category=self.category,
                name='Dishwasher',
                slug='dishwasher'
            ),
            is_available=False
        )
        
        self.assertTrue(available_amenity.is_available)
        self.assertFalse(unavailable_amenity.is_available)
    
    def test_room_amenity_room_type_relation(self):
        """Test RoomAmenity relation to RoomType."""
        self.assertEqual(self.room_amenity.room_type, self.room_type)
        self.assertIn(self.room_amenity, self.room_type.room_amenities.all())
    
    def test_room_amenity_amenity_relation(self):
        """Test RoomAmenity relation to Amenity."""
        self.assertEqual(self.room_amenity.amenity, self.amenity)
        self.assertIn(self.room_amenity, self.amenity.room_amenities.all())
    
    def test_room_amenity_soft_delete(self):
        """Test RoomAmenity soft delete functionality."""
        self.room_amenity.soft_delete()
        self.assertTrue(self.room_amenity.is_deleted)
        self.assertIsNotNone(self.room_amenity.deleted_at)
    
    def test_room_amenity_multiple_amenities(self):
        """Test that a room type can have multiple amenities."""
        amenity2 = Amenity.objects.create(
            category=self.category,
            name='Oven',
            slug='oven'
        )
        amenity3 = Amenity.objects.create(
            category=self.category,
            name='Refrigerator',
            slug='refrigerator'
        )
        
        room_amenity2 = RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=amenity2
        )
        room_amenity3 = RoomAmenity.objects.create(
            room_type=self.room_type,
            amenity=amenity3
        )
        
        self.assertEqual(self.room_type.room_amenities.count(), 3)
        self.assertIn(self.room_amenity, self.room_type.room_amenities.all())
        self.assertIn(room_amenity2, self.room_type.room_amenities.all())
        self.assertIn(room_amenity3, self.room_type.room_amenities.all())
    
    def test_room_amenity_cascade_deletion(self):
        """Test that deleting a room type cascades to room amenities."""
        room_amenity_id = self.room_amenity.id
        
        # Delete room type
        self.room_type.delete()
        
        # Verify cascade deletion
        self.assertFalse(RoomAmenity.objects.filter(id=room_amenity_id).exists())


class RatePlanModelTest(TestCase):
    """Test cases for RatePlan model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            description='Standard rate with flexible cancellation',
            base_price=Decimal('80.00'),
            currency='USD',
            min_nights=1,
            max_nights=30,
            is_active=True,
            cancellation_policy='Free cancellation up to 24 hours before check-in',
            deposit_required=False
        )
    
    def test_rate_plan_creation(self):
        """Test RatePlan creation."""
        self.assertEqual(self.rate_plan.room_type, self.room_type)
        self.assertEqual(self.rate_plan.name, 'Standard Rate')
        self.assertEqual(self.rate_plan.slug, 'standard-rate')
        self.assertEqual(self.rate_plan.rate_type, 'standard')
        self.assertEqual(self.rate_plan.base_price, Decimal('80.00'))
        self.assertEqual(self.rate_plan.currency, 'USD')
        self.assertEqual(self.rate_plan.min_nights, 1)
        self.assertEqual(self.rate_plan.max_nights, 30)
        self.assertTrue(self.rate_plan.is_active)
    
    def test_rate_plan_str(self):
        """Test RatePlan string representation."""
        expected = "Standard Room - Standard Rate"
        self.assertEqual(str(self.rate_plan), expected)
    
    def test_rate_plan_rate_type_choices(self):
        """Test RatePlan rate_type field choices."""
        valid_types = ['standard', 'non_refundable', 'early_bird', 'last_minute', 'long_stay', 'seasonal', 'corporate', 'promo']
        for i, rate_type in enumerate(valid_types):
            rate_plan = RatePlan.objects.create(
                room_type=self.room_type,
                name=f'{rate_type.title()} Rate',
                slug=f'{rate_type}-rate-{i}',  # Make slug unique
                rate_type=rate_type,
                base_price=Decimal('90.00')
            )
            self.assertEqual(rate_plan.rate_type, rate_type)
    
    def test_rate_plan_unique_slug(self):
        """Test that RatePlan slug must be unique per room type."""
        with self.assertRaises(Exception):
            RatePlan.objects.create(
                room_type=self.room_type,
                name='Different Rate',
                slug='standard-rate',  # Same slug
                base_price=Decimal('90.00')
            )
    
    def test_rate_plan_nights_validation(self):
        """Test RatePlan nights validation."""
        # Test max_nights < min_nights
        rate_plan = RatePlan(
            room_type=self.room_type,
            name='Invalid Rate',
            slug='invalid-rate',
            min_nights=7,
            max_nights=3,  # Invalid: less than min_nights
            base_price=Decimal('80.00')
        )
        
        with self.assertRaises(ValidationError):
            rate_plan.full_clean()
    
    def test_rate_plan_deposit_validation(self):
        """Test RatePlan deposit validation."""
        # Test deposit_required without deposit_percentage
        rate_plan = RatePlan(
            room_type=self.room_type,
            name='Invalid Deposit Rate',
            slug='invalid-deposit-rate',
            base_price=Decimal('80.00'),
            deposit_required=True,
            deposit_percentage=None  # Invalid: required when deposit_required is True
        )
        
        with self.assertRaises(ValidationError):
            rate_plan.full_clean()
        
        # Test deposit_percentage without deposit_required
        rate_plan = RatePlan(
            room_type=self.room_type,
            name='Invalid Deposit Rate 2',
            slug='invalid-deposit-rate-2',
            base_price=Decimal('80.00'),
            deposit_required=False,
            deposit_percentage=20  # Invalid: should not be set when deposit_required is False
        )
        
        with self.assertRaises(ValidationError):
            rate_plan.full_clean()
    
    def test_rate_plan_room_type_relation(self):
        """Test RatePlan relation to RoomType."""
        self.assertEqual(self.rate_plan.room_type, self.room_type)
        self.assertIn(self.rate_plan, self.room_type.rate_plans.all())
    
    def test_rate_plan_soft_delete(self):
        """Test RatePlan soft delete functionality."""
        self.rate_plan.soft_delete()
        self.assertTrue(self.rate_plan.is_deleted)
        self.assertIsNotNone(self.rate_plan.deleted_at)
    
    def test_rate_plan_restore(self):
        """Test RatePlan restore functionality."""
        self.rate_plan.soft_delete()
        self.rate_plan.restore()
        self.assertFalse(self.rate_plan.is_deleted)
        self.assertIsNone(self.rate_plan.deleted_at)
    
    def test_rate_plan_multiple_rate_plans(self):
        """Test that a room type can have multiple rate plans."""
        rate_plan2 = RatePlan.objects.create(
            room_type=self.room_type,
            name='Non-refundable Rate',
            slug='non-refundable-rate',
            rate_type='non_refundable',
            base_price=Decimal('70.00')
        )
        rate_plan3 = RatePlan.objects.create(
            room_type=self.room_type,
            name='Early Bird Rate',
            slug='early-bird-rate',
            rate_type='early_bird',
            base_price=Decimal('75.00')
        )
        
        self.assertEqual(self.room_type.rate_plans.count(), 3)
        self.assertIn(self.rate_plan, self.room_type.rate_plans.all())
        self.assertIn(rate_plan2, self.room_type.rate_plans.all())
        self.assertIn(rate_plan3, self.room_type.rate_plans.all())
    
    def test_rate_plan_cascade_deletion(self):
        """Test that deleting a room type cascades to rate plans."""
        rate_plan_id = self.rate_plan.id
        
        # Delete room type
        self.room_type.delete()
        
        # Verify cascade deletion
        self.assertFalse(RatePlan.objects.filter(id=rate_plan_id).exists())


class DateInventoryModelTest(TestCase):
    """Test cases for DateInventory model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
        self.room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00')
        )
        self.rate_plan = RatePlan.objects.create(
            room_type=self.room_type,
            name='Standard Rate',
            slug='standard-rate',
            base_price=Decimal('80.00')
        )
        self.date_inventory = DateInventory.objects.create(
            rate_plan=self.rate_plan,
            date=date(2024, 6, 15),
            available_rooms=5,
            booked_rooms=2,
            price=Decimal('85.00'),
            currency='USD',
            is_available=True,
            minimum_stay=1,
            maximum_stay=14
        )
    
    def test_date_inventory_creation(self):
        """Test DateInventory creation."""
        self.assertEqual(self.date_inventory.rate_plan, self.rate_plan)
        self.assertEqual(self.date_inventory.available_rooms, 5)
        self.assertEqual(self.date_inventory.booked_rooms, 2)
        self.assertEqual(self.date_inventory.price, Decimal('85.00'))
        self.assertEqual(self.date_inventory.currency, 'USD')
        self.assertTrue(self.date_inventory.is_available)
        self.assertEqual(self.date_inventory.minimum_stay, 1)
        self.assertEqual(self.date_inventory.maximum_stay, 14)
    
    def test_date_inventory_str(self):
        """Test DateInventory string representation."""
        expected = "Standard Rate - 2024-06-15 (5 available)"
        self.assertEqual(str(self.date_inventory), expected)
    
    def test_date_inventory_unique_constraint(self):
        """Test DateInventory unique constraint on rate_plan and date."""
        from datetime import date
        with self.assertRaises(Exception):
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=date(2024, 6, 15),  # Same date for same rate plan
                available_rooms=3
            )
    
    def test_date_inventory_booked_validation(self):
        """Test DateInventory booked_rooms validation."""
        # Test booked_rooms > available_rooms
        date_inventory = DateInventory(
            rate_plan=self.rate_plan,
            date=date(2024, 6, 16),
            available_rooms=3,
            booked_rooms=5  # Invalid: more than available
        )
        
        with self.assertRaises(ValidationError):
            date_inventory.full_clean()
    
    def test_date_inventory_stay_validation(self):
        """Test DateInventory stay validation."""
        # Test maximum_stay < minimum_stay
        date_inventory = DateInventory(
            rate_plan=self.rate_plan,
            date=date(2024, 6, 16),
            available_rooms=5,
            booked_rooms=2,
            minimum_stay=7,
            maximum_stay=3  # Invalid: less than minimum_stay
        )
        
        with self.assertRaises(ValidationError):
            date_inventory.full_clean()
    
    def test_date_inventory_remaining_rooms(self):
        """Test DateInventory remaining_rooms property."""
        self.assertEqual(self.date_inventory.remaining_rooms, 3)  # 5 - 2 = 3
        
        # Test when booked_rooms equals available_rooms
        self.date_inventory.booked_rooms = 5
        self.date_inventory.save()
        self.assertEqual(self.date_inventory.remaining_rooms, 0)
        
        # Test when booked_rooms exceeds available_rooms (should be 0)
        self.date_inventory.booked_rooms = 6
        self.date_inventory.save()
        self.assertEqual(self.date_inventory.remaining_rooms, 0)
    
    def test_date_inventory_is_available_for_booking(self):
        """Test DateInventory is_available_for_booking method."""
        # Test available for booking
        self.assertTrue(self.date_inventory.is_available_for_booking(nights=5))
        
        # Test not available due to is_available flag
        self.date_inventory.is_available = False
        self.date_inventory.save()
        self.assertFalse(self.date_inventory.is_available_for_booking(nights=5))
        
        # Reset for other tests
        self.date_inventory.is_available = True
        self.date_inventory.save()
        
        # Test not available due to no remaining rooms
        self.date_inventory.booked_rooms = 5
        self.date_inventory.save()
        self.assertFalse(self.date_inventory.is_available_for_booking(nights=5))
        
        # Reset for other tests
        self.date_inventory.booked_rooms = 2
        self.date_inventory.save()
        
        # Test not available due to minimum_stay constraint
        self.assertFalse(self.date_inventory.is_available_for_booking(nights=0))  # Less than minimum_stay=1
        
        # Test not available due to maximum_stay constraint
        self.assertFalse(self.date_inventory.is_available_for_booking(nights=20))  # More than maximum_stay=14
    
    def test_date_inventory_rate_plan_relation(self):
        """Test DateInventory relation to RatePlan."""
        self.assertEqual(self.date_inventory.rate_plan, self.rate_plan)
        self.assertIn(self.date_inventory, self.rate_plan.date_inventory.all())
    
    def test_date_inventory_soft_delete(self):
        """Test DateInventory soft delete functionality."""
        self.date_inventory.soft_delete()
        self.assertTrue(self.date_inventory.is_deleted)
        self.assertIsNotNone(self.date_inventory.deleted_at)
    
    def test_date_inventory_restore(self):
        """Test DateInventory restore functionality."""
        self.date_inventory.soft_delete()
        self.date_inventory.restore()
        self.assertFalse(self.date_inventory.is_deleted)
        self.assertIsNone(self.date_inventory.deleted_at)
    
    def test_date_inventory_multiple_dates(self):
        """Test that a rate plan can have inventory for multiple dates."""
        from datetime import date, timedelta
        base_date = date(2024, 6, 15)
        
        for i in range(1, 6):
            DateInventory.objects.create(
                rate_plan=self.rate_plan,
                date=base_date + timedelta(days=i),
                available_rooms=5,
                booked_rooms=0
            )
        
        self.assertEqual(self.rate_plan.date_inventory.count(), 6)  # Including the setUp date
    
    def test_date_inventory_cascade_deletion(self):
        """Test that deleting a rate plan cascades to date inventory."""
        date_inventory_id = self.date_inventory.id
        
        # Delete rate plan
        self.rate_plan.delete()
        
        # Verify cascade deletion
        self.assertFalse(DateInventory.objects.filter(id=date_inventory_id).exists())
    
    def test_date_inventory_optional_price(self):
        """Test DateInventory optional price field."""
        from datetime import date
        date_inventory = DateInventory.objects.create(
            rate_plan=self.rate_plan,
            date=date(2024, 6, 20),
            available_rooms=5,
            booked_rooms=0
        )
        self.assertIsNone(date_inventory.price)
        # Should use rate plan base price when date price is None


class RoomRatePlanIntegrationTest(TestCase):
    """Integration tests for room, rate plan, and inventory models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='TestPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.property_type = PropertyType.objects.create(
            name='Apartment',
            slug='apartment'
        )
        self.property = Property.objects.create(
            owner=self.user,
            property_type=self.property_type,
            max_guests=4,
            address_line1='123 Main Street',
            city='Tashkent',
            country='Uzbekistan',
            base_price=Decimal('100.00')
        )
    
    def test_complete_room_workflow(self):
        """Test complete room workflow with photos, amenities, rate plans, and inventory."""
        # Create room type
        room_type = RoomType.objects.create(
            property=self.property,
            name='Standard Room',
            slug='standard-room',
            base_occupancy=2,
            max_occupancy=4,
            base_price=Decimal('80.00'),
            total_rooms=5
        )
        
        # Add room photos
        from django.core.files.uploadedfile import SimpleUploadedFile
        image = SimpleUploadedFile(
            name='test_photo.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        photo1 = RoomPhoto.objects.create(
            room_type=room_type,
            photo=image,
            photo_type='bedroom',
            is_primary=True
        )
        photo2 = RoomPhoto.objects.create(
            room_type=room_type,
            photo=image,
            photo_type='bathroom'
        )
        
        # Add room amenities
        category = AmenityCategory.objects.create(
            name='Kitchen',
            slug='kitchen'
        )
        amenity1 = Amenity.objects.create(
            category=category,
            name='Microwave',
            slug='microwave'
        )
        amenity2 = Amenity.objects.create(
            category=category,
            name='Refrigerator',
            slug='refrigerator'
        )
        
        room_amenity1 = RoomAmenity.objects.create(
            room_type=room_type,
            amenity=amenity1,
            is_available=True
        )
        room_amenity2 = RoomAmenity.objects.create(
            room_type=room_type,
            amenity=amenity2,
            is_available=True
        )
        
        # Create rate plans
        rate_plan1 = RatePlan.objects.create(
            room_type=room_type,
            name='Standard Rate',
            slug='standard-rate',
            rate_type='standard',
            base_price=Decimal('80.00'),
            min_nights=1
        )
        rate_plan2 = RatePlan.objects.create(
            room_type=room_type,
            name='Non-refundable Rate',
            slug='non-refundable-rate',
            rate_type='non_refundable',
            base_price=Decimal('70.00'),
            min_nights=2
        )
        
        # Add date inventory
        from datetime import date, timedelta
        base_date = date(2024, 6, 15)
        
        for i in range(10):
            DateInventory.objects.create(
                rate_plan=rate_plan1,
                date=base_date + timedelta(days=i),
                available_rooms=5,
                booked_rooms=0,
                price=Decimal('80.00')
            )
        
        # Verify all relations
        self.assertEqual(room_type.photos.count(), 2)
        self.assertEqual(room_type.room_amenities.count(), 2)
        self.assertEqual(room_type.rate_plans.count(), 2)
        self.assertEqual(rate_plan1.date_inventory.count(), 10)
        
        self.assertIn(photo1, room_type.photos.all())
        self.assertIn(photo2, room_type.photos.all())
        self.assertIn(room_amenity1, room_type.room_amenities.all())
        self.assertIn(room_amenity2, room_type.room_amenities.all())
        self.assertIn(rate_plan1, room_type.rate_plans.all())
        self.assertIn(rate_plan2, room_type.rate_plans.all())
        
        # Verify cascade relationships
        self.assertEqual(room_type.property, self.property)
        self.assertIn(room_type, self.property.room_types.all())