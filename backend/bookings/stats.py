"""
Admin hám partner Status bólimleri ortaq paydalanatuǵın bron statistikası.

R12: anıqlamalar bookings/metrics.py de (mehmanlar = adamlar, unikal mijozlar,
túnler, turıwlar, dáramat = hár valyuta boyınsha juwmaqlanǵan bronlardıń jámi bahası, dáwirler, seriyalar).
Bul modul eski ashıq atlardı jińishke wrapper retinde saqlaydı, sonda eski shaqırıwshılar islewin dawam etedi:

- parse_period, parse_year, InvalidPeriod, counted_q, counted_bookings, available_years,
  COUNTED_STATUSES, PERIOD_ALL: metrics ten qayta eksport etiledi.
- revenue_by / revenue_total / metric_totals(bookings): aldınan filterlengen queryset ushın
  R12 ge shekemgi forma - ondaǵı `revenue` bron mánisi (hár bron valyutası boyınsha SUM(total_price),
  metrics.booking_value_*) hám `guests` ayrıqsha akkauntlar
  (metrics `unique_customers`). Status view leri metrics ti tikkeley paydalanadı.

Barlıq jıynaqlaw database de isleydi; Python tek aldınan jıynaqlanǵan qatarlardı qayta qurıp shıǵadı.
"""
from django.db.models import Count

from bookings.metrics import (  # noqa: F401  (re-exported)
    COUNTED_STATUSES, PERIOD_ALL, InvalidPeriod, available_years, booking_value_by, booking_value_total,
    counted_bookings, counted_q, parse_period, parse_year,
)


def commission_amount(gross_revenue, currency):
    """
    Bronnıń jalpı mánisinen platforma komissiyası.

    KOMISSIYA ELE ANIQLANBAǴAN: qaǵıydanı qosıwdıń birden-bir orını usı.
    Sol waqıtqa shekem None qaytaradı, hám Status view leri komissiyanı xabarlamaydı.
    """
    return None


def revenue_by(bookings, key):
    """Bron mánisiniń {kilt mánisi: [{'currency', 'amount'}, ...]} ı (R12 ge shekemgi `revenue`)."""
    return booking_value_by(bookings, key)


def revenue_total(bookings):
    """Bron mánisiniń [{'currency', 'amount'}, ...] ı (R12 ge shekemgi `revenue`)."""
    return booking_value_total(bookings)


def metric_totals(bookings):
    """R12 ge shekemgi {'bookings', 'guests' (ayrıqsha akkauntlar), 'revenue' (bron mánisi)}."""
    totals = bookings.aggregate(bookings=Count('id'), guests=Count('guest', distinct=True))
    return {'bookings': totals['bookings'], 'guests': totals['guests'], 'revenue': revenue_total(bookings)}
