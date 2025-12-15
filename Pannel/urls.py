# pannel/urls.py
from django.urls import path
from . import views
from pannel import home_view

app_name = 'pannel'  # Définition du namespace

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('learn/', views.learn_view, name='learn'),
    path('doc/', views.doc_view, name='doc'),
    path('history/', views.history_view, name='history'),
    path('account/', views.account_view, name='account'),
    path('', home_view, name='home'),
    path('certificat/<int:cours_id>/', views.generate_certificate, name='generate_certificate')
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/cancel/', views.payment_cancel, name='payment_cancel'),
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
    
   
    
]