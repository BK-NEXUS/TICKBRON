"""
Tests for property models.
"""
import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from properties.models import PropertyType, Property, PropertyTranslation, PropertyPolicy
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