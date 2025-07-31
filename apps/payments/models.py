"""
Payment models for Kikapu Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from shared.models.base import BaseModel, StatusModel, PriceModel
from softdelete.models import SoftDeleteObject
import uuid


class PaymentMethod(BaseModel, StatusModel):
    """Available payment methods"""
    
    class MethodType(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', _('Bank Transfer')
        MOBILE_MONEY = 'mobile_money', _('Mobile Money')
        CREDIT_CARD = 'credit_card', _('Credit Card')
        DEBIT_CARD = 'debit_card', _('Debit Card')
        CASH = 'cash', _('Cash')
        DIGITAL_WALLET = 'digital_wallet', _('Digital Wallet')
        CRYPTOCURRENCY = 'cryptocurrency', _('Cryptocurrency')
    
    name = models.CharField(_('method name'), max_length=100)
    method_type = models.CharField(
        _('method type'),
        max_length=20,
        choices=MethodType.choices
    )
    provider = models.CharField(_('provider'), max_length=100, blank=True)
    
    # Configuration
    is_active = models.BooleanField(_('is active'), default=True)
    is_default = models.BooleanField(_('is default'), default=False)
    requires_verification = models.BooleanField(_('requires verification'), default=False)
    
    # Processing details
    processing_fee_percentage = models.DecimalField(
        _('processing fee percentage'),
        max_digits=5,
        decimal_places=4,
        default=0.0000
    )
    processing_fee_fixed = models.DecimalField(
        _('processing fee fixed'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    minimum_amount = models.DecimalField(
        _('minimum amount'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    maximum_amount = models.DecimalField(
        _('maximum amount'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # API configuration
    api_endpoint = models.URLField(_('API endpoint'), blank=True)
    api_key = models.CharField(_('API key'), max_length=255, blank=True)
    api_secret = models.CharField(_('API secret'), max_length=255, blank=True)
    webhook_url = models.URLField(_('webhook URL'), blank=True)
    
    # Supported currencies
    supported_currencies = models.JSONField(
        _('supported currencies'),
        default=list,
        help_text=_('List of supported currency codes')
    )
    
    # Configuration settings
    settings = models.JSONField(
        _('method settings'),
        default=dict,
        help_text=_('Additional configuration settings')
    )
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = _('Payment Method')
        verbose_name_plural = _('Payment Methods')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.provider})"
    
    def calculate_fee(self, amount):
        """Calculate processing fee for given amount"""
        percentage_fee = amount * (self.processing_fee_percentage / 100)
        return percentage_fee + self.processing_fee_fixed


class Payment(SoftDeleteObject, BaseModel, StatusModel, PriceModel):
    """Payment transactions"""
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        FAILED = 'failed', _('Failed')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
        PARTIALLY_REFUNDED = 'partially_refunded', _('Partially Refunded')
    
    class PaymentType(models.TextChoices):
        ORDER_PAYMENT = 'order_payment', _('Order Payment')
        REFUND = 'refund', _('Refund')
        DEPOSIT = 'deposit', _('Deposit')
        WITHDRAWAL = 'withdrawal', _('Withdrawal')
        FEE = 'fee', _('Fee')
    
    # Payment identification
    payment_id = models.UUIDField(
        _('payment ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    reference_number = models.CharField(
        _('reference number'),
        max_length=100,
        unique=True,
        help_text=_('Human-readable reference number')
    )
    external_reference = models.CharField(
        _('external reference'),
        max_length=100,
        blank=True,
        help_text=_('Payment gateway reference')
    )
    
    # Payment details
    payment_type = models.CharField(
        _('payment type'),
        max_length=20,
        choices=PaymentType.choices,
        default=PaymentType.ORDER_PAYMENT
    )
    payment_status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    
    # Parties involved
    payer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments_made',
        verbose_name=_('payer')
    )
    payee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='payments_received',
        verbose_name=_('payee')
    )
    
    # Payment method
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name='payments',
        verbose_name=_('payment method')
    )
    
    # Related order
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.PROTECT,
        related_name='payments',
        blank=True,
        null=True,
        verbose_name=_('order')
    )
    
    # Amount details
    gross_amount = models.DecimalField(_('gross amount'), max_digits=12, decimal_places=2)
    fee_amount = models.DecimalField(_('fee amount'), max_digits=12, decimal_places=2, default=0)
    net_amount = models.DecimalField(_('net amount'), max_digits=12, decimal_places=2)
    
    # Payment gateway details
    gateway_transaction_id = models.CharField(
        _('gateway transaction ID'),
        max_length=255,
        blank=True,
        help_text=_('Transaction ID from payment gateway')
    )
    gateway_response = models.JSONField(
        _('gateway response'),
        default=dict,
        blank=True,
        help_text=_('Raw response from payment gateway')
    )
    
    # Important dates
    initiated_at = models.DateTimeField(_('initiated at'), auto_now_add=True)
    processed_at = models.DateTimeField(_('processed at'), blank=True, null=True)
    expires_at = models.DateTimeField(_('expires at'), blank=True, null=True)
    
    # Additional information
    description = models.TextField(_('description'), blank=True)
    notes = models.TextField(_('internal notes'), blank=True)
    
    # Verification
    is_verified = models.BooleanField(_('is verified'), default=False)
    verification_code = models.CharField(_('verification code'), max_length=20, blank=True)
    
    class Meta:
        db_table = 'payments'
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['external_reference']),
            models.Index(fields=['payer']),
            models.Index(fields=['payee']),
            models.Index(fields=['order']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['initiated_at']),
        ]

    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment {self.reference_number} - {self.gross_amount} {self.currency}"
    
    @property
    def is_successful(self):
        """Check if payment was successful"""
        return self.payment_status == self.PaymentStatus.COMPLETED
    
    @property
    def is_pending(self):
        """Check if payment is pending"""
        return self.payment_status == self.PaymentStatus.PENDING
    
    @property
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return self.payment_status == self.PaymentStatus.COMPLETED
    
    def calculate_net_amount(self):
        """Calculate net amount after fees"""
        self.net_amount = self.gross_amount - self.fee_amount
        return self.net_amount

    def save(self, *args, **kwargs):
        if self.payment_status == self.PaymentStatus.COMPLETED and self.completed_at is None:
            self.completed_at = timezone.now()
        elif self.payment_status == self.PaymentStatus.CANCELLED and self.cancelled_at is None:
            self.cancelled_at = timezone.now()
        elif self.payment_status == self.PaymentStatus.FAILED and self.failed_at is None:
            self.failed_at = timezone.now()
        elif self.payment_status == self.PaymentStatus.REFUNDED and self.refunded_at is None:
            self.refunded_at = timezone.now()
        super().save(*args, **kwargs)



class PaymentStatusHistory(BaseModel):
    """Track payment status changes"""
    
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_('payment')
    )
    from_status = models.CharField(
        _('from status'),
        max_length=20,
        choices=Payment.PaymentStatus.choices,
        blank=True
    )
    to_status = models.CharField(
        _('to status'),
        max_length=20,
        choices=Payment.PaymentStatus.choices
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
    gateway_response = models.JSONField(_('gateway response'), default=dict, blank=True)
    
    class Meta:
        db_table = 'payment_status_history'
        verbose_name = _('Payment Status History')
        verbose_name_plural = _('Payment Status History')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment']),
            models.Index(fields=['to_status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.payment.reference_number}: {self.from_status} → {self.to_status}"


class PaymentAccount(BaseModel, StatusModel):
    """User payment accounts (bank accounts, mobile money, etc.)"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_accounts',
        verbose_name=_('user')
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.PROTECT,
        related_name='user_accounts',
        verbose_name=_('payment method')
    )
    
    # Account details
    account_name = models.CharField(_('account name'), max_length=255)
    account_number = models.CharField(_('account number'), max_length=100)
    account_holder_name = models.CharField(_('account holder name'), max_length=255)
    
    # Additional details (bank specific)
    bank_name = models.CharField(_('bank name'), max_length=100, blank=True)
    bank_code = models.CharField(_('bank code'), max_length=20, blank=True)
    branch_name = models.CharField(_('branch name'), max_length=100, blank=True)
    branch_code = models.CharField(_('branch code'), max_length=20, blank=True)
    
    # Mobile money specific
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    provider_name = models.CharField(_('provider name'), max_length=50, blank=True)
    
    # Account settings
    is_primary = models.BooleanField(_('is primary'), default=False)
    is_verified = models.BooleanField(_('is verified'), default=False)
    verification_date = models.DateTimeField(_('verification date'), blank=True, null=True)
    
    # Limits
    daily_limit = models.DecimalField(
        _('daily limit'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    monthly_limit = models.DecimalField(
        _('monthly limit'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'payment_accounts'
        verbose_name = _('Payment Account')
        verbose_name_plural = _('Payment Accounts')
        unique_together = ['user', 'payment_method', 'account_number']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.account_name} - {self.account_number} ({self.user.display_name})"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary account per user per payment method
        if self.is_primary:
            PaymentAccount.objects.filter(
                user=self.user,
                payment_method=self.payment_method,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class PaymentRefund(BaseModel, StatusModel, PriceModel):
    """Payment refunds"""
    
    class RefundReason(models.TextChoices):
        CUSTOMER_REQUEST = 'customer_request', _('Customer Request')
        ORDER_CANCELLED = 'order_cancelled', _('Order Cancelled')
        PRODUCT_UNAVAILABLE = 'product_unavailable', _('Product Unavailable')
        QUALITY_ISSUE = 'quality_issue', _('Quality Issue')
        DELIVERY_FAILED = 'delivery_failed', _('Delivery Failed')
        DUPLICATE_PAYMENT = 'duplicate_payment', _('Duplicate Payment')
        OTHER = 'other', _('Other')
    
    class RefundStatus(models.TextChoices):
        REQUESTED = 'requested', _('Requested')
        APPROVED = 'approved', _('Approved')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        REJECTED = 'rejected', _('Rejected')
        FAILED = 'failed', _('Failed')
    
    # Original payment
    original_payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name='refunds',
        verbose_name=_('original payment')
    )
    
    # Refund details
    refund_number = models.CharField(_('refund number'), max_length=100, unique=True)
    refund_reason = models.CharField(
        _('refund reason'),
        max_length=20,
        choices=RefundReason.choices
    )
    refund_status = models.CharField(
        _('refund status'),
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.REQUESTED
    )
    
    # Amount details
    refund_amount = models.DecimalField(_('refund amount'), max_digits=12, decimal_places=2)
    refund_fee = models.DecimalField(_('refund fee'), max_digits=12, decimal_places=2, default=0)
    net_refund = models.DecimalField(_('net refund'), max_digits=12, decimal_places=2)
    
    # Parties
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='refund_requests',
        verbose_name=_('requested by')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='refund_approvals',
        verbose_name=_('approved by')
    )
    
    # Important dates
    requested_at = models.DateTimeField(_('requested at'), auto_now_add=True)
    approved_at = models.DateTimeField(_('approved at'), blank=True, null=True)
    processed_at = models.DateTimeField(_('processed at'), blank=True, null=True)
    
    # Additional information
    reason_description = models.TextField(_('reason description'), blank=True)
    admin_notes = models.TextField(_('admin notes'), blank=True)
    
    # Gateway details
    gateway_refund_id = models.CharField(_('gateway refund ID'), max_length=255, blank=True)
    gateway_response = models.JSONField(_('gateway response'), default=dict, blank=True)
    
    class Meta:
        db_table = 'payment_refunds'
        verbose_name = _('Payment Refund')
        verbose_name_plural = _('Payment Refunds')
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['original_payment']),
            models.Index(fields=['refund_number']),
            models.Index(fields=['refund_status']),
            models.Index(fields=['requested_by']),
            models.Index(fields=['requested_at']),
        ]
    
    def __str__(self):
        return f"Refund {self.refund_number} - {self.refund_amount} {self.currency}"
    
    def calculate_net_refund(self):
        """Calculate net refund amount after fees"""
        self.net_refund = self.refund_amount - self.refund_fee
        return self.net_refund


