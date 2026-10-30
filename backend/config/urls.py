"""
URL configuration for TICKBRON Backend
"""
from common.health import healthz, readyz
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from common.permissions import StaffOrDebug
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Probes for the load balancer / uptime monitor (no authentication, no detail in the answers)
    path('healthz/', healthz, name='healthz'),
    path('readyz/', readyz, name='readyz'),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(permission_classes=[StaffOrDebug]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema', permission_classes=[StaffOrDebug]), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema', permission_classes=[StaffOrDebug]), name='redoc'),

    # API v1 endpoints
    path('api/v1/auth/', include('users.urls')),
    path('api/v1/', include('properties.urls')),
    path('api/v1/', include('bookings.urls')),
    path('api/v1/geography/', include('geography.urls')),
    path('api/v1/me/', include('accounts.urls')),
    path('api/v1/partner/', include('partner.urls')),
    path('api/v1/admin-panel/', include('admin_panel.urls')),
    path('api/v1/promotions/', include('promotions.urls')),
    path('api/v1/chat/', include('chat.urls')),
]

# Local development only: with DEBUG off `static()` adds nothing and the web server serves /media/
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
