"""Admin jazıw endpoint leri ushın audit járdemshileri (N-17). Tek id hám jeke emes faktlar."""
from admin_panel.models import AdminAccessLog


class AuditedModelViewSetMixin:
    """
    ModelViewSet tiń hár tabıslı create, update hám delete inen keyin bir AdminAccessLog qatarın jazadı:
    `<audit_name>_create|update|delete` obyekt id si menen (hám geografiya dárejesi).
    Qabıllanbaǵan yamasa jaramsız sorawda qatar jazılmastan aldın qátelik kóteriledi.
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
