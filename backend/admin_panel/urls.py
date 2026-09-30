"""
URL configuration for admin app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_panel.views import (
    AdminAPIRootView, AdminPropertyViewSet, AdminUserViewSet,
    AdminAmenityCategoryViewSet, AdminAmenityViewSet,
    admin_property_approve, admin_property_suspend, admin_property_region,
    admin_create_hotel_owner, admin_payment_transactions,
    admin_booking_lookup_by_reference,
    admin_customers_directory,
    admin_customer_detail,
    admin_internal_note_create,
    admin_internal_note_detail,
    admin_registration_statistics,
    admin_top_bookers_leaderboard
)

app_name = 'admin_panel'

router = DefaultRouter()
router.APIRootView = AdminAPIRootView
router.register(r'properties', AdminPropertyViewSet, basename='admin-property')
router.register(r'amenities/categories', AdminAmenityCategoryViewSet, basename='admin-amenity-category')
router.register(r'amenities', AdminAmenityViewSet, basename='admin-amenity')

urlpatterns = [
    path('users/create-hotel-owner/', admin_create_hotel_owner, name='admin-create-hotel-owner'),
    path('users/', AdminUserViewSet.as_view({'get': 'list'}), name='admin-user-list'),
    path('customers/', admin_customers_directory, name='admin-customers-directory'),
    path('customers/<int:customer_id>/', admin_customer_detail, name='admin-customer-detail'),
    path('customers/<int:customer_id>/notes/', admin_internal_note_create, name='admin-internal-note-create'),
    path('customers/<int:customer_id>/notes/<int:note_id>/', admin_internal_note_detail, name='admin-internal-note-detail'),
    path('statistics/registrations/', admin_registration_statistics, name='admin-registration-statistics'),
    path('statistics/top-bookers/', admin_top_bookers_leaderboard, name='admin-top-bookers-leaderboard'),
    path('', include(router.urls)),
    path('properties/<int:property_id>/approve/', admin_property_approve, name='admin-property-approve'),
    path('properties/<int:property_id>/suspend/', admin_property_suspend, name='admin-property-suspend'),
    path('properties/<int:property_id>/region/', admin_property_region, name='admin-property-region'),
    path('payments/transactions/', admin_payment_transactions, name='admin-payment-transactions'),
    path('bookings/lookup/', admin_booking_lookup_by_reference, name='admin-booking-lookup'),
]
