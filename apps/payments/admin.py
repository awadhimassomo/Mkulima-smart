"""
Payments admin configuration
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    PaymentMethod, Payment, PaymentStatusHistory, PaymentAccount,
    PaymentRefund, PaymentWebhook
)


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Payment method admin"""
    
    list_display = [
        'name', 'method_type', 'provider', 'is_active', 
        'is_default', 'processing_fee_percentage'
    ]
    list_filter = ['method_type', 'is_active', 'is_default', 'requires_verification']
    search_fields = ['name', 'provider']
    ordering = ['name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'method_type', 'provider')
        }),
        (_('Settings'), {
            'fields': ('is_active', 'is_default', 'requires_verification')
        }),
        (_('Fees & Limits'), {
            'fields': ('processing_fee_percentage', 'processing_fee_fixed',
                      'minimum_amount', 'maximum_amount')
        }),
        (_('API Configuration'), {
            'fields': ('api_endpoint', 'api_key', 'api_secret', 'webhook_url'),
            'classes': ('collapse',)
        }),
        (_('Supported Currencies'), {
            'fields': ('supported_currencies',)
        }),
        (_('Additional Settings'), {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin"""
    
    list_display = [
        'reference_number', 'payer', 'payee', 'payment_method',
        'payment_status', 'gross_amount', 'currency', 'initiated_at'
    ]
    list_filter = [
        'payment_status', 'payment_type', 'payment_method',
        'currency', 'is_verified', 'initiated_at'
    ]
    search_fields = [
        'reference_number', 'external_reference', 'gateway_transaction_id',
        'payer__email', 'payee__email'
    ]
    ordering = ['-initiated_at']
    readonly_fields = [
        'payment_id', 'initiated_at', 'processed_at',
        'net_amount', 'gateway_response'
    ]
    
    fieldsets = (
        (_('Payment Information'), {
            'fields': ('payment_id', 'reference_number', 'external_reference',
                      'payment_type', 'payment_status')
        }),
        (_('Parties'), {
            'fields': ('payer', 'payee', 'payment_method', 'order')
        }),
        (_('Amount Details'), {
            'fields': ('gross_amount', 'fee_amount', 'net_amount', 'currency')
        }),
        (_('Gateway Details'), {
            'fields': ('gateway_transaction_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
        (_('Dates'), {
            'fields': ('initiated_at', 'processed_at', 'expires_at'),
            'classes': ('collapse',)
        }),
        (_('Additional'), {
            'fields': ('description', 'notes', 'is_verified', 'verification_code'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'payer', 'payee', 'payment_method', 'order'
        )


@admin.register(PaymentStatusHistory)
class PaymentStatusHistoryAdmin(admin.ModelAdmin):
    """Payment status history admin"""
    
    list_display = [
        'payment', 'from_status', 'to_status', 'changed_by', 'created_at'
    ]
    list_filter = ['from_status', 'to_status', 'created_at']
    search_fields = ['payment__reference_number', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'gateway_response']
    
    def has_add_permission(self, request):
        return False  # These are created automatically


@admin.register(PaymentAccount)
class PaymentAccountAdmin(admin.ModelAdmin):
    """Payment account admin"""
    
    list_display = [
        'user', 'payment_method', 'account_name', 'account_number',
        'is_primary', 'is_verified', 'status'
    ]
    list_filter = ['payment_method', 'is_primary', 'is_verified', 'status']
    search_fields = [
        'user__email', 'account_name', 'account_number',
        'account_holder_name', 'bank_name'
    ]
    ordering = ['user', 'payment_method']
    readonly_fields = ['verification_date']
    
    fieldsets = (
        (_('Account Information'), {
            'fields': ('user', 'payment_method', 'account_name',
                      'account_number', 'account_holder_name')
        }),
        (_('Bank Details'), {
            'fields': ('bank_name', 'bank_code', 'branch_name', 'branch_code')
        }),
        (_('Mobile Money'), {
            'fields': ('phone_number', 'provider_name')
        }),
        (_('Settings'), {
            'fields': ('is_primary', 'is_verified', 'verification_date', 'status')
        }),
        (_('Limits'), {
            'fields': ('daily_limit', 'monthly_limit'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentRefund)
class PaymentRefundAdmin(admin.ModelAdmin):
    """Payment refund admin"""
    
    list_display = [
        'refund_number', 'original_payment', 'refund_status',
        'refund_amount', 'requested_by', 'requested_at'
    ]
    list_filter = ['refund_status', 'refund_reason', 'requested_at']
    search_fields = [
        'refund_number', 'original_payment__reference_number',
        'requested_by__email'
    ]
    ordering = ['-requested_at']
    readonly_fields = [
        'requested_at', 'approved_at', 'processed_at',
        'net_refund', 'gateway_response'
    ]
    
    fieldsets = (
        (_('Refund Information'), {
            'fields': ('refund_number', 'original_payment', 'refund_reason',
                      'refund_status')
        }),
        (_('Amount Details'), {
            'fields': ('refund_amount', 'refund_fee', 'net_refund', 'currency')
        }),
        (_('Parties'), {
            'fields': ('requested_by', 'approved_by')
        }),
        (_('Dates'), {
            'fields': ('requested_at', 'approved_at', 'processed_at'),
            'classes': ('collapse',)
        }),
        (_('Details'), {
            'fields': ('reason_description', 'admin_notes'),
            'classes': ('collapse',)
        }),
        (_('Gateway'), {
            'fields': ('gateway_refund_id', 'gateway_response'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentWebhook)
class PaymentWebhookAdmin(admin.ModelAdmin):
    """Payment webhook admin"""
    
    list_display = [
        'webhook_id', 'payment_method', 'event_type',
        'status', 'is_verified', 'created_at'
    ]
    list_filter = ['payment_method', 'event_type', 'status', 'is_verified']
    search_fields = ['webhook_id', 'event_type']
    ordering = ['-created_at']
    readonly_fields = [
        'created_at', 'processed_at', 'event_data',
        'headers', 'signature'
    ]
    
    fieldsets = (
        (_('Webhook Information'), {
            'fields': ('webhook_id', 'payment_method', 'payment', 'event_type')
        }),
        (_('Status'), {
            'fields': ('status', 'processed_at', 'error_message', 'is_verified')
        }),
        (_('Data'), {
            'fields': ('event_data', 'headers', 'signature'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        return False  # These are created by webhooks
    
    def has_change_permission(self, request, obj=None):
        return False  # These should not be modified manually