"""
Plain English names for the Uzbek regions (2026-10-02): "Samarkand Region" -> "Samarkand", "Tashkent City" ->
"Tashkent", and so on. Only the English names change: the uz/ru names (the official forms) and the slugs
(stable keys) stay. "Tashkent Region" and the Republic of Karakalpakstan keep their names, so "Tashkent"
(the city) and "Tashkent Region" remain two regions.

geography/0002 is applied and untouched; this renames its rows. A region whose name an admin has edited
since (it no longer holds the old name) is left alone, and so is a rename that would clash with another
region of the country. Properties keep their text `state` in step. The reverse migration swaps back.
"""
from django.db import migrations

RENAMES = [
    ('Tashkent City', 'Tashkent'),
    ('Samarkand Region', 'Samarkand'),
    ('Bukhara Region', 'Bukhara'),
    ('Khorezm Region', 'Khorezm'),
    ('Fergana Region', 'Fergana'),
    ('Andijan Region', 'Andijan'),
    ('Namangan Region', 'Namangan'),
    ('Kashkadarya Region', 'Kashkadarya'),
    ('Surkhandarya Region', 'Surkhandarya'),
    ('Navoi Region', 'Navoi'),
    ('Jizzakh Region', 'Jizzakh'),
    ('Sirdarya Region', 'Sirdarya'),
]


def _rename(apps, pairs):
    Region = apps.get_model('geography', 'Region')
    Property = apps.get_model('properties', 'Property')
    for old, new in pairs:
        for region in Region.objects.filter(country__code='UZ', name_en=old):
            if Region.objects.filter(country_id=region.country_id, name_en=new).exists():
                continue  # would clash with another region of the country
            Region.objects.filter(pk=region.pk).update(name_en=new)
            Property.objects.filter(region_ref_id=region.pk, state=old).update(state=new)


def forward(apps, schema_editor):
    _rename(apps, RENAMES)


def backward(apps, schema_editor):
    _rename(apps, [(new, old) for old, new in RENAMES])


class Migration(migrations.Migration):

    dependencies = [
        ('geography', '0002_initial_data'),
        ('properties', '0013_map_property_geography'),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
