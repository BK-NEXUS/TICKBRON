"""
seed_demo management command ı ushın testler (jergilikli demo maǵlıwmat).
"""
from io import StringIO

import pytest
from django.core.management import CommandError, call_command
from django.utils import timezone

from properties.models import DateInventory, Property, RatePlan, RoomType
from users.models import User


def run_seed():
    out = StringIO()
    call_command('seed_demo', stdout=out)
    return out.getvalue()


@pytest.mark.django_db
class TestSeedDemo:
    @pytest.fixture(autouse=True)
    def debug_on(self, settings):
        settings.DEBUG = True

    def test_creates_demo_users_with_roles(self):
        output = run_seed()

        admin = User.objects.get(email='admin@tickbron.demo')
        owner = User.objects.get(email='owner@tickbron.demo')
        guest = User.objects.get(email='guest@tickbron.demo')
        assert admin.is_superuser and admin.is_staff
        assert owner.role.name == 'hotel-owner' and not owner.is_staff
        assert guest.role is None and not guest.is_staff
        # Programmist kire alıwı ushın kirisiw maǵlıwmatı basıp shıǵarıladı
        for user in (admin, owner, guest):
            assert user.email in output

    def test_creates_three_active_properties_with_90_days_of_inventory(self):
        run_seed()

        properties = Property.objects.filter(owner__email='owner@tickbron.demo')
        assert sorted(properties.values_list('city', flat=True)) == ['Bukhara', 'Samarkand', 'Tashkent']
        assert all(p.status == 'active' and p.approved_at is not None for p in properties)
        assert all(p.translations.filter(language='en').exists() for p in properties)
        # Geografiya sózligine baylanıstırılǵan
        assert sorted(properties.values_list('region_ref__name_en', flat=True)) == ['Bukhara', 'Samarkand', 'Tashkent']
        assert set(properties.values_list('country_ref__code', flat=True)) == {'UZ'}

        today = timezone.localdate()
        for rate_plan in RatePlan.objects.filter(room_type__property__in=properties):
            dates = list(rate_plan.date_inventory.values_list('date', flat=True))
            assert len(dates) == 90
            assert min(dates) == today
        assert RoomType.objects.filter(property__in=properties).count() >= 3

    def test_running_twice_does_not_duplicate(self):
        run_seed()
        counts = (User.objects.count(), Property.objects.count(), RoomType.objects.count(),
                  RatePlan.objects.count(), DateInventory.objects.count())

        run_seed()

        assert (User.objects.count(), Property.objects.count(), RoomType.objects.count(),
                RatePlan.objects.count(), DateInventory.objects.count()) == counts

    def test_keeps_booked_rooms_on_rerun(self):
        run_seed()
        inventory = DateInventory.objects.filter(rate_plan__room_type__property__city='Tashkent').first()
        inventory.booked_rooms = 1
        inventory.save(update_fields=['booked_rooms'])

        run_seed()

        inventory.refresh_from_db()
        assert inventory.booked_rooms == 1


@pytest.mark.django_db
def test_refuses_to_run_without_debug(settings):
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command('seed_demo', stdout=StringIO())
    assert not User.objects.filter(email='admin@tickbron.demo').exists()


@pytest.mark.django_db
@pytest.mark.no_default_exchange_rate  # seed demo kursın tek ele joq bolǵanda saqlaydı
class TestSeedDemoExchangeRate:
    """R6: demo mehmanxanalar USD de bahalanǵan, sol sebepli jergilikli database ge olardı bronlaw ushın kurs kerek."""

    @pytest.fixture(autouse=True)
    def debug_on(self, settings):
        settings.DEBUG = True

    def test_demo_rate_when_none_exists(self):
        from currency.models import ExchangeRate
        from currency.rates import current_rate

        output = run_seed()

        rate = current_rate('USD')
        assert rate is not None and rate.source == 'demo'
        assert 'fetch_exchange_rates' in output
        run_seed()
        # dollar, tenge hám rubl ushın bir-birden demo kurs, hám ekinshi isleniw hesh qanday qospaydı
        assert ExchangeRate.objects.filter(source='demo').count() == 3

    def test_demo_rates_for_every_currency_the_site_shows(self):
        from currency.rates import current_rate

        run_seed()

        for code in ('USD', 'KZT', 'RUB'):
            rate = current_rate(code)
            assert rate is not None and rate.source == 'demo', code

    def test_a_real_rate_of_one_currency_is_left_alone(self):
        from decimal import Decimal
        from currency.cbu import tashkent_today
        from currency.models import ExchangeRate

        ExchangeRate.objects.create(currency='KZT', rate=Decimal('24.510000'), nominal=1, source='cbu.uz',
                                    status='accepted', rate_date=tashkent_today())
        run_seed()
        assert not ExchangeRate.objects.filter(currency='KZT', source='demo').exists()
        assert ExchangeRate.objects.filter(currency='RUB', source='demo').exists()

    def test_real_rate_is_left_alone(self):
        from decimal import Decimal
        from currency.cbu import tashkent_today
        from currency.models import ExchangeRate

        ExchangeRate.objects.create(currency='USD', rate=Decimal('11772.95'), nominal=1, source='cbu.uz',
                                    status='accepted', rate_date=tashkent_today())
        run_seed()
        # haqıyqıy dollar kursı demo kurs penen almastırılmaydı yamasa eki ese bolmaydı (tenge hám rubl ele demo kurs aladı)
        assert not ExchangeRate.objects.filter(currency='USD', source='demo').exists()
