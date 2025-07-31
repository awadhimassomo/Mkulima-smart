"""
Order models for Kikapu Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from decimal import Decimal
from shared.models.base import BaseModel, StatusModel, AddressModel, PriceModel


class Order(BaseModel, StatusModel, PriceModel):
    """Main order model"""
    
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        PROCESSING = 'processing', _('Processing')
        SHIPPED = 'shipped', _('Shipped')
        DELIVERED = 'delivered', _('Delivered')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PAID = 'paid', _('Paid')
        PARTIALLY_PAID = 'partially_paid', _('Partially Paid')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')
    
    class OrderType(models.TextChoices):
        DIRECT_PURCHASE = 'direct_purchase', _('Direct Purchase')
        MARKETPLACE_ORDER = 'marketplace_order', _('Marketplace Order')
        BULK_ORDER = 'bulk_order', _('Bulk Order')
        SUBSCRIPTION = 'subscription', _('Subscription')
    
    # Order identification
    order_number = models.CharField(
        _('order number'),
        max_length=50,
        unique=True,
        help_text=_('Unique order identifier')
    )
    
    # Parties involved
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name=_('buyer')
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name=_('seller')
    )
    
    # Order details
    order_type = models.CharField(
        _('order type'),
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.DIRECT_PURCHASE
    )
    order_status = models.CharField(
        _('order status'),
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Pricing breakdown
    subtotal = models.DecimalField(_('subtotal'), max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(_('tax amount'), max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(_('shipping cost'), max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(_('discount amount'), max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(_('total amount'), max_digits=12, decimal_places=2)
    
    # Important dates
    order_date = models.DateTimeField(_('order date'), auto_now_add=True)
    required_date = models.DateTimeField(_('required date'), blank=True, null=True)
    shipped_date = models.DateTimeField(_('shipped date'), blank=True, null=True)
    delivered_date = models.DateTimeField(_('delivered date'), blank=True, null=True)
    
    # Delivery information
    delivery_method = models.CharField(
        _('delivery method'),
        max_length=20,
        choices=[
            ('pickup', _('Pickup')),
            ('delivery', _('Delivery')),
            ('shipping', _('Shipping')),
        ],
        default='delivery'
    )
    
    # Special instructions
    notes = models.TextField(_('order notes'), blank=True)
    special_instructions = models.TextField(_('special instructions'), blank=True)
    
    # Tracking
    tracking_number = models.CharField(_('tracking number'), max_length=100, blank=True)

    # Integrating with 3rd party
    tracking_provider = models.CharField(_('tracking provider'), max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)

    
    class Meta:
        db_table = 'orders'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['buyer']),
            models.Index(fields=['seller']),
            models.Index(fields=['order_status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['order_date']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.buyer.display_name}"
    
    @property
    def is_paid(self):
        """Check if order is fully paid"""
        return self.payment_status == self.PaymentStatus.PAID
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.order_status in [
            self.OrderStatus.PENDING,
            self.OrderStatus.CONFIRMED
        ]
    
    @property
    def is_delivered(self):
        """Check if order is delivered"""
        return self.order_status == self.OrderStatus.DELIVERED
    
    def calculate_total(self):
        """Calculate and update total amount"""
        self.total_amount = (
            self.subtotal +
            self.tax_amount +
            self.shipping_cost -
            self.discount_amount
        )
        return self.total_amount


class OrderItem(BaseModel):
    """Individual items in an order"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('order')
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('product')
    )
    variant = models.ForeignKey(
        'products.ProductVariant',
        on_delete=models.PROTECT,
        related_name='order_items',
        blank=True,
        null=True,
        verbose_name=_('variant')
    )
    
    # Item details
    quantity = models.PositiveIntegerField(_('quantity'))
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Price per unit at time of order')
    )
    total_price = models.DecimalField(
        _('total price'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Total price for this item (quantity × unit_price)')
    )
    
    # Product snapshot (in case product details change)
    product_name = models.CharField(_('product name'), max_length=200)
    product_sku = models.CharField(_('product SKU'), max_length=50)
    product_description = models.TextField(_('product description'), blank=True)
    
    # Item status
    item_status = models.CharField(
        _('item status'),
        max_length=20,
        choices=[
            ('pending', _('Pending')),
            ('confirmed', _('Confirmed')),
            ('preparing', _('Preparing')),
            ('ready', _('Ready')),
            ('shipped', _('Shipped')),
            ('delivered', _('Delivered')),
            ('cancelled', _('Cancelled')),
        ],
        default='pending'
    )
    
    # Special requirements
    notes = models.TextField(_('item notes'), blank=True)
    
    class Meta:
        db_table = 'order_items'
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
            models.Index(fields=['variant']),
        ]
    
    def __str__(self):
        return f"{self.product_name} × {self.quantity} - Order {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.quantity * self.unit_price
        
        # Store product snapshot
        if not self.product_name and self.product:
            self.product_name = self.product.name
            self.product_sku = self.product.sku
            self.product_description = self.product.description
        
        super().save(*args, **kwargs)


