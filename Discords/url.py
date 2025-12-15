# Discords/urls.py
from django.urls import path
from . import views

app_name = 'discords'

urlpatterns = [
    path('login/', views.discord_login, name='login'),
    path('login/redirect/', views.discord_login_redirect, name='login_redirect'),
]