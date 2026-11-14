from django.db import migrations, models
from django.db.models import F, OuterRef, Subquery


def repair_existing_rows(apps, schema_editor):
    """
    Make today's data satisfy the new constraints before they are added:
    - a night offered for more rooms than the room type has goes back to total_rooms;
    - a night with more rooms booked than offered is offered for exactly the booked rooms (the bookings
      are real and stay; this only stops new sales on that night);
    - a nightly price of 0 or less is emptied, so the rate plan's base price applies.
    """
    RoomInventory = apps.get_model('properties', 'RoomInventory')
    RoomType = apps.get_model('properties', 'RoomType')
    DateInventory = apps.get_model('properties', 'DateInventory')

    total = Subquery(RoomType.objects.filter(pk=OuterRef('room_type_id')).values('total_rooms')[:1])
    RoomInventory.objects.filter(available_rooms__gt=total).update(available_rooms=total)
    RoomInventory.objects.filter(booked_rooms__gt=F('available_rooms')).update(available_rooms=F('booked_rooms'))
    DateInventory.objects.filter(price__lte=0).update(price=None)


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0017_remove_city_level'),
    ]

    operations = [
        # The repair cannot be undone (the old wrong values are gone), and nothing needs it undone
        migrations.RunPython(repair_existing_rows, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='roominventory',
            constraint=models.CheckConstraint(
                condition=models.Q(('booked_rooms__lte', models.F('available_rooms'))),
                name='room_inventory_booked_lte_available',
            ),
        ),
        migrations.AddConstraint(
            model_name='dateinventory',
            constraint=models.CheckConstraint(
                condition=models.Q(('price__isnull', True), ('price__gt', 0), _connector='OR'),
                name='date_inventory_price_positive',
            ),
        ),
    ]
