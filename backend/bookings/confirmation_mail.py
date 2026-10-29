"""The guest's confirmation e-mail: the whole stay in uz, ru and en. Amounts and dates are the ones stored with the booking."""
from decimal import Decimal

from django.conf import settings
from django.template.loader import render_to_string

LANGUAGES = ('uz', 'ru', 'en')
LABELS = {'uz': 'Uz', 'ru': 'Ru', 'en': 'En'}

# One line per fact; {placeholders} are filled from `facts()`. Pay in cash at the hotel (no online payment).
LINES = {
    'uz': {
        'intro': "{code} raqamli broningiz tasdiqlandi.",
        'hotel': "Mehmonxona: {hotel}, {address}",
        'dates': "Kelish: {check_in}, ketish: {check_out} ({nights} tun)",
        'rooms': "Xona: {rooms}",
        'guests': "Mehmonlar soni: {guests}",
        'arrival': ("Kelish vaqti: {arrival}. Shu vaqtda kelmasangiz, mehmonxona yana {hours} soat kutadi, "
                    "undan keyin bron bekor qilinadi."),
        'total': "Jami: {total}. To'lov mehmonxonada, naqd pulda.",
    },
    'ru': {
        'intro': "Ваша бронь {code} подтверждена.",
        'hotel': "Отель: {hotel}, {address}",
        'dates': "Заезд: {check_in}, выезд: {check_out} (ночей: {nights})",
        'rooms': "Номер: {rooms}",
        'guests': "Гостей: {guests}",
        'arrival': ("Время прибытия: {arrival}. Если вы не приедете в это время, отель подождёт ещё {hours} ч., "
                    "после чего бронь будет отменена."),
        'total': "Итого: {total}. Оплата наличными в отеле.",
    },
    'en': {
        'intro': "Your booking {code} is confirmed.",
        'hotel': "Hotel: {hotel}, {address}",
        'dates': "Check-in: {check_in}, check-out: {check_out} ({nights} nights)",
        'rooms': "Room: {rooms}",
        'guests': "Guests: {guests}",
        'arrival': ("Arrival time: {arrival}. If you do not arrive then, the hotel waits {hours} more hours, "
                    "after which the booking is cancelled."),
        'total': "Total: {total}. You pay in cash at the hotel.",
    },
}


def money(amount, currency):
    """49 000 UZS has no decimals; every other currency keeps two."""
    amount = Decimal(amount)
    text = f'{amount:,.0f}' if currency == 'UZS' else f'{amount:,.2f}'
    return f'{text.replace(",", " ")} {currency}'


def _rooms(booking):
    return ', '.join(f'{item.room_type.name} x{item.number_of_rooms}'
                     for item in booking.booking_items.select_related('room_type'))


def facts(booking, language):
    hotel = booking.property
    return {
        'code': booking.confirmation_code, 'hotel': hotel.display_name(language), 'address': hotel.get_full_address(),
        'check_in': booking.check_in.isoformat(), 'check_out': booking.check_out.isoformat(),
        'nights': booking.number_of_nights, 'rooms': _rooms(booking), 'guests': booking.guest_count,
        'arrival': booking.expected_arrival_time.strftime('%H:%M') if booking.expected_arrival_time else '',
        'hours': settings.ARRIVAL_GRACE_HOURS, 'total': money(booking.charge_amount, booking.charge_currency),
    }


def _lines(booking, language):
    values = facts(booking, language)
    # Bookings made before the arrival time existed have none: that line is left out
    keys = [key for key in LINES[language] if key != 'arrival' or values['arrival']]
    return [LINES[language][key].format(**values) for key in keys]


def confirmation_body(booking, link):
    blocks = [{'label': LABELS[language], 'lines': _lines(booking, language)} for language in LANGUAGES]
    return render_to_string('bookings/confirmation.txt', {'blocks': blocks, 'link': link})
