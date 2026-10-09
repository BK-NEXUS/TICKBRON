"""Shared builders for the promotions (R10) tests."""
from datetime import timedelta
from decimal import Decimal

from common.dates import business_today
from geography.models import City, Country, Region
from permissions.models import Role
from promotions.models import Promotion
from properties.models import Property, PropertyTranslation, PropertyType
from users.models import User


def make_owner(email='owner@example.com'):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
    return User.objects.create_user(email=email, password='Pass12345!', full_name='Owner', role=role)


def make_staff(email='staff@example.com'):
    return User.objects.create_user(email=email, password='Pass12345!', full_name='Staff', is_staff=True)


def make_superadmin(email='root@example.com'):
    return User.objects.create_superuser(email=email, password='Pass12345!')


def make_guest(email='guest@example.com'):
    return User.objects.create_user(email=email, password='Pass12345!', full_name='Guest')


def make_hotel(owner, name='Alpha', status='active', city_ref=None, base_price=500000):
    hotel_type, _ = PropertyType.objects.get_or_create(name='Hotel', slug='hotel')
    prop = Property.objects.create(
        owner=owner, property_type=hotel_type, status=status, max_guests=2, bedrooms=1, bathrooms=1,
        address_line1=f'1 {name} Street', city='Samarkand', country='Uzbekistan', base_price=base_price,
        currency='UZS', city_ref=city_ref,
        region_ref=city_ref.region if city_ref else None,
        country_ref=city_ref.region.country if city_ref else None,
    )
    PropertyTranslation.objects.create(property=prop, language='en', name=name)
    return prop


def uz_city(name_en='Samarkand'):
    return City.objects.filter(region__country__code='UZ', name_en=name_en).first() or City.objects.filter(
        region__country__code='UZ').first()


def other_country_city():
    return City.objects.exclude(region__country__code='UZ').first()


def make_promotion(prop, start_offset=0, days=7, paid=True, status='active', priority=0, **extra):
    start = business_today() + timedelta(days=start_offset)
    promotion = Promotion.objects.create(
        property=prop, start_date=start, end_date=start + timedelta(days=days - 1), priority=priority,
        price_amount=Decimal('1000000'), price_currency='UZS', status=status, **extra)
    if paid:
        from django.utils import timezone
        promotion.paid_at = timezone.now()
        promotion.save(update_fields=['paid_at'])
    return promotion
