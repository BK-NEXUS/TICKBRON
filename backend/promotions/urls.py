from django.urls import path

from promotions import views

app_name = 'promotions'

urlpatterns = [
    path('home/', views.home_promotions, name='home'),
    path('<int:promotion_id>/click/', views.promotion_click, name='click'),
]
