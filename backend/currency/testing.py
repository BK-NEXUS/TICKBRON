"""Test helper (R6): USD-priced hotels can only be booked once an exchange rate exists."""
from decimal import Decimal


def make_usd_rate(rate=Decimal('12000.00'), days_old=0):
    """Store an accepted CBU USD rate, as the scheduled fetch does in a running system."""
    from datetime import timedelta

    from currency.cbu import tashkent_today
    from currency.models import ExchangeRate

    return ExchangeRate.objects.create(currency='USD', rate=Decimal(rate), nominal=1, source='cbu.uz',
                                       status='accepted', rate_date=tashkent_today() - timedelta(days=days_old))
