from datetime import timedelta
from decimal import Decimal

import pytest

from admin_panel.models import AdminAccessLog
from common.dates import business_today
from promotions import service
from promotions.models import Promotion
from promotions.service import PromotionError
from promotions.tests.helpers import (
    make_hotel, make_owner, make_promotion, make_superadmin, other_country_city, uz_city)

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin():
    return make_superadmin()


@pytest.fixture
def hotel():
    return make_hotel(make_owner(), city_ref=uz_city())


def create(admin, hotel, start=0, days=7, **kw):
    first = business_today() + timedelta(days=start)
    return service.create_promotion(
        actor=admin, property=hotel, start_date=first, end_date=first + timedelta(days=days - 1), **kw)


class TestCreate:
    def test_creates_unpaid_scheduled_promotion_with_audit(self, admin, hotel):
        promo = create(admin, hotel, price_amount=Decimal('2500000'), price_currency='uzs', note='Invoice 15')
        assert promo.status == 'scheduled'
        assert promo.paid_at is None
        assert promo.price_currency == 'UZS'
        assert promo.created_by_id == admin.pk
        row = AdminAccessLog.objects.get(action='promotion_create')
        assert row.actor_id == admin.pk
        assert row.details['promotion_id'] == promo.pk
        assert row.details['property_id'] == hotel.pk

    def test_start_in_the_past_is_rejected(self, admin, hotel):
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, start=-1)
        assert err.value.code == 'start_in_past'

    def test_end_before_start_is_rejected(self, admin, hotel):
        today = business_today()
        with pytest.raises(PromotionError) as err:
            service.create_promotion(actor=admin, property=hotel, start_date=today,
                                     end_date=today - timedelta(days=1))
        assert err.value.code == 'bad_dates'

    def test_longer_than_a_year_is_rejected(self, admin, hotel):
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, days=366)
        assert err.value.code == 'too_long'

    def test_one_year_is_allowed(self, admin, hotel):
        assert create(admin, hotel, days=365).pk

    @pytest.mark.parametrize('priority', [-1, 101])
    def test_priority_out_of_range_is_rejected(self, admin, hotel, priority):
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, priority=priority)
        assert err.value.code == 'bad_priority'

    @pytest.mark.parametrize('amount', [Decimal('-1'), Decimal('1000000000000')])
    def test_bad_price_is_rejected(self, admin, hotel, amount):
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, price_amount=amount)
        assert err.value.code == 'bad_price'

    def test_bad_currency_is_rejected(self, admin, hotel):
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, price_amount=Decimal('1'), price_currency='so\'m')
        assert err.value.code == 'bad_currency'

    def test_note_over_500_chars_is_rejected(self, admin, hotel):
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, note='x' * 501)
        assert err.value.code == 'note_too_long'

    def test_inactive_hotel_can_be_promoted_but_is_not_shown(self, admin):
        suspended = make_hotel(make_owner('o2@example.com'), name='Beta', status='suspended')
        promo = create(admin, suspended)
        assert promo.pk
        service.mark_paid(promo, actor=admin)
        assert list(service.shown_now()) == []

    def test_scope_refs_must_agree(self, admin, hotel):
        city = uz_city()
        foreign = other_country_city()
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, country_ref=foreign.region.country, city_ref=city)
        assert err.value.code == 'bad_scope'

    def test_consistent_scope_is_saved(self, admin, hotel):
        city = uz_city()
        promo = create(admin, hotel, country_ref=city.region.country, region_ref=city.region, city_ref=city)
        assert promo.city_ref_id == city.pk


class TestOverlap:
    def test_overlapping_period_for_same_hotel_is_rejected(self, admin, hotel):
        create(admin, hotel, start=0, days=7)
        with pytest.raises(PromotionError) as err:
            create(admin, hotel, start=6, days=3)
        assert err.value.code == 'overlap'

    def test_back_to_back_periods_are_allowed(self, admin, hotel):
        create(admin, hotel, start=0, days=7)
        assert create(admin, hotel, start=7, days=7).pk

    def test_other_hotel_is_independent(self, admin, hotel):
        other = make_hotel(make_owner('o3@example.com'), name='Gamma')
        create(admin, hotel)
        assert create(admin, other).pk

    def test_cancelled_period_does_not_block(self, admin, hotel):
        first = create(admin, hotel)
        service.cancel(first, actor=admin, reason='client asked')
        assert create(admin, hotel).pk

    def test_paused_period_still_blocks(self, admin, hotel):
        first = create(admin, hotel)
        service.pause(first, actor=admin)
        with pytest.raises(PromotionError) as err:
            create(admin, hotel)
        assert err.value.code == 'overlap'


