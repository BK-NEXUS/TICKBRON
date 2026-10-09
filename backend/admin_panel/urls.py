"""
URL configuration for admin app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from bookings.admin_views import auto_completion_status
from bookings.views_noshow import (
    admin_no_show_report_approve, admin_no_show_report_detail, admin_no_show_report_reject,
    admin_no_show_report_reverse, admin_no_show_reports,
)
from promotions import admin_views as promotion_views
from payments.admin_views import refund_mark_done, refund_retry, refunds_needs_attention
from currency.views import exchange_rate_accept, exchange_rate_list, exchange_rate_status
from geography.admin_views import AdminCityViewSet, AdminCountryViewSet, AdminRegionViewSet
from admin_panel.status import (
    status_countries, status_hotel_detail, status_hotels, status_hotels_flat, status_regions, status_user_detail,
    status_users,
)
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
    admin_top_bookers_leaderboard,
    admin_access_log,
)

app_name = 'admin_panel'

router = DefaultRouter()
router.APIRootView = AdminAPIRootView
router.register(r'properties', AdminPropertyViewSet, basename='admin-property')
router.register(r'geography/countries', AdminCountryViewSet, basename='admin-geo-country')
router.register(r'geography/regions', AdminRegionViewSet, basename='admin-geo-region')
router.register(r'geography/cities', AdminCityViewSet, basename='admin-geo-city')
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
    path('status/countries/', status_countries, name='admin-status-countries'),
    path('status/countries/<str:country>/regions/', status_regions, name='admin-status-regions'),
    path('status/countries/<str:country>/regions/<str:region>/hotels/', status_hotels, name='admin-status-hotels'),
    path('status/hotels/', status_hotels_flat, name='admin-status-hotels-flat'),
    path('status/hotels/<int:property_id>/', status_hotel_detail, name='admin-status-hotel-detail'),
    path('status/users/', status_users, name='admin-status-users'),
    path('status/users/<int:user_id>/', status_user_detail, name='admin-status-user-detail'),
    path('audit-log/', admin_access_log, name='admin-access-log'),
    path('auto-completion/status/', auto_completion_status, name='admin-auto-completion-status'),
    path('no-show-reports/', admin_no_show_reports, name='admin-no-show-reports'),
    path('no-show-reports/<int:report_id>/', admin_no_show_report_detail, name='admin-no-show-report-detail'),
    path('no-show-reports/<int:report_id>/approve/', admin_no_show_report_approve,
         name='admin-no-show-report-approve'),
    path('no-show-reports/<int:report_id>/reject/', admin_no_show_report_reject,
         name='admin-no-show-report-reject'),
    path('no-show-reports/<int:report_id>/reverse/', admin_no_show_report_reverse,
         name='admin-no-show-report-reverse'),
    path('refunds/needs-attention/', refunds_needs_attention, name='admin-refunds-needs-attention'),
    path('refunds/<int:refund_id>/mark-done/', refund_mark_done, name='admin-refund-mark-done'),
    path('refunds/<int:refund_id>/retry/', refund_retry, name='admin-refund-retry'),
    path('exchange-rates/', exchange_rate_list, name='admin-exchange-rates'),
    path('exchange-rates/status/', exchange_rate_status, name='admin-exchange-rate-status'),
    path('exchange-rates/<int:rate_id>/accept/', exchange_rate_accept, name='admin-exchange-rate-accept'),
    path('', include(router.urls)),
    path('properties/<int:property_id>/approve/', admin_property_approve, name='admin-property-approve'),
    path('properties/<int:property_id>/suspend/', admin_property_suspend, name='admin-property-suspend'),
    path('properties/<int:property_id>/region/', admin_property_region, name='admin-property-region'),
    path('payments/transactions/', admin_payment_transactions, name='admin-payment-transactions'),
    path('bookings/lookup/', admin_booking_lookup_by_reference, name='admin-booking-lookup'),
    path('promotion-hotels/', promotion_views.promotion_hotels, name='admin-promotion-hotels'),
    path('promotions/', promotion_views.promotions, name='admin-promotions'),
    path('promotions/<int:promotion_id>/', promotion_views.promotion_detail, name='admin-promotion-detail'),
    path('promotions/<int:promotion_id>/pause/', promotion_views.promotion_pause, name='admin-promotion-pause'),
    path('promotions/<int:promotion_id>/resume/', promotion_views.promotion_resume, name='admin-promotion-resume'),
    path('promotions/<int:promotion_id>/cancel/', promotion_views.promotion_cancel, name='admin-promotion-cancel'),
    path('promotions/<int:promotion_id>/mark-paid/', promotion_views.promotion_mark_paid,
         name='admin-promotion-mark-paid'),
    path('promotions/<int:promotion_id>/stats/', promotion_views.promotion_stats, name='admin-promotion-stats'),
]
