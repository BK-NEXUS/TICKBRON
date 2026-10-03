"""
R6: a property is priced in USD or UZS; its room types, rate plans and nightly
prices use the property's currency; UZS prices are whole so'm. A new property
defaults to its country's currency when supported (Uzbekistan -> UZS), else USD.
"""
from datetime import date, timedelta

import pytest

from geography.models import City
from partner.tests.geography_helpers import uzbek_location
from partner.tests.test_property_create_access import client_for, inventory, owner, owner_role  # noqa: F401

P = '/api/v1/partner'


def _property_payload(inv, **extra):
    payload = {
        'property_type': inv['property_type'].id, 'max_guests': 2, 'bedrooms': 1, 'bathrooms': 1,
        'address_line1': '2 Navoi', **uzbek_location('Tashkent'), 'base_price': '700000',
    }
    payload.update(extra)
    return {k: v for k, v in payload.items() if v is not None}


@pytest.mark.django_db
class TestPropertyCurrency:

    def test_unsupported_currency_is_rejected(self, owner, inventory):
        response = client_for(owner).post(f'{P}/properties/', _property_payload(inventory, currency='EUR'),
                                          format='json')
        assert response.status_code == 400
        assert 'currency' in str(response.data)

    def test_uzbek_property_defaults_to_uzs(self, owner, inventory):
        response = client_for(owner).post(f'{P}/properties/', _property_payload(inventory), format='json')
        assert response.status_code == 201, response.data
        assert response.data['currency'] == 'UZS'

    def test_other_country_defaults_to_usd(self, owner, inventory):
        city = City.objects.select_related('region__country').filter(region__country__code='KZ').first()
        payload = _property_payload(inventory, country_ref=city.region.country_id, region_ref=city.region_id,
                                    city_ref=city.id, base_price='70.00')
        response = client_for(owner).post(f'{P}/properties/', payload, format='json')
        assert response.status_code == 201, response.data
        assert response.data['currency'] == 'USD'

    def test_owner_may_choose_usd_in_uzbekistan(self, owner, inventory):
        response = client_for(owner).post(
            f'{P}/properties/', _property_payload(inventory, currency='USD', base_price='70.00'), format='json')
        assert response.status_code == 201
        assert response.data['currency'] == 'USD'

    def test_uzs_price_must_be_whole_som(self, owner, inventory):
        response = client_for(owner).post(
            f'{P}/properties/', _property_payload(inventory, currency='UZS', base_price='700000.50'), format='json')
        assert response.status_code == 400
        assert 'base_price' in str(response.data)

    def test_currency_cannot_change_once_rooms_exist(self, owner, inventory):
        response = client_for(owner).patch(f"{P}/properties/{inventory['property'].id}/", {'currency': 'UZS'},
                                           format='json')
        assert response.status_code == 400
        inventory['property'].refresh_from_db()
        assert inventory['property'].currency == 'USD'


@pytest.mark.django_db
class TestChildrenFollowTheProperty:
    """inventory fixture: a USD property with a room type, rate plan and one nightly price."""

    @pytest.mark.parametrize('url, payload', [
        ('rooms', lambda inv: {'property': inv['property'].id, 'name': 'Deluxe', 'slug': 'deluxe',
                               'base_occupancy': 2, 'max_occupancy': 3, 'base_price': '90.00', 'total_rooms': 2}),
        ('rates', lambda inv: {'room_type': inv['room'].id, 'name': 'Flex', 'slug': 'flex', 'rate_type': 'standard',
                               'base_price': '65.00', 'min_nights': 1, 'is_active': True}),
        ('inventory', lambda inv: {'rate_plan': inv['rate'].id, 'date': (date.today() + timedelta(days=1)).isoformat(),
                                   'available_rooms': 3, 'price': '60.00', 'is_available': True}),
    ])
    def test_other_currency_is_rejected_and_default_is_the_propertys(self, owner, inventory, url, payload):
        client = client_for(owner)
        wrong = client.post(f'{P}/{url}/', {**payload(inventory), 'currency': 'UZS'}, format='json')
        assert wrong.status_code == 400
        assert 'currency' in str(wrong.data)

        right = client.post(f'{P}/{url}/', payload(inventory), format='json')
        assert right.status_code == 201, right.data
        assert right.data['currency'] == 'USD'

    def test_uzs_nightly_price_must_be_whole_som(self, owner, inventory):
        from properties.models import Property, RatePlan, RoomType
        prop = inventory['property']
        Property.objects.filter(pk=prop.pk).update(currency='UZS')
        RoomType.objects.filter(pk=inventory['room'].pk).update(currency='UZS')
        RatePlan.objects.filter(pk=inventory['rate'].pk).update(currency='UZS')

        client = client_for(owner)
        tomorrow = (date.today() + timedelta(days=2)).isoformat()
        base = {'rate_plan': inventory['rate'].id, 'date': tomorrow, 'available_rooms': 3, 'is_available': True}
        assert client.post(f'{P}/inventory/', {**base, 'price': '700000.50'}, format='json').status_code == 400
        assert client.post(f'{P}/inventory/', {**base, 'price': '700000'}, format='json').status_code == 201

        bulk = client.post(f'{P}/inventory/bulk-price/', {
            'rate_plan': inventory['rate'].id, 'date_from': tomorrow,
            'date_to': (date.today() + timedelta(days=4)).isoformat(), 'price': '650000.25',
        }, format='json')
        assert bulk.status_code == 400
