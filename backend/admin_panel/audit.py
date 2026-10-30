"""Audit helpers for admin write endpoints (N-17). Ids and non-personal facts only."""
from admin_panel.models import AdminAccessLog


class AuditedModelViewSetMixin:
    """
    Writes one AdminAccessLog row after every successful create, update and delete of a
    ModelViewSet: `<audit_name>_create|update|delete` with the object id (and the geography
    level). A refused or invalid request raises before the row is written.
    """
    audit_name = None
    audit_level = None

    def _audit_details(self, object_id):
        details = {'object_id': object_id}
        if self.audit_level:
            details['level'] = self.audit_level
        return details

    def audit(self, verb, object_id):
        AdminAccessLog.record(self.request.user, f'{self.audit_name}_{verb}', details=self._audit_details(object_id))

    def perform_create(self, serializer):
        instance = serializer.save()
        self.audit('create', instance.pk)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.audit('update', instance.pk)

    def perform_destroy(self, instance):
        object_id = instance.pk
        super().perform_destroy(instance)
        self.audit('delete', object_id)
