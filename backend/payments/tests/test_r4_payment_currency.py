"""
R4 security review: a payment must be in the booking's currency.

The amount was already checked against booking.total_price, but the currency
was taken from the client, so a 300 USD booking could be "paid" with 300 UZS.
"""
from rest_framework import status

from payments.models import PaymentTransaction
from payments.tests.test_payment_security import TRANSACTIONS_URL, PaymentSecurityTestBase, error_details


class TestPaymentCurrencyMatchesBooking(PaymentSecurityTestBase):

    def test_other_currency_with_same_amount_is_rejected(self):
        response = self.client.post(
            TRANSACTIONS_URL, self._payment_data(self.booking, 'k-cur-uzs', currency='UZS'), format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'currency' in error_details(response)
        assert not PaymentTransaction.objects.filter(idempotency_key='k-cur-uzs').exists()

    def test_booking_currency_is_accepted(self):
        response = self.client.post(
            TRANSACTIONS_URL, self._payment_data(self.booking, 'k-cur-usd'), format='json'
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert PaymentTransaction.objects.get(idempotency_key='k-cur-usd').currency == 'USD'