class OrderAddress(BaseModel, AddressModel):
    """Delivery/billing addresses for orders"""
    
    class AddressType(models.TextChoices):
        BILLING = 'billing', _('Billing Address')
        SHIPPING = 'shipping', _('Shipping Address')
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='addresses',
        verbose_name=_('order')
    )
    address_type = models.CharField(
        _('address type'),
        max_length=20,
        choices=AddressType.choices
    )
    
    # Contact information
    recipient_name = models.CharField(_('recipient name'), max_length=255)
    phone_number = models.CharField(_('phone number'), max_length=20)
    email = models.EmailField(_('email'), blank=True)
    
    # Special instructions
    delivery_instructions = models.TextField(_('delivery instructions'), blank=True)
    
    class Meta:
        db_table = 'order_addresses'
        verbose_name = _('Order Address')
        verbose_name_plural = _('Order Addresses')
        unique_together = ['order', 'address_type']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.address_type} - {self.recipient_name}"


class OrderStatusHistory(BaseModel):
    """Track order status changes"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('order')
    )
    from_status = models.CharField(
        _('from status'),
        max_length=20,
        choices=Order.OrderStatus.choices,
        blank=True
    )
    to_status = models.CharField(
        _('to status'),
        max_length=20,
        choices=Order.OrderStatus.choices
    )
    
    # Change details
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('changed by')
    )
    notes = models.TextField(_('notes'), blank=True)
    
    # Notification sent
    notification_sent = models.BooleanField(_('notification sent'), default=False)
    
    class Meta:
        db_table = 'order_status_history'
        verbose_name = _('Order Status History')
        verbose_name_plural = _('Order Status History')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['to_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order.order_number}: {self.from_status} → {self.to_status}"


class OrderDiscount(BaseModel):
    """Discounts applied to orders"""
    
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage')
        FIXED_AMOUNT = 'fixed_amount', _('Fixed Amount')
        BULK_DISCOUNT = 'bulk_discount', _('Bulk Discount')
        COUPON = 'coupon', _('Coupon')
        LOYALTY = 'loyalty', _('Loyalty Discount')
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='discounts',
        verbose_name=_('order')
    )
    
    discount_type = models.CharField(
        _('discount type'),
        max_length=20,
        choices=DiscountType.choices
    )
    discount_code = models.CharField(_('discount code'), max_length=50, blank=True)
    discount_name = models.CharField(_('discount name'), max_length=100)
    
    # Discount values
    discount_percentage = models.DecimalField(
        _('discount percentage'),
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    maximum_discount = models.DecimalField(
        _('maximum discount'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'order_discounts'
        verbose_name = _('Order Discount')
        verbose_name_plural = _('Order Discounts')
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['discount_code']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number} - {self.discount_name}"


class OrderNote(BaseModel):
    """Internal notes for orders"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='internal_notes',
        verbose_name=_('order')
    )
    note = models.TextField(_('note'))
    is_customer_visible = models.BooleanField(_('customer visible'), default=False)
    
    class Meta:
        db_table = 'order_notes'
        verbose_name = _('Order Note')
        verbose_name_plural = _('Order Notes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['is_customer_visible']),
        ]

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, verbose_name=_('order note'))
 
    def __str__(self):
        return f"Note for Order {self.order.order_number}"