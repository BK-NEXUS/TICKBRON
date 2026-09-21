"""
URL configuration for admin app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from admin_panel.views import (
    AdminPropertyViewSet, AdminUserViewSet,
    AdminAmenityCategoryViewSet, AdminAmenityViewSet,
    admin_property_approve, admin_property_suspend,
    admin_create_hotel_owner, admin_payment_transactions
)

app_name = 'admin_panel'

router = DefaultRouter()
router.register(r'properties', AdminPropertyViewSet, basename='admin-property')
router.register(r'amenities/categories', AdminAmenityCategoryViewSet, basename='admin-amenity-category')
router.register(r'amenities', AdminAmenityViewSet, basename='admin-amenity')

urlpatterns = [
    path('users/create-hotel-owner/', admin_create_hotel_owner, name='admin-create-hotel-owner'),
    path('users/', AdminUserViewSet.as_view({'get': 'list'}), name='admin-user-list'),
    path('', include(router.urls)),
    path('properties/<int:property_id>/approve/', admin_property_approve, name='admin-property-approve'),
    path('properties/<int:property_id>/suspend/', admin_property_suspend, name='admin-property-suspend'),
    path('payments/transactions/', admin_payment_transactions, name='admin-payment-transactions'),
]
