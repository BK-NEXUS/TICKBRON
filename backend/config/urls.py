"""
URL configuration for TICKBRON Backend
"""
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 endpoints
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/', include('properties.urls')),
    path('api/v1/', include('bookings.urls')),
    path('api/v1/geography/', include('geography.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/me/', include('accounts.urls')),
    path('api/v1/partner/', include('partner.urls')),
    path('api/v1/admin-panel/', include('admin_panel.urls')),
    path('api/v1/promotions/', include('promotions.urls')),
]
