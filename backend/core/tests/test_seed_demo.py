"""
Tests for the seed_demo management command (local demo data).
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
        # Credentials are printed so the developer can log in
        for user in (admin, owner, guest):
            assert user.email in output

    def test_creates_three_active_properties_with_90_days_of_inventory(self):
        run_seed()

        properties = Property.objects.filter(owner__email='owner@tickbron.demo')
        assert sorted(properties.values_list('city', flat=True)) == ['Bukhara', 'Samarkand', 'Tashkent']
        assert all(p.status == 'active' and p.approved_at is not None for p in properties)
        assert all(p.translations.filter(language='en').exists() for p in properties)

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
