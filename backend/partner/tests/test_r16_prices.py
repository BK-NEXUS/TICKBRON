"""
R16 slice 1: the owner enters the price of a rate plan in every currency (USD, UZS, KZT, RUB).
The plan's main price (`base_price`, in the property's currency) is one of them. Fixture
`inventory`: a USD property with one rate plan.
"""
import pytest
from partner.tests.test_property_create_access import client_for, inventory, owner, owner_role  # noqa: F401
from properties.models import RatePlan, RatePlanPrice

P = '/api/v1/partner'
FULL = {'USD': '65.00', 'UZS': '800000', 'KZT': '29000', 'RUB': '5800'}


def new_plan(inv, **extra):
    return {'room_type': inv['room'].id, 'name': 'Flex', 'slug': 'flex', 'rate_type': 'standard',
            'min_nights': 1, 'is_active': True, **extra}


@pytest.mark.django_db
class TestWritePrices:

    def test_create_with_all_four_prices(self, owner, inventory):
        response = client_for(owner).post(f'{P}/rates/', new_plan(inventory, prices=FULL), format='json')
        assert response.status_code == 201, response.data
        plan = RatePlan.objects.get(pk=response.data['id'])
        assert str(plan.base_price) == '65.00'      # the main price is the property's currency (USD)
        assert {row.currency: str(row.amount) for row in plan.prices.all()} == {
            'UZS': '800000.00', 'KZT': '29000.00', 'RUB': '5800.00'}
        assert response.data['prices'] == {'USD': '65.00', 'UZS': '800000.00', 'KZT': '29000.00', 'RUB': '5800.00'}

    def test_the_read_side_lists_every_currency(self, owner, inventory):
        RatePlanPrice.objects.create(rate_plan=inventory['rate'], currency='UZS', amount=750000)
        response = client_for(owner).get(f"{P}/rates/{inventory['rate'].id}/")
        assert response.data['prices'] == {'USD': '60.00', 'UZS': '750000.00'}

    @pytest.mark.parametrize('missing', ['USD', 'UZS', 'KZT', 'RUB'])
    def test_a_missing_currency_is_named(self, owner, inventory, missing):
        prices = {code: value for code, value in FULL.items() if code != missing}
        response = client_for(owner).post(f'{P}/rates/', new_plan(inventory, prices=prices), format='json')
        assert response.status_code == 400
        assert missing in str(response.data)

    @pytest.mark.parametrize('prices', [
        {**FULL, 'EUR': '60'},
        {**FULL, 'UZS': '800000.50'},       # so'm are whole
        {**FULL, 'KZT': '29000.5'},         # tenge are whole
        {**FULL, 'USD': '65.001'},          # cents
        {**FULL, 'RUB': '-1'},
        {**FULL, 'UZS': 'abc'},
    ])
    def test_bad_prices_are_refused(self, owner, inventory, prices):
        response = client_for(owner).post(f'{P}/rates/', new_plan(inventory, prices=prices), format='json')
        assert response.status_code == 400
        assert 'prices' in str(response.data)

    @pytest.mark.parametrize('prices', ['65.00', ['USD', '65.00'], 65])
    def test_a_price_map_that_is_not_an_object_is_a_400_with_an_example(self, owner, inventory, prices):
        response = client_for(owner).post(f'{P}/rates/', new_plan(inventory, prices=prices), format='json')
        assert response.status_code == 400
        assert 'Send an object like' in str(response.data)

    def test_base_price_must_agree_with_the_main_price(self, owner, inventory):
        response = client_for(owner).post(f'{P}/rates/', new_plan(inventory, prices=FULL, base_price='70.00'),
                                          format='json')
        assert response.status_code == 400
        assert 'base_price' in str(response.data)

    def test_update_replaces_the_prices_and_moves_the_main_one(self, owner, inventory):
        client = client_for(owner)
        plan = client.post(f'{P}/rates/', new_plan(inventory, prices=FULL), format='json').data
        response = client.patch(f"{P}/rates/{plan['id']}/", {'prices': {**FULL, 'USD': '70.00', 'UZS': '850000'}},
                                format='json')
        assert response.status_code == 200, response.data
        rate = RatePlan.objects.get(pk=plan['id'])
        assert str(rate.base_price) == '70.00'
        assert str(rate.prices.get(currency='UZS').amount) == '850000.00'
        assert rate.prices.count() == 3

    def test_another_owner_cannot_write_prices(self, owner, inventory):
        from users.models import User
        other = User.objects.create_user(email='other@example.com', password='Passw0rd#12345', role=owner.role)
        response = client_for(other).patch(f"{P}/rates/{inventory['rate'].id}/", {'prices': FULL}, format='json')
        assert response.status_code == 404
        assert not RatePlanPrice.objects.exists()

    def test_without_the_requirement_prices_stay_optional(self, owner, inventory, settings):
        settings.RATE_PLAN_PRICES_REQUIRED = False
        response = client_for(owner).post(f'{P}/rates/', new_plan(inventory, base_price='65.00'), format='json')
        assert response.status_code == 201, response.data


@pytest.mark.django_db
class TestPricesRequired:
    """The owner decided (2026-10-19): all four currencies are mandatory."""

    @pytest.fixture(autouse=True)
    def required(self, settings):
        settings.RATE_PLAN_PRICES_REQUIRED = True

    def test_create_without_prices_is_refused(self, owner, inventory):
        response = client_for(owner).post(f'{P}/rates/', new_plan(inventory, base_price='65.00'), format='json')
        assert response.status_code == 400
        assert 'prices' in str(response.data)

    def test_a_plan_without_the_other_prices_cannot_be_edited_until_they_are_entered(self, owner, inventory):
        client = client_for(owner)
        url = f"{P}/rates/{inventory['rate'].id}/"
        refused = client.patch(url, {'name': 'Renamed'}, format='json')
        assert refused.status_code == 400
        assert 'prices' in str(refused.data)
        assert client.patch(url, {'name': 'Renamed', 'prices': {**FULL, 'USD': '60.00'}}, format='json').status_code == 200

    def test_a_complete_plan_can_be_edited_without_resending_the_prices(self, owner, inventory):
        client = client_for(owner)
        plan = client.post(f'{P}/rates/', new_plan(inventory, prices=FULL), format='json').data
        response = client.patch(f"{P}/rates/{plan['id']}/", {'name': 'Renamed'}, format='json')
        assert response.status_code == 200, response.data
        assert response.data['prices']['KZT'] == '29000.00'
