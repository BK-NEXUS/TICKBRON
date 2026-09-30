"""
Geography plan G2: fill Property.country_ref / region_ref / city_ref from the old text
fields (see geography/mapping.py). Unmatched values stay NULL and are printed in a report.
The text fields are not changed. Reverse: clear the refs.
"""
from django.db import migrations


def forward(apps, schema_editor):
    from geography.mapping import format_report, map_properties

    report = map_properties(
        apps.get_model('properties', 'Property'), apps.get_model('geography', 'Country'),
        apps.get_model('geography', 'Region'), apps.get_model('geography', 'City'),
    )
    if report['properties']:
        print('\n' + format_report(report))


def backward(apps, schema_editor):
    apps.get_model('properties', 'Property').objects.update(country_ref=None, region_ref=None, city_ref=None)


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0012_property_geography_refs'),
        ('geography', '0002_initial_data'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
