# Run manually against a local dev server to smoke-test the core register→login→book→favorites chain. Usage: venv\Scripts\python.exe backend\scripts\smoke_test.py
"""
Comprehensive API Smoke Test for TICKBRON Backend - VERSION 2
Tests the core register→login→book chain with fresh unique users each run
"""
import os
import sys
import django
import time
import random

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Test mode settings
os.environ.setdefault('SMS_TEST_MODE', 'True')
os.environ.setdefault('PAYMENT_TEST_MODE', 'True')

django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from properties.models import Property, PropertyType, RoomType, RatePlan, DateInventory
from bookings.models import Booking, BookingItem
from payments.models import PaymentTransaction
from admin_panel.models import InternalNote
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

User = get_user_model()

class APISmokeTestV2:
    def __init__(self):
        self.client = Client()
        # Override the default testserver host to avoid ALLOWED_HOSTS issues
        self.client.defaults['HTTP_HOST'] = 'localhost'
        self.test_user = None
        self.test_property = None
        self.test_booking = None
        self.super_admin = None
        self.timestamp = int(time.time())
        self.random_suffix = random.randint(1000, 9999)

    def get_unique_email(self):
        """Generate a unique email for this test run"""
        return f"smoketest_{self.timestamp}_{self.random_suffix}@example.com"

    def get_unique_phone(self):
        """Generate a unique phone number for this test run"""
        return f"+99890{self.random_suffix}{self.timestamp % 1000000:06d}"

    def setup_test_data(self):
        """Create test data for smoke tests"""
        print("\n=== SETTING UP TEST DATA ===")
        
        # Create super admin
        self.super_admin, created = User.objects.get_or_create(
            email='admin@smoketest.com',
            defaults={
                'password': 'adminpass123',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            self.super_admin.set_password('adminpass123')
            self.super_admin.save()
        else:
            self.super_admin.set_password('adminpass123')
            self.super_admin.save()
        print(f"Created/retrieved super admin: {self.super_admin.email}")
        
        # Create property type
        property_type, created = PropertyType.objects.get_or_create(
            slug='apartment',
            defaults={
                'name': 'Apartment',
                'description': 'Apartment property type'
            }
        )
        
        # Create test property
        self.test_property, created = Property.objects.get_or_create(
            address_line1='123 Test St',
            defaults={
                'owner': self.super_admin,
                'property_type': property_type,
                'status': 'active',
                'max_guests': 4,
                'bedrooms': 2,
                'bathrooms': 1,
                'city': 'Tashkent',
                'country': 'Uzbekistan',
                'base_price': Decimal('100.00'),
                'currency': 'USD'
            }
        )
        print(f"Created/retrieved test property: {self.test_property.id} - {self.test_property.city}, {self.test_property.country}")
        
        # Create room type
        room_type, created = RoomType.objects.get_or_create(
            property=self.test_property,
            slug='standard-room',
            defaults={
                'name': 'Standard Room',
                'base_occupancy': 2,
                'max_occupancy': 4,
                'base_price': Decimal('100.00'),
                'currency': 'USD',
                'total_rooms': 5
            }
        )
        
        # Create rate plan
        rate_plan, created = RatePlan.objects.get_or_create(
            room_type=room_type,
            slug='standard-rate',
            defaults={
                'name': 'Standard Rate',
                'rate_type': 'standard',
                'base_price': Decimal('100.00'),
                'currency': 'USD',
                'min_nights': 1,
                'max_nights': 30,
                'is_active': True
            }
        )
        
        # Create date inventory for testing
        today = date.today()
        # Delete existing inventory for this rate plan
        DateInventory.objects.filter(rate_plan=rate_plan).delete()
        
        for i in range(30):
            inventory_date = today + timedelta(days=i)
            DateInventory.objects.create(
                rate_plan=rate_plan,
                date=inventory_date,
                available_rooms=5,
                booked_rooms=0,
                price=Decimal('100.00'),
                currency='USD',
                is_available=True
            )
        
        print("Created room type, rate plan, and inventory")

        # R6: a USD hotel can only be booked once an exchange rate exists
        from currency.cbu import tashkent_today
        from currency.models import ExchangeRate
        if not ExchangeRate.objects.filter(currency='USD', status='accepted').exists():
            ExchangeRate.objects.create(currency='USD', rate=Decimal('12000.00'), nominal=1, source='demo',
                                        status='accepted', rate_date=tashkent_today(),
                                        note='smoke_test: local only, not a real rate')
            print("Stored a demo USD rate (run fetch_exchange_rates for the real one)")

    def test_registration(self):
        """Test user registration with fresh unique user"""
        print("\n=== STEP 1: USER REGISTRATION ===")
        
        unique_email = self.get_unique_email()
        unique_phone = self.get_unique_phone()
        test_password = 'testpassword123'
        
        print(f"Using unique email: {unique_email}")
        print(f"Using unique phone: {unique_phone}")
        print(f"Using password: {test_password}")
        
        data = {
            'full_name': 'Smoke Test User',
            'phone_number': unique_phone,
            'email': unique_email,
            'password': test_password,
            'password_confirm': test_password
        }
        
        print(f"\nREQUEST: POST /api/v1/auth/register/")
        print(f"Payload: {data}")
        
        response = self.client.post('/api/v1/auth/register/', data, content_type='application/json')
        
        print(f"\nRESPONSE:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.content.decode('utf-8')}")
        
        if response.status_code == 202:
            # Verify user was created
            user_exists = User.objects.filter(email=unique_email).exists()
            if user_exists:
                self.test_user = User.objects.get(email=unique_email)
                print(f"\nSUCCESS: User created successfully: {self.test_user.email}")
                print(f"User ID: {self.test_user.id}")
                print(f"User is_active: {self.test_user.is_active}")
                # Store credentials for login test
                self.test_user_email = unique_email
                self.test_user_password = test_password
                return True
            else:
                print(f"\nFAIL: User not found in database despite 202 response")
                return False
        else:
            print(f"\nFAIL: Registration failed with status {response.status_code}")
            return False

    def test_password_login(self):
        """Test password login with the freshly registered user"""
        print("\n=== STEP 2: PASSWORD LOGIN ===")
        
        if not hasattr(self, 'test_user_email'):
            print("SKIPPED: No user from registration step")
            return False
        
        print(f"Email from registration: {self.test_user_email}")
        print(f"Password from registration: {self.test_user_password}")
        
        data = {
            'email': self.test_user_email,
            'password': self.test_user_password
        }
        
        print(f"\nREQUEST: POST /api/v1/auth/login/")
        print(f"Payload: {data}")
        
        response = self.client.post('/api/v1/auth/login/', data, content_type='application/json')
        
        print(f"\nRESPONSE:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.content.decode('utf-8')}")
        
        if response.status_code == 200:
            print(f"\nSUCCESS: Login successful")
            # Update test_user reference to the authenticated user
            self.test_user = User.objects.get(email=self.test_user_email)
            return True
        else:
            print(f"\nFAIL: Login failed with status {response.status_code}")
            # Investigate why
            print(f"\nINVESTIGATION:")
            user = User.objects.filter(email=self.test_user_email).first()
            if user:
                print(f"User exists in DB: {user.email}")
                print(f"User is_active: {user.is_active}")
                print(f"User password hash: {user.password[:50]}...")
                # Verify password manually
                from django.contrib.auth import check_password
                if check_password(self.test_user_password, user.password):
                    print("Password hash verification: MATCH")
                else:
                    print("Password hash verification: MISMATCH")
            else:
                print("User NOT found in DB")
            return False

    def test_booking_creation(self):
        """Test booking creation with authenticated session"""
        print("\n=== STEP 3: BOOKING CREATION ===")
        
        if not self.test_user or not self.test_property:
            print("SKIPPED: Missing test data")
            return False
        
        # Get room type and rate plan
        room_type = RoomType.objects.filter(property=self.test_property).first()
        if not room_type:
            print("SKIPPED: No room type available")
            return False
        
        rate_plan = RatePlan.objects.filter(room_type=room_type).first()
        if not rate_plan:
            print("SKIPPED: No rate plan available")
            return False
        
        check_in = date.today() + timedelta(days=10)
        check_out = date.today() + timedelta(days=12)
        
        data = {
            'property_id': self.test_property.id,
            'room_type_id': room_type.id,
            'rate_plan_id': rate_plan.id,
            'check_in': str(check_in),
            'check_out': str(check_out),
            'guest_count': 2,
            'special_requests': 'Smoke test booking'
        }
        
        print(f"\nREQUEST: POST /api/v1/bookings/")
        print(f"Payload: {data}")
        print(f"Authenticated as: {self.test_user.email}")
        
        response = self.client.post('/api/v1/bookings/', data, content_type='application/json')
        
        print(f"\nRESPONSE:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.content.decode('utf-8')}")
        
        if response.status_code == 201:
            print(f"\nSUCCESS: Booking creation successful")
            try:
                import json
                booking_data = json.loads(response.content)
                booking_id = booking_data.get('id')
                if booking_id:
                    self.test_booking = Booking.objects.get(id=booking_id)
                    print(f"Booking ID: {booking_id}")
                    print(f"Booking status: {self.test_booking.status}")
                    print(f"Booking confirmation code: {self.test_booking.confirmation_code}")
                    return True
                else:
                    print("WARNING: No booking ID in response")
                    return False
            except Exception as e:
                print(f"WARNING: Could not parse booking response: {e}")
                return False
        else:
            print(f"\nFAIL: Booking creation failed with status {response.status_code}")
            return False

    def test_favorites(self):
        """Test favorites functionality with authenticated session"""
        print("\n=== STEP 4: FAVORITES ===")
        
        if not self.test_user or not self.test_property:
            print("SKIPPED: Missing test data")
            return False
        
        data = {'property': self.test_property.id}
        
        print(f"\nREQUEST: POST /api/v1/me/favorites/")
        print(f"Payload: {data}")
        print(f"Authenticated as: {self.test_user.email}")
        
        response = self.client.post('/api/v1/me/favorites/', data, content_type='application/json')
        
        print(f"\nRESPONSE:")
        print(f"Status Code: {response.status_code}")
        print(f"Response Body: {response.content.decode('utf-8')}")
        
        if response.status_code == 201:
            print(f"\nSUCCESS: Added to favorites")
            return True
        else:
            print(f"\nFAIL: Add to favorites failed with status {response.status_code}")
            return False

    def run_full_chain(self):
        """Run the full register→login→book→favorites chain"""
        print("=" * 80)
        print("TICKBRON BACKEND API SMOKE TEST - FULL CHAIN")
        print("=" * 80)
        print(f"Test Timestamp: {self.timestamp}")
        print(f"Random Suffix: {self.random_suffix}")
        
        try:
            self.setup_test_data()
            
            # Step 1: Register
            step1_pass = self.test_registration()
            
            # Step 2: Login
            step2_pass = self.test_password_login()
            
            # Step 3: Create booking
            step3_pass = self.test_booking_creation()
            
            # Step 4: Add to favorites
            step4_pass = self.test_favorites()
            
            # Summary
            print("\n" + "=" * 80)
            print("FULL CHAIN SUMMARY")
            print("=" * 80)
            print(f"Step 1 - Registration: {'PASS' if step1_pass else 'FAIL'}")
            print(f"Step 2 - Login: {'PASS' if step2_pass else 'FAIL'}")
            print(f"Step 3 - Booking Creation: {'PASS' if step3_pass else 'FAIL'}")
            print(f"Step 4 - Favorites: {'PASS' if step4_pass else 'FAIL'}")
            
            all_pass = step1_pass and step2_pass and step3_pass and step4_pass
            print(f"\nFULL CHAIN: {'CONFIRMED' if all_pass else 'FAILED'}")
            
            return all_pass
            
        except Exception as e:
            print(f"\nCHAIN FAILED WITH EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    tester = APISmokeTestV2()
    result = tester.run_full_chain()
    sys.exit(0 if result else 1)
