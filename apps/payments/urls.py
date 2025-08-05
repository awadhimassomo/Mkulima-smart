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
    
    # Payment management
    path('', views.PaymentListView.as_view(), name='payment-list'),
    path('<uuid:payment_id>/status/', views.PaymentStatusView.as_view(), name='payment-status'),
    path('<uuid:payment_id>/refund/', views.PaymentRefundView.as_view(), name='payment-refund'),
    
    # User payment accounts
    path('accounts/', views.PaymentAccountListView.as_view(), name='payment-accounts'),
    path('accounts/create/', views.PaymentAccountCreateView.as_view(), name='create-payment-account'),
    
    # Statistics
    path('statistics/', views.PaymentStatisticsView.as_view(), name='payment-statistics'),
    
    # Webhooks (for payment gateways)
    path('webhooks/<str:provider>/', views.PaymentWebhookView.as_view(), name='payment-webhook'),
]