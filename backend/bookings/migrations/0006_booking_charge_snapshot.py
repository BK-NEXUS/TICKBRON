# R6: what the guest is charged. Nullable here; 0007 fills existing rows, 0008 makes them required.
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bookings', '0005_status_indexes'),
        # The R6 guard (unsupported property currencies) runs first and stops everything
        ('currency', '0001_exchange_rates'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking', name='charge_currency',
            field=models.CharField(max_length=3, null=True),
        ),
        migrations.AddField(
            model_name='booking', name='charge_amount',
            field=models.DecimalField(decimal_places=2, max_digits=14, null=True,
                                      validators=[django.core.validators.MinValueValidator(0)]),
        ),
        migrations.AddField(
            model_name='booking', name='exchange_rate',
            field=models.DecimalField(decimal_places=6, max_digits=18, null=True,
                                      help_text='UZS per one unit of currency'),
        ),
        migrations.AddField(
            model_name='booking', name='exchange_rate_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='booking', name='exchange_rate_source',
            field=models.CharField(max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='booking', name='exchange_rate_stale',
            field=models.BooleanField(default=False),
        ),
    ]
