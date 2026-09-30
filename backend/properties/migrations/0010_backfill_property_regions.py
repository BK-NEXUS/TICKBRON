"""
Status plan S1: the region of a property is its existing `state` field.
Fill it from the city where the region is obvious (Tashkent, Samarkand, Bukhara).
Never overwrites a region that is already set; the reverse migration is a no-op.
"""
from django.db import migrations


def backfill(apps, schema_editor):
    from properties.regions import backfill_regions_from_city

    backfill_regions_from_city(apps.get_model('properties', 'Property'))


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0009_roomblock'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
