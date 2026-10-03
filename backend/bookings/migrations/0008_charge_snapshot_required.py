# R6: every booking now has a charge snapshot (0007), so new rows must too.
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0007_backfill_charge_snapshot'),
    ]

    operations = [
        migrations.AlterField(
            model_name='booking', name='charge_currency',
            field=models.CharField(max_length=3),
        ),
        migrations.AlterField(
            model_name='booking', name='charge_amount',
            field=models.DecimalField(decimal_places=2, max_digits=14,
                                      validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AlterField(
            model_name='booking', name='exchange_rate',
            field=models.DecimalField(decimal_places=6, max_digits=18, help_text='UZS per one unit of currency'),
        ),
        migrations.AlterField(
            model_name='booking', name='exchange_rate_source',
            field=models.CharField(max_length=16),
        ),
    ]
