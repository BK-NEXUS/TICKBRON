"""Test járdemshisi (R6): USD bahalı mehmanxanalardı tek valyuta kursı bolǵannan keyin bronlap boladı."""
from decimal import Decimal


def make_usd_rate(rate=Decimal('12000.00'), days_old=0):
    """Qabıllanǵan CBU USD kursın saqlaw, isleytuǵın sistemada rejelestirilgen alıw islegenindey."""
    from datetime import timedelta

    from currency.cbu import tashkent_today
    from currency.models import ExchangeRate

    return ExchangeRate.objects.create(currency='USD', rate=Decimal(rate), nominal=1, source='cbu.uz',
                                       status='accepted', rate_date=tashkent_today() - timedelta(days=days_old))