class PaymentWebhook(BaseModel):
    """Store webhook events from payment gateways"""
    
    class WebhookStatus(models.TextChoices):
        RECEIVED = 'received', _('Received')
        PROCESSING = 'processing', _('Processing')
        PROCESSED = 'processed', _('Processed')
        FAILED = 'failed', _('Failed')
        IGNORED = 'ignored', _('Ignored')
    
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.CASCADE,
        related_name='webhooks',
        verbose_name=_('payment method')
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks',
        verbose_name=_('payment')
    )
    
    # Webhook details
    webhook_id = models.CharField(_('webhook ID'), max_length=255, unique=True)
    event_type = models.CharField(_('event type'), max_length=100)
    event_data = models.JSONField(_('event data'), default=dict)
    
    # Processing status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=WebhookStatus.choices,
        default=WebhookStatus.RECEIVED
    )
    processed_at = models.DateTimeField(_('processed at'), blank=True, null=True)
    error_message = models.TextField(_('error message'), blank=True)
    
    # HTTP details
    headers = models.JSONField(_('HTTP headers'), default=dict, blank=True)
    signature = models.CharField(_('signature'), max_length=500, blank=True)
    is_verified = models.BooleanField(_('is verified'), default=False)
    
    class Meta:
        db_table = 'payment_webhooks'
        verbose_name = _('Payment Webhook')
        verbose_name_plural = _('Payment Webhooks')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['webhook_id']),
            models.Index(fields=['payment_method']),
            models.Index(fields=['payment']),
            models.Index(fields=['event_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.webhook_id} - {self.event_type}"