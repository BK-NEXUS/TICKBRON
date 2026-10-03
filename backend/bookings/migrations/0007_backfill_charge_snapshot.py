"""
R6: existing bookings were priced and paid in their own currency, so their snapshot
says exactly that: charged in `currency`, amount = total_price, rate 1, rate date =
the day the booking was made, source 'legacy' ('identity' for UZS rows). Reverse is a
no-op: 0006's reverse drops the columns.
"""
from django.db import migrations

BATCH = 1000


def backfill(apps, schema_editor):
    Booking = apps.get_model('bookings', 'Booking')
    rows = Booking._base_manager.filter(charge_currency__isnull=True).only('id', 'currency', 'total_price', 'created_at')
    batch = []
    for booking in rows.iterator(chunk_size=BATCH):
        booking.charge_currency = booking.currency
        booking.charge_amount = booking.total_price
        booking.exchange_rate = 1
        booking.exchange_rate_date = booking.created_at.date()
        booking.exchange_rate_source = 'identity' if booking.currency == 'UZS' else 'legacy'
        batch.append(booking)
        if len(batch) >= BATCH:
            _write(Booking, batch)
            batch = []
    _write(Booking, batch)


def _write(Booking, batch):
    if batch:
        Booking._base_manager.bulk_update(batch, [
            'charge_currency', 'charge_amount', 'exchange_rate', 'exchange_rate_date', 'exchange_rate_source',
        ])


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0006_booking_charge_snapshot'),
    ]

    operations = [
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
