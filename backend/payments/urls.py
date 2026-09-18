"""
URL configuration for TICKBRON payment API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentTransactionViewSet, WebhookEventViewSet, PaymentAuditLogViewSet, webhook_endpoint

router = DefaultRouter()
router.register(r'transactions', PaymentTransactionViewSet, basename='paymenttransaction')
router.register(r'webhooks', WebhookEventViewSet, basename='webhookevent')
router.register(r'audit-logs', PaymentAuditLogViewSet, basename='paymentauditlog')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/<str:provider>/', webhook_endpoint, name='webhook'),
]