"""
R12 1c: refunds made before the Refund model become `succeeded` Refund rows.

Before R12 a refund was only a payment status (`refunded` / `partially_refunded`) plus a
`payment_refunded` PaymentAuditLog row with the amount as text. Each such audit row
becomes one Refund (amount, reason cancel/staff, created_by, time). A `refunded`
payment without an audit row gets one refund of its full amount. A
`partially_refunded` payment without an audit row is reported and skipped (the amount
is unknown; never invented). Refunds that would exceed the payment are reported and
skipped. Keys `backfill:<payment id>:<n>`; reverse deletes exactly those rows.
"""
from decimal import Decimal, InvalidOperation

from django.db import migrations

BATCH = 1000


def backfill_refunds(apps, schema_editor):
    PaymentTransaction = apps.get_model('payments', 'PaymentTransaction')
    PaymentAuditLog = apps.get_model('payments', 'PaymentAuditLog')
    Refund = apps.get_model('payments', 'Refund')

    payments = (PaymentTransaction._base_manager.filter(status__in=('refunded', 'partially_refunded'))
                .order_by('pk').only('id', 'booking_id', 'amount', 'currency', 'status'))
    created, skipped = 0, []
    for payment in payments.iterator(chunk_size=BATCH):
        logs = list(PaymentAuditLog._base_manager.filter(payment_transaction_id=payment.pk, action='payment_refunded')
                    .order_by('created_at', 'pk'))
        rows = []
        for log in logs:
            details = log.details or {}
            try:
                amount = Decimal(str(details.get('refund_amount')))
            except (InvalidOperation, ValueError):
                amount = None
            if amount is None or not amount.is_finite() or amount <= 0:
                amount = payment.amount if payment.status == 'refunded' and not rows else None
            if amount is None:
                continue
            rows.append((amount, 'cancel' if details.get('cancel_booking') else 'staff', log.actor_id, log.created_at))
        if not rows:
            if payment.status != 'refunded':
                skipped.append(f'payment {payment.pk}: partially refunded, amount unknown')
                continue
            rows.append((payment.amount, 'staff', None, None))
        if sum(amount for amount, *_ in rows) > payment.amount:
            skipped.append(f'payment {payment.pk}: recorded refunds exceed the payment')
            continue
        for number, (amount, reason, actor_id, when) in enumerate(rows, start=1):
            refund = Refund.objects.create(
                payment_id=payment.pk, booking_id=payment.booking_id, amount=amount, currency=payment.currency,
                reason=reason, status='succeeded', idempotency_key=f'backfill:{payment.pk}:{number}',
                provider_reference='backfill', created_by_id=actor_id,
            )
            if when is not None:
                Refund.objects.filter(pk=refund.pk).update(created_at=when, updated_at=when)
            created += 1
    if created or skipped:
        print(f'\n  Refund backfill: {created} refund row(s) created, {len(skipped)} payment(s) skipped')
        for line in skipped:
            print(f'    skipped {line}')


def remove_backfilled(apps, schema_editor):
    Refund = apps.get_model('payments', 'Refund')
    Refund.objects.filter(idempotency_key__startswith='backfill:').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_refunds'),
    ]

    operations = [
        migrations.RunPython(backfill_refunds, remove_backfilled),
    ]
