from django.db import migrations
from django.db.models import Sum


def populate_room_inventory(apps, schema_editor):
    """
    Backfill RoomInventory (audit #31, Phase 3 step 3.2) from the existing
    per-rate-plan DateInventory rows and active bookings. DateInventory rows
    are read only, never written.

    For each (room_type, date) that has at least one DateInventory row:
      available_rooms = min(room_type.total_rooms, max available_rooms over its rate plans)
      booked_rooms = rooms held by pending/confirmed bookings of that room type on that
                     date (recalculated from Booking/BookingItem, not from old counters)
      is_available = True if any of its rate plans is open on that date

    A date already oversold (booked_rooms > available_rooms) is left as computed,
    not clamped, and listed in the printed report.
    """
    RoomType = apps.get_model('properties', 'RoomType')
    DateInventory = apps.get_model('properties', 'DateInventory')
    RoomInventory = apps.get_model('properties', 'RoomInventory')
    BookingItem = apps.get_model('bookings', 'BookingItem')

    oversold = []
    to_create = []

    for room_type in RoomType.objects.all():
        dates = DateInventory.objects.filter(
            rate_plan__room_type=room_type, is_deleted=False,
        ).order_by().values_list('date', flat=True).distinct()

        for date in dates:
            date_rows = list(DateInventory.objects.filter(
                rate_plan__room_type=room_type, date=date, is_deleted=False,
            ))
            available = min(
                room_type.total_rooms,
                max((row.available_rooms for row in date_rows), default=0),
            )
            is_available = any(row.is_available for row in date_rows)

            booked = BookingItem.objects.filter(
                room_type=room_type,
                is_deleted=False,
                booking__status__in=('pending', 'confirmed'),
                booking__is_deleted=False,
                booking__check_in__lte=date,
                booking__check_out__gt=date,
            ).aggregate(total=Sum('number_of_rooms'))['total'] or 0

            to_create.append(RoomInventory(
                room_type=room_type, date=date,
                available_rooms=available, booked_rooms=booked, is_available=is_available,
            ))
            if booked > available:
                oversold.append((room_type.pk, date, available, booked))

    if to_create:
        RoomInventory.objects.bulk_create(to_create)

    if oversold:
        lines = '\n'.join(
            f'  room_type={room_type_id} date={date} available={available} booked={booked}'
            for room_type_id, date, available, booked in oversold
        )
        print(
            f'\n[0008_populate_room_inventory] {len(oversold)} already-oversold date(s), '
            f'left as computed:\n{lines}'
        )


def remove_room_inventory(apps, schema_editor):
    """Reverse: RoomInventory held nothing before this migration populated it."""
    RoomInventory = apps.get_model('properties', 'RoomInventory')
    RoomInventory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0007_room_inventory'),
        ('bookings', '0004_booking_reference_code'),
    ]

    operations = [
        migrations.RunPython(populate_room_inventory, remove_room_inventory),
    ]
