"""
Two admins promoting the same hotel at the same moment: exactly one wins (PostgreSQL row lock).

    pytest --create-db promotions/tests/test_concurrency.py
"""
from datetime import timedelta

from django.test import TransactionTestCase

from bookings.tests.test_concurrency import run_concurrently
from common.dates import business_today
from promotions import service
from promotions.models import Promotion
from promotions.service import PromotionError
from promotions.tests.helpers import make_hotel, make_owner, make_superadmin


class PromotionConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.admin = make_superadmin()
        self.hotel = make_hotel(make_owner('o@example.com'), name='Alpha')
        self.other = make_hotel(make_owner('p@example.com'), name='Beta')
        self.start = business_today() + timedelta(days=1)

    def create(self, hotel, first_offset, days=7):
        first = self.start + timedelta(days=first_offset)
        return lambda: service.create_promotion(
            actor=self.admin, property=hotel, start_date=first, end_date=first + timedelta(days=days - 1))

    def test_overlapping_requests_for_one_hotel_only_one_wins(self):
        results = run_concurrently(*[self.create(self.hotel, offset) for offset in (0, 1, 2, 3)])
        winners = [r for r in results if r[0] == 'ok']
        losers = [r for r in results if r[0] == 'error']
        assert len(winners) == 1
        assert all(isinstance(r[1], PromotionError) and r[1].code == 'overlap' for r in losers)
        assert Promotion.objects.filter(property=self.hotel).count() == 1

    def test_different_hotels_do_not_block_each_other(self):
        results = run_concurrently(self.create(self.hotel, 0), self.create(self.other, 0))
        assert [r[0] for r in results] == ['ok', 'ok']

    def test_back_to_back_periods_for_one_hotel_both_win(self):
        results = run_concurrently(self.create(self.hotel, 0, days=7), self.create(self.hotel, 7, days=7))
        assert [r[0] for r in results] == ['ok', 'ok']

    def test_two_mark_paid_calls_record_one_payment(self):
        promo = service.create_promotion(actor=self.admin, property=self.hotel, start_date=self.start,
                                         end_date=self.start + timedelta(days=6))
        results = run_concurrently(
            lambda: service.mark_paid(Promotion.objects.get(pk=promo.pk), actor=self.admin),
            lambda: service.mark_paid(Promotion.objects.get(pk=promo.pk), actor=self.admin))
        assert sorted(r[0] for r in results) == ['error', 'ok']
        assert [r[1].code for r in results if r[0] == 'error'] == ['already_paid']