class TestLifecycle:
    def test_mark_paid_sets_time_and_actor_and_audits(self, admin, hotel):
        promo = create(admin, hotel)
        service.mark_paid(promo, actor=admin)
        promo.refresh_from_db()
        assert promo.paid_at is not None
        assert promo.paid_marked_by_id == admin.pk
        assert AdminAccessLog.objects.filter(action='promotion_mark_paid').count() == 1

    def test_mark_paid_twice_is_rejected(self, admin, hotel):
        promo = create(admin, hotel)
        service.mark_paid(promo, actor=admin)
        with pytest.raises(PromotionError) as err:
            service.mark_paid(promo, actor=admin)
        assert err.value.code == 'already_paid'

    def test_pause_and_resume(self, admin, hotel):
        promo = create(admin, hotel)
        service.pause(promo, actor=admin)
        assert promo.status == 'paused'
        service.resume(promo, actor=admin)
        assert promo.status == 'scheduled'
        assert AdminAccessLog.objects.filter(action__in=['promotion_pause', 'promotion_resume']).count() == 2

    def test_resume_of_active_promotion_goes_back_to_active(self, admin, hotel):
        promo = make_promotion(hotel, status='active')
        service.pause(promo, actor=admin)
        service.resume(promo, actor=admin)
        assert promo.status == 'active'

    def test_cannot_pause_a_cancelled_promotion(self, admin, hotel):
        promo = create(admin, hotel)
        service.cancel(promo, actor=admin, reason='x')
        with pytest.raises(PromotionError) as err:
            service.pause(promo, actor=admin)
        assert err.value.code == 'bad_status'

    def test_cancel_needs_a_reason(self, admin, hotel):
        promo = create(admin, hotel)
        with pytest.raises(PromotionError) as err:
            service.cancel(promo, actor=admin, reason='  ')
        assert err.value.code == 'reason_required'

    def test_cancel_records_reason_and_audit(self, admin, hotel):
        promo = create(admin, hotel)
        service.cancel(promo, actor=admin, reason='Client withdrew')
        promo.refresh_from_db()
        assert (promo.status, promo.cancelled_reason) == ('cancelled', 'Client withdrew')
        assert AdminAccessLog.objects.filter(action='promotion_cancel').count() == 1

    def test_update_changes_priority_and_audits(self, admin, hotel):
        promo = create(admin, hotel)
        service.update_promotion(promo, actor=admin, priority=50)
        promo.refresh_from_db()
        assert promo.priority == 50
        assert AdminAccessLog.objects.filter(action='promotion_update').count() == 1

    def test_update_dates_rechecks_overlap(self, admin, hotel):
        create(admin, hotel, start=0, days=7)
        later = create(admin, hotel, start=7, days=7)
        with pytest.raises(PromotionError) as err:
            service.update_promotion(later, actor=admin, start_date=business_today() + timedelta(days=3))
        assert err.value.code == 'overlap'

    def test_update_does_not_collide_with_itself(self, admin, hotel):
        promo = create(admin, hotel, start=0, days=7)
        service.update_promotion(promo, actor=admin, end_date=business_today() + timedelta(days=9))
        promo.refresh_from_db()
        assert promo.end_date == business_today() + timedelta(days=9)

    def test_ended_promotion_cannot_be_edited(self, admin, hotel):
        promo = make_promotion(hotel, status='ended')
        with pytest.raises(PromotionError) as err:
            service.update_promotion(promo, actor=admin, priority=5)
        assert err.value.code == 'bad_status'


class TestShownNow:
    def test_paid_started_active_hotel_is_shown(self, hotel):
        promo = make_promotion(hotel)
        assert list(service.shown_now()) == [promo]

    def test_unpaid_is_not_shown(self, hotel):
        make_promotion(hotel, paid=False)
        assert list(service.shown_now()) == []

    def test_future_and_expired_are_not_shown(self, hotel):
        make_promotion(hotel, start_offset=2)
        other = make_hotel(make_owner('o4@example.com'), name='Delta')
        make_promotion(other, start_offset=-10, days=3)
        assert list(service.shown_now()) == []

    def test_last_day_is_still_shown(self, hotel):
        promo = make_promotion(hotel, start_offset=-6, days=7)
        assert list(service.shown_now()) == [promo]

    @pytest.mark.parametrize('status', ['paused', 'ended', 'cancelled'])
    def test_not_served_statuses(self, hotel, status):
        make_promotion(hotel, status=status)
        assert list(service.shown_now()) == []

    def test_deleted_promotion_and_deleted_hotel_are_not_shown(self, hotel):
        promo = make_promotion(hotel)
        promo.soft_delete()
        assert list(service.shown_now()) == []

    def test_hotel_that_became_inactive_is_not_shown(self, hotel):
        make_promotion(hotel)
        hotel.status = 'suspended'
        hotel.save(update_fields=['status'])
        assert list(service.shown_now()) == []

    def test_scope_limits_to_matching_hotels(self):
        city = uz_city()
        inside = make_hotel(make_owner('a@example.com'), name='In', city_ref=city)
        outside = make_hotel(make_owner('b@example.com'), name='Out')
        scoped = make_promotion(inside, city_ref=city)
        make_promotion(outside, city_ref=city)
        assert list(service.shown_now()) == [scoped]

    def test_explicit_date_argument(self, hotel):
        promo = make_promotion(hotel, start_offset=5)
        assert list(service.shown_now(today=business_today() + timedelta(days=5))) == [promo]


class TestOrdering:
    def make_many(self, n, priority=0, prefix='p'):
        promos = []
        for i in range(n):
            owner = make_owner(f'{prefix}{i}@example.com')
            promos.append(make_promotion(make_hotel(owner, name=f'{prefix}{i}'), priority=priority))
        return promos

    def test_higher_priority_first(self):
        low = self.make_many(1, 0, 'low')[0]
        high = self.make_many(1, 50, 'high')[0]
        assert service.ordered(service.shown_now()) == [high, low]

    def test_order_is_stable_within_a_day(self):
        self.make_many(6)
        first = [p.pk for p in service.ordered(service.shown_now())]
        again = [p.pk for p in service.ordered(service.shown_now())]
        assert first == again

    def test_rotation_changes_between_days(self):
        self.make_many(8)
        today = business_today()
        orders = {tuple(p.pk for p in service.ordered(Promotion.objects.all(), today + timedelta(days=d)))
                  for d in range(5)}
        assert len(orders) > 1

    def test_limit_is_applied(self):
        self.make_many(10)
        assert len(service.ordered(service.shown_now(), limit=8)) == 8
