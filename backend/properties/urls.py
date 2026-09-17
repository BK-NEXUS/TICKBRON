"""
URL configuration for properties app.
"""
from django.urls import path
from properties.views import property_search, property_search_suggestions

app_name = 'properties'

urlpatterns = [
    path('properties/search/', property_search, name='property_search'),
    path('properties/search/suggestions/', property_search_suggestions, name='property_search_suggestions'),
]