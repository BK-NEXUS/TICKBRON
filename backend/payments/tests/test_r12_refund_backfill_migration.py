"""
R12 1c: payments/0004 turns refunds made before the Refund model into `succeeded`
Refund rows, and its reverse removes exactly those rows (0003's reverse drops the table).

Runs the real migration executor against the test database.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from bookings.tests.r12_helpers import make_booking
from common.dates import business_today
from payments.models import PaymentAuditLog, PaymentTransaction, Refund
from properties.models import Property, PropertyType
from users.models import User

BEFORE = [('payments', '0003_refunds')]
AFTER = [('payments', '0004_backfill_refunds')]
NO_TABLE = [('payments', '0002_alter_paymentauditlog_action')]


class RefundBackfillMigration(TransactionTestCase):

    def setUp(self):
        super().setUp()
        if connection.vendor != 'postgresql':
            self.skipTest('Migration executor tests need PostgreSQL')
        staff = User.objects.create_user(email='s@example.com', password='x', is_staff=True)
        guest = User.objects.create_user(email='g@example.com', password='x')
        hotel = Property.objects.create(
            owner=staff, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'),
            status='active', max_guests=2, bedrooms=1, bathrooms=1, address_line1='1', city='Tashkent',
            country='Uzbekistan', base_price=500000, currency='UZS',
        )
        self.staff = staff
        self.payments = {}
        for key, status in [('full_logged', 'refunded'), ('partial_logged', 'partially_refunded'),
                            ('full_unlogged', 'refunded'), ('partial_unlogged', 'partially_refunded'),
                            ('paid', 'completed')]:
            booking = make_booking(hotel, guest, business_today() + timedelta(days=5), nights=2)
            self.payments[key] = PaymentTransaction.objects.create(
                idempotency_key=key, booking=booking, provider='payme', amount=booking.charge_amount,
                currency=booking.charge_currency, status=status, provider_transaction_id=f'p-{key}',
            )
        for key, amount, cancel in [('full_logged', '1000000.00', True), ('partial_logged', '300000.00', False)]:
            tx = self.payments[key]
            PaymentAuditLog.objects.create(
                action='payment_refunded', payment_transaction=tx, booking=tx.booking, old_status='completed',
                new_status=tx.status, actor=staff, details={'refund_amount': amount, 'cancel_booking': cancel},
            )
        self.executor = MigrationExecutor(connection)
        self._migrate(BEFORE)   # reverse of 0004 first: start without backfilled rows

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def _migrate(self, target):
        self.executor.loader.build_graph()
        self.executor.migrate(target)

    def test_forward_creates_refunds_and_reverse_removes_them(self):
        assert not Refund.objects.exists()
        self._migrate(AFTER)

        rows = {r.payment_id: r for r in Refund.objects.all()}
        assert set(rows) == {self.payments['full_logged'].id, self.payments['partial_logged'].id,
                             self.payments['full_unlogged'].id}   # partial without an amount: skipped
        full = rows[self.payments['full_logged'].id]
        assert (full.amount, full.reason, full.status, full.created_by_id) == (
            Decimal('1000000.00'), 'cancel', 'succeeded', self.staff.id)
        partial = rows[self.payments['partial_logged'].id]
        assert (partial.amount, partial.reason) == (Decimal('300000.00'), 'staff')
        assert rows[self.payments['full_unlogged'].id].amount == self.payments['full_unlogged'].amount
        assert all(r.idempotency_key.startswith('backfill:') for r in rows.values())

        # A refund created after the migration survives its reverse
        Refund.objects.create(payment=self.payments['paid'], booking=self.payments['paid'].booking,
                              amount=Decimal('1000'), currency='UZS', reason='staff', idempotency_key='later')
        self._migrate(BEFORE)
        assert list(Refund.objects.values_list('idempotency_key', flat=True)) == ['later']

        Refund.objects.filter(idempotency_key='later').delete()
        self._migrate(NO_TABLE)
        with connection.cursor() as cursor:
            assert 'payment_refunds' not in connection.introspection.table_names(cursor)

    def test_running_forward_twice_is_not_possible_but_rerun_after_reverse_is_identical(self):
        self._migrate(AFTER)
        first = sorted(Refund.objects.values_list('payment_id', 'amount', 'reason'))
        self._migrate(BEFORE)
        self._migrate(AFTER)
        assert sorted(Refund.objects.values_list('payment_id', 'amount', 'reason')) == first
