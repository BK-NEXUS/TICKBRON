"""Iyeniń rate plan lar dizimi database ge belgili sanda soraw beredi, plan qansha bolsa da
(hár plannıń tórt valyutadaǵı bahaları birge júklenedi, birewlep emes)."""
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from permissions.models import Role
from properties.models import Property, PropertyType, RatePlan, RatePlanPrice, RoomType
from users.models import User

pytestmark = pytest.mark.django_db
URL = '/api/v1/partner/rates/'


def add_plan(room, number):
    plan = RatePlan.objects.create(room_type=room, name=f'Plan {number}', slug=f'plan-{number}', base_price=100, currency='UZS')
    for currency in ('UZS', 'USD', 'KZT', 'RUB'):
        RatePlanPrice.objects.create(rate_plan=plan, currency=currency, amount=100)
    return plan


def test_the_number_of_queries_does_not_grow_with_the_number_of_plans(django_assert_max_num_queries):
    role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'description': 'Owner', 'is_system_role': True})
    owner = User.objects.create_user(email='o@example.com', password='testpassword123', role=role)
    kind = PropertyType.objects.create(name='Hotel', slug='hotel')
    prop = Property.objects.create(
        owner=owner, property_type=kind, status='active', max_guests=4, bedrooms=1, bathrooms=1,
        address_line1='1 Main St', city='Tashkent', country='Uzbekistan', base_price=100, currency='UZS')
    room = RoomType.objects.create(
        property=prop, name='Std', slug='std', base_occupancy=2, max_occupancy=3, base_price=100, currency='UZS', total_rooms=5)
    api = APIClient()
    api.force_authenticate(user=owner)
    add_plan(room, 0)
    with CaptureQueriesContext(connection) as one:
        assert api.get(URL).status_code == 200
    for number in range(1, 9):
        add_plan(room, number)

    with django_assert_max_num_queries(len(one)):
        response = api.get(URL)

    assert len(response.data['results']) == 9
    assert all(set(row['prices']) == {'UZS', 'USD', 'KZT', 'RUB'} for row in response.data['results'])
