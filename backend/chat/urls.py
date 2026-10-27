from django.urls import path

from chat import views

app_name = 'chat'

urlpatterns = [
    path('messages/', views.MyMessages.as_view(), name='messages'),
    path('read/', views.MyRead.as_view(), name='read'),
    path('unread/', views.MyUnread.as_view(), name='unread'),
]
