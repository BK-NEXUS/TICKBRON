"""R12 phase 3: two approvals at once refund once; the OpenAPI schema still builds without collisions."""
import io
import threading

import pytest
from django.core.management import call_command
from django.db import connection

from bookings.models import NoShowReport
from bookings.noshow import NoShowError, approve_report
from bookings.tests.r12b_helpers import COMMENT, DECISION, past_stay, world  # noqa: F401
from payments.models import Refund


@pytest.mark.django_db(transaction=True)
def test_two_concurrent_approves_refund_once(world):
    booking = past_stay(world)
    report = NoShowReport.objects.create(
        booking=booking, property=booking.property, created_by=world['owner'], comment=COMMENT)
    barrier = threading.Barrier(2)
    results = []

    def worker():
        try:
            barrier.wait(timeout=10)
            approve_report(report.pk, world['staff'], DECISION)
            results.append('ok')
        except NoShowError as error:
            results.append(error.code)
        finally:
            connection.close()

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert sorted(results) == ['not_pending', 'ok']
    assert Refund.objects.filter(booking=booking).count() == 1


def test_openapi_schema_builds_without_collisions():
    stderr = io.StringIO()
    call_command('spectacular', stdout=io.StringIO(), stderr=stderr)
    assert 'Warning' not in stderr.getvalue()
    assert 'Error' not in stderr.getvalue()
