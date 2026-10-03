"""
R6 migration guard (decision B): run as the first operation of the first R6
migration. If any property, room type or rate plan is priced in a currency that is
not supported, the migration stops before anything has changed.
"""
from common.money import SUPPORTED_BASE_CURRENCIES


def check_property_currencies(apps, schema_editor):
    Property = apps.get_model('properties', 'Property')
    RoomType = apps.get_model('properties', 'RoomType')
    RatePlan = apps.get_model('properties', 'RatePlan')

    problems = []
    for label, model in (('property', Property), ('room type', RoomType), ('rate plan', RatePlan)):
        rows = model.objects.exclude(currency__in=SUPPORTED_BASE_CURRENCIES).order_by('id')
        for row_id, currency in rows.values_list('id', 'currency'):
            problems.append(f'{label} id={row_id} currency={currency}')
    if problems:
        allowed = ', '.join(SUPPORTED_BASE_CURRENCIES)
        raise RuntimeError(
            'R6 currency migration stopped; nothing was changed.\n'
            f'Only {allowed} are supported as a property currency. Unsupported rows:\n  '
            + '\n  '.join(problems) + '\n'
            'How to fix: decide the real price in USD or UZS with the hotel owner and set `currency` (and the '
            'prices) of the property, its room types and rate plans, then run migrate again. On a development '
            'database with demo data, delete the demo hotels and run `python manage.py seed_demo_stats` again '
            '(it now creates USD hotels).'
        )
