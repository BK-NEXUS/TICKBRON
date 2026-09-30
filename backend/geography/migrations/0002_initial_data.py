"""
Initial Country > Region > City data (geography/data.py). Idempotent; the reverse
migration leaves the rows in place (they may be referenced by then).
"""
from django.db import migrations


def load(apps, schema_editor):
    from geography.data import load_geography

    load_geography(apps.get_model('geography', 'Country'), apps.get_model('geography', 'Region'),
                   apps.get_model('geography', 'City'))


class Migration(migrations.Migration):

    dependencies = [
        ('geography', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load, migrations.RunPython.noop),
    ]
