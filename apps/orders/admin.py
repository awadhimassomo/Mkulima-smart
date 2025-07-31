"""
Orders admin configuration
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Order, OrderItem, OrderAddress, OrderStatusHistory,
    OrderDiscount, OrderNote
)


class OrderItemInline(admin.TabularInline):
    """Inline for order items"""
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price', 'product_name', 'product_sku']
    fields = [
        'product', 'variant', 'quantity', 'unit_price', 'total_price',
        'item_status', 'notes'
    ]


class OrderAddressInline(admin.TabularInline):
    """Inline for order addresses"""
    model = OrderAddress
    extra = 0
    fields = [
        'address_type', 'recipient_name', 'phone_number',
        'address_line_1', 'city', 'delivery_instructions'
    ]


class OrderDiscountInline(admin.TabularInline):
    """Inline for order discounts"""
    model = OrderDiscount
    extra = 0
    readonly_fields = ['discount_amount']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order admin"""
    
    list_display = [
        'order_number', 'buyer', 'seller', 'order_status', 
        'payment_status', 'total_amount', 'order_date'
    ]
    list_filter = [
        'order_status', 'payment_status', 'order_type', 
        'delivery_method', 'order_date'
    ]
    search_fields = [
        'order_number', 'buyer__email', 'seller__email',
        'tracking_number'
    ]
    ordering = ['-order_date']
    readonly_fields = [
        'order_date', 'shipped_date', 'delivered_date',
        'subtotal', 'total_amount'
    ]
    
    inlines = [OrderItemInline, OrderAddressInline, OrderDiscountInline]
    
    fieldsets = (
        (_('Order Information'), {
            'fields': ('order_number', 'buyer', 'seller', 'order_type')
        }),
        (_('Status'), {
            'fields': ('order_status', 'payment_status')
        }),
        (_('Pricing'), {
            'fields': ('subtotal', 'tax_amount', 'shipping_cost', 
                      'discount_amount', 'total_amount', 'currency')
        }),
        (_('Delivery'), {
            'fields': ('delivery_method', 'required_date', 'tracking_number')
        }),
        (_('Important Dates'), {
            'fields': ('order_date', 'shipped_date', 'delivered_date'),
            'classes': ('collapse',)
        }),
        (_('Additional Information'), {
            'fields': ('notes', 'special_instructions'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('buyer', 'seller')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Order item admin"""
    
    list_display = [
        'order', 'product_name', 'quantity', 'unit_price', 
        'total_price', 'item_status'
    ]
    list_filter = ['item_status', 'created_at']
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    ordering = ['-created_at']
    readonly_fields = ['total_price', 'product_name', 'product_sku', 'product_description']


@admin.register(OrderAddress)
class OrderAddressAdmin(admin.ModelAdmin):
    """Order address admin"""
    
    list_display = [
        'order', 'address_type', 'recipient_name', 
        'city', 'phone_number'
    ]
    list_filter = ['address_type', 'country']
    search_fields = [
        'order__order_number', 'recipient_name', 'phone_number',
        'city', 'address_line_1'
    ]


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Order status history admin"""
    
    list_display = [
        'order', 'from_status', 'to_status', 'changed_by', 
        'notification_sent', 'created_at'
    ]
    list_filter = ['from_status', 'to_status', 'notification_sent', 'created_at']
    search_fields = ['order__order_number', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # These are created automatically


@admin.register(OrderDiscount)
class OrderDiscountAdmin(admin.ModelAdmin):
    """Order discount admin"""
    
    list_display = [
        'order', 'discount_type', 'discount_name', 
        'discount_code', 'discount_amount'
    ]
    list_filter = ['discount_type']
    search_fields = ['order__order_number', 'discount_code', 'discount_name']


@admin.register(OrderNote)
class OrderNoteAdmin(admin.ModelAdmin):
    """Order note admin"""
    
    list_display = [
        'order', 'note', 'is_customer_visible', 'created_by', 'created_at'
    ]
    list_filter = ['is_customer_visible', 'created_at']
    search_fields = ['order__order_number', 'note']
    ordering = ['-created_at']