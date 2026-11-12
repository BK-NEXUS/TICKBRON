from django.urls import path

from geography.views import country_list, region_list

app_name = 'geography'

urlpatterns = [
    path('countries/', country_list, name='country-list'),
    path('countries/<str:code>/regions/', region_list, name='region-list'),
]
