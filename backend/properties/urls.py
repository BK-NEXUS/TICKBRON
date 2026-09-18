"""
URL configuration for properties app.
"""
from django.urls import path
from properties.views import property_search, property_search_suggestions, property_detail, property_availability

app_name = 'properties'

urlpatterns = [
    path('properties/search/', property_search, name='property_search'),
    path('properties/search/suggestions/', property_search_suggestions, name='property_search_suggestions'),
    path('properties/<int:property_id>/', property_detail, name='property_detail'),
    path('properties/<int:property_id>/availability/', property_availability, name='property_availability'),
]