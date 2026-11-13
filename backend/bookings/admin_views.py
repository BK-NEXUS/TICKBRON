"""
Túngi avtomat juwmaqlawdıń super-admin view si (R12), /api/v1/admin-panel/ astında.

GET auto-completion/status/  sońǵı haqıyqıy isleniw (waqıt, trigger, juwmaqlanǵan, sátsiz) hám
                             házir keyingi isleniwdi kútip turǵan pitken turıwlar sanı.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from admin_panel.views import IsSuperAdmin
from bookings.completion import finished_stays
from bookings.models import AutoCompletionRun

SCHEDULE_TEXT = '00:05 Asia/Tashkent'


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def auto_completion_status(request):
    run = AutoCompletionRun.objects.first()
    last_run = None if run is None else {
        'trigger': run.trigger, 'started_at': run.started_at, 'finished_at': run.finished_at,
        'changed': run.changed, 'failed': run.failed,
    }
    return Response({'schedule': SCHEDULE_TEXT, 'last_run': last_run, 'waiting': finished_stays().count()})
