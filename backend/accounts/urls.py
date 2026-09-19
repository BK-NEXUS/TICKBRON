"""
URL configuration for the accounts app.

This module contains URL patterns for favorites, reviews, notifications, and account history.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FavoriteViewSet, ReviewViewSet, NotificationViewSet, AccountHistoryViewSet

router = DefaultRouter()
router.register(r'favorites', FavoriteViewSet, basename='favorite')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'history', AccountHistoryViewSet, basename='account-history')

urlpatterns = [
    path('', include(router.urls)),
]
