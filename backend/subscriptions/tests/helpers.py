from decimal import Decimal

from properties.models import Property, PropertyTranslation, PropertyType
from users.models import User


def make_owner(**extra):
    return User.objects.create_user(email=f'owner{User.objects.count()}@example.com', password='x', **extra)


def make_hotel(owner=None, name='Kolya Hotel', city='Tashkent', status='active'):
    owner = owner or make_owner(first_name='Olim', last_name='Egasi', phone_number='+998901112233')
    kind, _ = PropertyType.objects.get_or_create(name='Hotel', defaults={'slug': 'hotel'})
    hotel = Property.objects.create(
        owner=owner, property_type=kind, status=status, max_guests=2, bedrooms=1, bathrooms=1,
        address_line1='1 Main St', city=city, country='Uzbekistan', base_price=Decimal('60.00'), currency='USD',
        latitude=Decimal('41.311081'), longitude=Decimal('69.240562'),
    )
    PropertyTranslation.objects.create(property=hotel, language='en', name=name)
    return hotel
