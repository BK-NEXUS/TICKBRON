from django.urls import path

from geography.views import city_list, country_list, region_list

app_name = 'geography'

urlpatterns = [
    path('countries/', country_list, name='country-list'),
    path('countries/<str:code>/regions/', region_list, name='region-list'),
    path('regions/<int:region_id>/cities/', city_list, name='city-list'),
]
