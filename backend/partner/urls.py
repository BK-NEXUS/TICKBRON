"""
URL configuration for partner app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from partner.status import partner_status
from partner.views import (
    PartnerAPIRootView, PartnerPropertyViewSet, PartnerRoomTypeViewSet,
    PartnerRatePlanViewSet, PartnerDateInventoryViewSet, PartnerRoomInventoryViewSet,
    PartnerBlockViewSet, partner_property_photo_upload, partner_bookings
)

app_name = 'partner'

router = DefaultRouter()
router.APIRootView = PartnerAPIRootView
router.register(r'properties', PartnerPropertyViewSet, basename='partner-property')
router.register(r'rooms', PartnerRoomTypeViewSet, basename='partner-room')
router.register(r'rates', PartnerRatePlanViewSet, basename='partner-rate')
router.register(r'inventory', PartnerDateInventoryViewSet, basename='partner-inventory')
router.register(r'room-inventory', PartnerRoomInventoryViewSet, basename='partner-room-inventory')
router.register(r'blocks', PartnerBlockViewSet, basename='partner-block')

urlpatterns = [
    path('status/', partner_status, name='partner-status'),
    path('', include(router.urls)),
    path('properties/<int:property_id>/photos/', partner_property_photo_upload, name='partner-property-photo-upload'),
    path('bookings/', partner_bookings, name='partner-bookings'),
]
