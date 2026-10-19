"""
R11: what a guest is told about cancelling before booking (the quote and the rate plans of a property),
and how the hotel owner sets the terms (.ai/PLAN_R11_CANCELLATION.md).
"""
from datetime import timedelta

import pytest
from django.conf import settings
from rest_framework.test import APIClient

from bookings.cancellation import free_until
from bookings.tests.test_quote import stay  # noqa: F401  (fixture: property, room, rate plan, nights from start)
from properties.models import RatePlanPrice

P = '/api/v1/partner'


def quote(stay, first=0):
    check_in = stay['start'] + timedelta(days=first)
    return APIClient().get(f"/api/v1/properties/{stay['property'].id}/quote/", {
        'room_type_id': stay['room'].id, 'rate_plan_id': stay['rate'].id,
        'check_in': check_in.isoformat(), 'check_out': (check_in + timedelta(days=1)).isoformat(),
    })


@pytest.mark.django_db
class TestQuoteTellsTheTerms:

    def test_a_plan_with_nothing_set_has_no_free_cancellation_and_the_platform_percent(self, stay):
        terms = quote(stay).data['cancellation_terms']
        assert terms == {'free_cancellation': False, 'free_until': None,
                         'refund_percent_after': settings.CANCEL_REFUND_PERCENT}

    def test_a_free_window_gives_the_badge_and_the_date_it_ends(self, stay):
        stay['rate'].free_cancel_hours = 48
        stay['rate'].save()
        terms = quote(stay).data['cancellation_terms']
        assert terms['free_cancellation'] is True
        assert terms['free_until'] == free_until(stay['start'], 48).isoformat()

    def test_a_window_that_has_already_passed_for_these_dates_is_not_free_cancellation(self, stay):
        # the stay starts in 7 days; 14 days of free window ended a week ago
        stay['rate'].free_cancel_hours = 24 * 14
        stay['rate'].save()
        terms = quote(stay).data['cancellation_terms']
        assert terms['free_cancellation'] is False
        assert terms['free_until'] is None

    def test_the_plans_own_percent_is_told(self, stay):
        stay['rate'].cancel_refund_percent = 0
        stay['rate'].save()
        assert quote(stay).data['cancellation_terms']['refund_percent_after'] == 0

    def test_the_quote_still_prices_the_stay(self, stay):
        assert quote(stay).data['total_price'] == '60.00'


@pytest.mark.django_db
class TestRatePlansOfAProperty:

    def plans(self, stay):
        data = APIClient().get(f"/api/v1/properties/{stay['property'].id}/").data
        return {plan['id']: plan for room in data['room_types'] for plan in room['rate_plans']}

    def test_a_plan_without_a_window_is_not_marked_free_cancellation(self, stay):
        plan = self.plans(stay)[stay['rate'].id]
        assert plan['free_cancellation'] is False
        assert plan['free_cancel_hours'] is None
        assert plan['cancel_refund_percent'] == settings.CANCEL_REFUND_PERCENT

    def test_a_plan_with_a_window_is_marked_with_its_hours_and_percent(self, stay):
        stay['rate'].free_cancel_hours = 72
        stay['rate'].cancel_refund_percent = 20
        stay['rate'].save()
        plan = self.plans(stay)[stay['rate'].id]
        assert plan['free_cancellation'] is True
        assert (plan['free_cancel_hours'], plan['cancel_refund_percent']) == (72, 20)


@pytest.mark.django_db
class TestOwnerSetsTheTerms:

    def owner(self, stay):
        from permissions.models import Role
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        owner = stay['property'].owner
        owner.role = role
        owner.save()
        # R16: a rate plan carries the owner's price in every currency, or it cannot be edited
        for code, amount in (('UZS', 750000), ('KZT', 27000), ('RUB', 5400)):
            RatePlanPrice.objects.create(rate_plan=stay['rate'], currency=code, amount=amount)
        client = APIClient()
        client.force_authenticate(user=owner)
        return client

    def test_the_owner_sets_a_free_window_and_a_percent(self, stay):
        response = self.owner(stay).patch(f"{P}/rates/{stay['rate'].id}/",
                                          {'free_cancel_hours': 48, 'cancel_refund_percent': 30}, format='json')
        assert response.status_code == 200, response.data
        stay['rate'].refresh_from_db()
        assert (stay['rate'].free_cancel_hours, stay['rate'].cancel_refund_percent) == (48, 30)

    def test_zero_is_allowed_for_both(self, stay):
        response = self.owner(stay).patch(f"{P}/rates/{stay['rate'].id}/",
                                          {'free_cancel_hours': 0, 'cancel_refund_percent': 0}, format='json')
        assert response.status_code == 200
        stay['rate'].refresh_from_db()
        assert (stay['rate'].free_cancel_hours, stay['rate'].cancel_refund_percent) == (0, 0)

    def test_null_goes_back_to_no_window_and_the_platform_percent(self, stay):
        stay['rate'].free_cancel_hours = 48
        stay['rate'].cancel_refund_percent = 30
        stay['rate'].save()
        response = self.owner(stay).patch(f"{P}/rates/{stay['rate'].id}/",
                                          {'free_cancel_hours': None, 'cancel_refund_percent': None}, format='json')
        assert response.status_code == 200
        stay['rate'].refresh_from_db()
        assert (stay['rate'].free_cancel_hours, stay['rate'].cancel_refund_percent) == (None, None)

    @pytest.mark.parametrize('data', [
        {'free_cancel_hours': 8761}, {'free_cancel_hours': -1}, {'free_cancel_hours': 'soon'},
        {'cancel_refund_percent': 101}, {'cancel_refund_percent': -5}, {'cancel_refund_percent': 'half'},
    ])
    def test_values_out_of_range_are_refused(self, stay, data):
        response = self.owner(stay).patch(f"{P}/rates/{stay['rate'].id}/", data, format='json')
        assert response.status_code == 400
        stay['rate'].refresh_from_db()
        assert (stay['rate'].free_cancel_hours, stay['rate'].cancel_refund_percent) == (None, None)

    def test_another_owner_cannot_change_the_terms(self, stay):
        from users.models import User
        from permissions.models import Role
        role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        intruder = User.objects.create_user(email='intruder@example.com', password='x', role=role)
        client = APIClient()
        client.force_authenticate(user=intruder)
        response = client.patch(f"{P}/rates/{stay['rate'].id}/", {'cancel_refund_percent': 100}, format='json')
        assert response.status_code in (403, 404)
        stay['rate'].refresh_from_db()
        assert stay['rate'].cancel_refund_percent is None
