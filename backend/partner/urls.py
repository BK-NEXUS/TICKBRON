"""
URL configuration for partner app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from partner.views import (
    PartnerAPIRootView, PartnerPropertyViewSet, PartnerRoomTypeViewSet,
    PartnerRatePlanViewSet, PartnerDateInventoryViewSet, PartnerRoomInventoryViewSet,
    partner_property_photo_upload, partner_bookings
)

app_name = 'partner'

router = DefaultRouter()
router.APIRootView = PartnerAPIRootView
router.register(r'properties', PartnerPropertyViewSet, basename='partner-property')
router.register(r'rooms', PartnerRoomTypeViewSet, basename='partner-room')
router.register(r'rates', PartnerRatePlanViewSet, basename='partner-rate')
router.register(r'inventory', PartnerDateInventoryViewSet, basename='partner-inventory')
router.register(r'room-inventory', PartnerRoomInventoryViewSet, basename='partner-room-inventory')

urlpatterns = [
    path('', include(router.urls)),
    path('properties/<int:property_id>/photos/', partner_property_photo_upload, name='partner-property-photo-upload'),
    path('bookings/', partner_bookings, name='partner-bookings'),
]
