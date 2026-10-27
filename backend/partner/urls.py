"""
URL configuration for partner app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from bookings.views_noshow import (
    partner_no_show_report_create, partner_no_show_report_withdraw, partner_no_show_reports,
)
from partner.status import partner_status, partner_status_arrivals, partner_status_hotel, partner_status_rooms
from partner.views import (
    PartnerAPIRootView, PartnerPropertyViewSet, PartnerRoomTypeViewSet,
    PartnerRatePlanViewSet, PartnerDateInventoryViewSet, PartnerRoomInventoryViewSet,
    PartnerBlockViewSet, partner_property_photos, partner_property_photo_detail, partner_room_photos, partner_room_photo_detail, partner_bookings, partner_booking_arrived, partner_assigned_place
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
    path('status/hotels/<int:property_id>/', partner_status_hotel, name='partner-status-hotel'),
    path('status/arrivals/', partner_status_arrivals, name='partner-status-arrivals'),
    path('status/rooms/', partner_status_rooms, name='partner-status-rooms'),
    path('', include(router.urls)),
    path('properties/<int:property_id>/photos/', partner_property_photos, name='partner-property-photos'),
    path('rooms/<int:room_type_id>/photos/', partner_room_photos, name='partner-room-photos'),
    path('rooms/<int:room_type_id>/photos/<int:photo_id>/', partner_room_photo_detail, name='partner-room-photo-detail'),
    path('properties/<int:property_id>/photos/<int:photo_id>/', partner_property_photo_detail,
         name='partner-property-photo-detail'),
    path('assigned-place/', partner_assigned_place, name='partner-assigned-place'),
    path('bookings/', partner_bookings, name='partner-bookings'),
    path('bookings/<int:booking_id>/arrived/', partner_booking_arrived, name='partner-booking-arrived'),
    path('bookings/<int:booking_id>/no-show-report/', partner_no_show_report_create,
         name='partner-no-show-report-create'),
    path('no-show-reports/', partner_no_show_reports, name='partner-no-show-reports'),
    path('no-show-reports/<int:report_id>/withdraw/', partner_no_show_report_withdraw,
         name='partner-no-show-report-withdraw'),
]
