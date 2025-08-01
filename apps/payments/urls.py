"""
Payments URL patterns
"""
from django.urls import path
from . import views

urlpatterns = [
    # Payment methods
    path('methods/', views.PaymentMethodListView.as_view(), name='payment-methods'),
    
    # Process payment
    path('process/', views.ProcessPaymentView.as_view(), name='process-payment'),
    
    # Payment status
    path('<uuid:payment_id>/status/', views.PaymentStatusView.as_view(), name='payment-status'),
    
    # User payment accounts
    path('accounts/', views.PaymentAccountListView.as_view(), name='payment-accounts'),
    path('accounts/create/', views.PaymentAccountCreateView.as_view(), name='create-payment-account'),
    
    # Webhooks (for payment gateways)
    path('webhooks/<str:provider>/', views.PaymentWebhookView.as_view(), name='payment-webhook'),
]