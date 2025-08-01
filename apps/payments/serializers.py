"""
Payments serializers
"""
from rest_framework import serializers
from .models import PaymentMethod, Payment, PaymentAccount, PaymentRefund


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Payment method serializer"""
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'method_type', 'provider', 'is_active',
            'is_default', 'processing_fee_percentage', 'processing_fee_fixed',
            'minimum_amount', 'maximum_amount', 'supported_currencies'
        ]
        read_only_fields = ['id']


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer"""
    
    payer_name = serializers.CharField(source='payer.display_name', read_only=True)
    payee_name = serializers.CharField(source='payee.display_name', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    
    # Calculated fields
    is_successful = serializers.ReadOnlyField()
    is_pending = serializers.ReadOnlyField()
    can_be_refunded = serializers.ReadOnlyField()
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'reference_number', 'external_reference',
            'payment_type', 'payment_status', 'payer_name', 'payee_name',
            'payment_method_name', 'order_number', 'gross_amount',
            'fee_amount', 'net_amount', 'currency', 'description',
            'initiated_at', 'processed_at', 'expires_at', 'is_verified',
            'is_successful', 'is_pending', 'can_be_refunded'
        ]
        read_only_fields = [
            'id', 'payment_id', 'reference_number', 'initiated_at',
            'processed_at', 'net_amount'
        ]


class PaymentAccountSerializer(serializers.ModelSerializer):
    """Payment account serializer"""
    
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    
    class Meta:
        model = PaymentAccount
        fields = [
            'id', 'payment_method', 'payment_method_name', 'account_name',
            'account_number', 'account_holder_name', 'bank_name',
            'bank_code', 'phone_number', 'provider_name', 'is_primary',
            'is_verified', 'daily_limit', 'monthly_limit', 'status'
        ]
        read_only_fields = ['id', 'is_verified', 'verification_date']
    
    def validate_account_number(self, value):
        """Validate account number uniqueness per user"""
        user = self.context['request'].user
        payment_method = self.initial_data.get('payment_method')
        
        if self.instance:
            # Update case
            existing = PaymentAccount.objects.filter(
                user=user,
                payment_method=payment_method,
                account_number=value
            ).exclude(id=self.instance.id)
        else:
            # Create case
            existing = PaymentAccount.objects.filter(
                user=user,
                payment_method=payment_method,
                account_number=value
            )
        
        if existing.exists():
            raise serializers.ValidationError(
                "You already have an account with this number for this payment method"
            )
        
        return value


class PaymentRefundSerializer(serializers.ModelSerializer):
    """Payment refund serializer"""
    
    original_payment_reference = serializers.CharField(
        source='original_payment.reference_number', 
        read_only=True
    )
    requested_by_name = serializers.CharField(
        source='requested_by.display_name', 
        read_only=True
    )
    
    class Meta:
        model = PaymentRefund
        fields = [
            'id', 'refund_number', 'original_payment_reference',
            'refund_reason', 'refund_status', 'refund_amount',
            'refund_fee', 'net_refund', 'currency', 'requested_by_name',
            'reason_description', 'requested_at', 'approved_at',
            'processed_at'
        ]
        read_only_fields = [
            'id', 'refund_number', 'net_refund', 'requested_at',
            'approved_at', 'processed_at'
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """Payment creation serializer"""
    
    order_id = serializers.UUIDField(required=True)
    payment_method_id = serializers.UUIDField(required=True)
    payment_account_id = serializers.UUIDField(required=False)
    
    def validate_order_id(self, value):
        """Validate order exists and belongs to user"""
        from apps.orders.models import Order
        
        try:
            order = Order.objects.get(id=value)
            if order.buyer != self.context['request'].user:
                raise serializers.ValidationError("Order not found")
            
            if order.payment_status == 'paid':
                raise serializers.ValidationError("Order is already paid")
            
            self.context['order'] = order
            return value
        except Order.DoesNotExist:
            raise serializers.ValidationError("Order not found")
    
    def validate_payment_method_id(self, value):
        """Validate payment method exists and is active"""
        try:
            payment_method = PaymentMethod.objects.get(
                id=value, 
                is_active=True, 
                status='active'
            )
            self.context['payment_method'] = payment_method
            return value
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError("Payment method not available")
    
    def validate_payment_account_id(self, value):
        """Validate payment account belongs to user"""
        if value:
            try:
                account = PaymentAccount.objects.get(
                    id=value,
                    user=self.context['request'].user,
                    status='active'
                )
                self.context['payment_account'] = account
                return value
            except PaymentAccount.DoesNotExist:
                raise serializers.ValidationError("Payment account not found")
        return value