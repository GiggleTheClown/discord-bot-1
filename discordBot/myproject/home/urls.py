from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('moderation/', views.mod, name='moderation'),
    path('leveling/', views.leveling, name='levels'),
    path('currency/', views.currency, name='currency'),
    path('person/<int:user_id>', views.detail, name='detail')
]
