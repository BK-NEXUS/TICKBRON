"""
URL configuration for TICKBRON booking endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookingViewSet, booking_cancel

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
    path('bookings/<int:booking_id>/cancel/', booking_cancel, name='booking-cancel'),
]
