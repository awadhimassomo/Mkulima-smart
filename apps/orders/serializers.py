"""
Orders serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Order, OrderItem, OrderAddress, OrderStatusHistory, OrderDiscount
from apps.products.models import Product, ProductVariant
from apps.products.serializers import ProductListSerializer

User = get_user_model()


class OrderItemSerializer(serializers.ModelSerializer):
    """Order item serializer"""
    
    product_details = ProductListSerializer(source='product', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'quantity', 'unit_price',
            'total_price', 'product_name', 'product_sku',
            'item_status', 'notes', 'product_details', 'variant_name'
        ]
        read_only_fields = [
            'id', 'total_price', 'product_name', 'product_sku'
        ]


class OrderItemCreateSerializer(serializers.ModelSerializer):
    """Order item creation serializer"""
    
    class Meta:
        model = OrderItem
        fields = ['product', 'variant', 'quantity', 'notes']
    
    def validate(self, attrs):
        """Validate order item"""
        product = attrs['product']
        variant = attrs.get('variant')
        quantity = attrs['quantity']
        
        # Check product availability
        from apps.products.services import ProductService
        is_available, message = ProductService.check_product_availability(product, quantity)
        
        if not is_available:
            raise serializers.ValidationError(message)
        
        # Validate variant belongs to product
        if variant and variant.product != product:
            raise serializers.ValidationError("Variant does not belong to this product")
        
        return attrs


class OrderAddressSerializer(serializers.ModelSerializer):
    """Order address serializer"""
    
    full_address = serializers.ReadOnlyField()
    
    class Meta:
        model = OrderAddress
        fields = [
            'id', 'address_type', 'recipient_name', 'phone_number',
            'email', 'address_line_1', 'address_line_2', 'city',
            'state_region', 'postal_code', 'country', 'latitude',
            'longitude', 'delivery_instructions', 'full_address'
        ]
        read_only_fields = ['id']


class OrderDiscountSerializer(serializers.ModelSerializer):
    """Order discount serializer"""
    
    class Meta:
        model = OrderDiscount
        fields = [
            'id', 'discount_type', 'discount_code', 'discount_name',
            'discount_percentage', 'discount_amount', 'maximum_discount'
        ]
        read_only_fields = ['id']


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Order status history serializer"""
    
    changed_by_name = serializers.CharField(source='changed_by.display_name', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'from_status', 'to_status', 'changed_by_name',
            'notes', 'notification_sent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OrderListSerializer(serializers.ModelSerializer):
    """Order list serializer (minimal fields for performance)"""
    
    buyer_name = serializers.CharField(source='buyer.display_name', read_only=True)
    seller_name = serializers.CharField(source='seller.display_name', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'buyer_name', 'seller_name',
            'order_status', 'payment_status', 'order_type',
            'total_amount', 'currency', 'order_date', 'required_date',
            'items_count', 'delivery_method'
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Order detail serializer (all fields)"""
    
    buyer = serializers.SerializerMethodField()
    seller = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    addresses = OrderAddressSerializer(many=True, read_only=True)
    discounts = OrderDiscountSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    # Calculated fields
    is_paid = serializers.ReadOnlyField()
    can_be_cancelled = serializers.ReadOnlyField()
    is_delivered = serializers.ReadOnlyField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'buyer', 'seller', 'order_type',
            'order_status', 'payment_status', 'subtotal', 'tax_amount',
            'shipping_cost', 'discount_amount', 'total_amount', 'currency',
            'order_date', 'required_date', 'shipped_date', 'delivered_date',
            'delivery_method', 'notes', 'special_instructions',
            'tracking_number', 'items', 'addresses', 'discounts',
            'status_history', 'is_paid', 'can_be_cancelled', 'is_delivered',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'subtotal', 'total_amount',
            'order_date', 'shipped_date', 'delivered_date', 'created_at', 'updated_at'
        ]
    
    def get_buyer(self, obj):
        return {
            'id': str(obj.buyer.id),
            'name': obj.buyer.display_name,
            'email': obj.buyer.email,
            'phone': obj.buyer.phone_number,
            'user_type': obj.buyer.user_type,
        }
    
    def get_seller(self, obj):
        return {
            'id': str(obj.seller.id),
            'name': obj.seller.display_name,
            'email': obj.seller.email,
            'phone': obj.seller.phone_number,
            'user_type': obj.seller.user_type,
            'location': obj.seller.location,
        }


class OrderCreateSerializer(serializers.ModelSerializer):
    """Order creation serializer"""
    
    items = OrderItemCreateSerializer(many=True)
    billing_address = OrderAddressSerializer(required=False)
    shipping_address = OrderAddressSerializer(required=False)
    
    class Meta:
        model = Order
        fields = [
            'seller', 'order_type', 'delivery_method', 'required_date',
            'notes', 'special_instructions', 'items', 'billing_address',
            'shipping_address'
        ]
    
    def validate_items(self, value):
        """Validate order items"""
        if not value:
            raise serializers.ValidationError("Order must have at least one item")
        
        # Check all items belong to the same seller
        sellers = set(item['product'].seller for item in value)
        if len(sellers) > 1:
            raise serializers.ValidationError("All items must be from the same seller")
        
        return value
    
    def validate(self, attrs):
        """Custom validation"""
        items = attrs['items']
        seller = attrs['seller']
        
        # Ensure seller matches items' seller
        for item in items:
            if item['product'].seller != seller:
                raise serializers.ValidationError("Seller mismatch with product seller")
        
        return attrs
    
    def create(self, validated_data):
        """Create order with items and addresses"""
        from .services import OrderService
        
        items_data = validated_data.pop('items')
        billing_address_data = validated_data.pop('billing_address', None)
        shipping_address_data = validated_data.pop('shipping_address', None)
        
        buyer = self.context['request'].user
        
        # Create order using service
        order = OrderService.create_order(
            buyer=buyer,
            items_data=items_data,
            billing_address_data=billing_address_data,
            shipping_address_data=shipping_address_data,
            **validated_data
        )
        
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Order update serializer (limited fields)"""
    
    class Meta:
        model = Order
        fields = [
            'delivery_method', 'required_date', 'notes',
            'special_instructions'
        ]
    
    def validate(self, attrs):
        """Validate update permissions"""
        order = self.instance
        
        if order.order_status not in ['pending', 'confirmed']:
            raise serializers.ValidationError(
                "Order cannot be modified after processing has started"
            )
        
        return attrs


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Order status update serializer"""
    
    new_status = serializers.ChoiceField(choices=Order.OrderStatus.choices)
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_new_status(self, value):
        """Validate status transition"""
        order = self.context['order']
        current_status = order.order_status
        
        # Define allowed status transitions
        allowed_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],  # Terminal state
            'cancelled': [],  # Terminal state
            'refunded': [],   # Terminal state
        }
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {value}"
            )
        
        return value


class OrderSummarySerializer(serializers.Serializer):
    """Order summary for checkout"""
    
    items = OrderItemCreateSerializer(many=True)
    discount_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate_items(self, value):
        """Validate items for summary calculation"""
        if not value:
            raise serializers.ValidationError("Items are required")
        return value