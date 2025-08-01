"""
Products serializers
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    ProductCategory, Product, ProductImage, ProductVariant,
    ProductReview, ProductInventoryLog, ProductPriceHistory
)

User = get_user_model()


class ProductCategorySerializer(serializers.ModelSerializer):
    """Product category serializer"""
    
    full_path = serializers.ReadOnlyField()
    level = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'description', 'parent', 'image',
            'slug', 'sort_order', 'is_agricultural', 'seasonal',
            'perishable', 'status', 'full_path', 'level', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer"""
    
    class Meta:
        model = ProductImage
        fields = [
            'id', 'image', 'alt_text', 'is_primary', 'sort_order'
        ]
        read_only_fields = ['id']


class ProductVariantSerializer(serializers.ModelSerializer):
    """Product variant serializer"""
    
    final_price = serializers.ReadOnlyField()
    is_in_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'attributes', 'stock_quantity',
            'weight_kg', 'price_adjustment', 'final_price',
            'is_active', 'is_in_stock'
        ]
        read_only_fields = ['id']


class ProductReviewSerializer(serializers.ModelSerializer):
    """Product review serializer"""
    
    reviewer_name = serializers.CharField(source='reviewer.display_name', read_only=True)
    reviewer_avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'rating', 'title', 'comment', 'reviewer_name',
            'reviewer_avatar', 'is_verified_purchase', 'helpful_count',
            'images', 'created_at'
        ]
        read_only_fields = ['id', 'reviewer', 'is_verified_purchase', 'helpful_count']
    
    def get_reviewer_avatar(self, obj):
        if obj.reviewer.avatar:
            return obj.reviewer.avatar.url
        return None


class ProductListSerializer(serializers.ModelSerializer):
    """Product list serializer (minimal fields for performance)"""
    
    seller_name = serializers.CharField(source='seller.display_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_image = serializers.SerializerMethodField()
    is_in_stock = serializers.ReadOnlyField()
    formatted_price = serializers.ReadOnlyField()
    rating_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'short_description', 'seller_name',
            'category_name', 'primary_image', 'price', 'currency',
            'formatted_price', 'stock_quantity', 'unit_of_measure',
            'is_in_stock', 'rating', 'rating_display', 'is_featured',
            'quality_grade', 'origin_location', 'created_at'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image.image.url
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Product detail serializer (all fields)"""
    
    seller = serializers.SerializerMethodField()
    category = ProductCategorySerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ProductReviewSerializer(many=True, read_only=True)
    
    # Calculated fields
    is_in_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_to_expiry = serializers.ReadOnlyField()
    profit_margin = serializers.ReadOnlyField()
    formatted_price = serializers.ReadOnlyField()
    rating_display = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'short_description',
            'category', 'product_type', 'seller', 'sku', 'barcode',
            'quality_grade', 'origin_location', 'harvest_date',
            'expiry_date', 'weight_kg', 'unit_of_measure',
            'stock_quantity', 'minimum_order_quantity', 'maximum_order_quantity',
            'price', 'currency', 'cost_price', 'wholesale_price', 'retail_price',
            'requires_cold_storage', 'fragile', 'hazardous',
            'nutritional_info', 'certifications', 'tags',
            'is_featured', 'is_available', 'status', 'published_at',
            'rating', 'rating_count', 'slug', 'meta_title', 'meta_description',
            'images', 'variants', 'reviews',
            'is_in_stock', 'is_low_stock', 'is_expired', 'days_to_expiry',
            'profit_margin', 'formatted_price', 'rating_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'rating', 'rating_count', 'created_at', 'updated_at'
        ]
    
    def get_seller(self, obj):
        return {
            'id': str(obj.seller.id),
            'name': obj.seller.display_name,
            'user_type': obj.seller.user_type,
            'location': obj.seller.location,
            'avatar': obj.seller.avatar.url if obj.seller.avatar else None,
            'is_verified': obj.seller.is_verified,
        }


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Product create/update serializer"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category',
            'product_type', 'sku', 'barcode', 'quality_grade',
            'origin_location', 'harvest_date', 'expiry_date',
            'weight_kg', 'unit_of_measure', 'stock_quantity',
            'minimum_order_quantity', 'maximum_order_quantity',
            'price', 'currency', 'cost_price', 'wholesale_price',
            'retail_price', 'requires_cold_storage', 'fragile',
            'hazardous', 'nutritional_info', 'certifications', 'tags',
            'is_featured', 'is_available', 'slug', 'meta_title',
            'meta_description'
        ]
    
    def validate_sku(self, value):
        """Validate SKU uniqueness"""
        if self.instance:
            # Update case - exclude current instance
            if Product.objects.filter(sku=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("SKU already exists")
        else:
            # Create case
            if Product.objects.filter(sku=value).exists():
                raise serializers.ValidationError("SKU already exists")
        return value
    
    def validate(self, attrs):
        """Custom validation"""
        # Validate price ranges
        if attrs.get('cost_price') and attrs.get('price'):
            if attrs['cost_price'] > attrs['price']:
                raise serializers.ValidationError(
                    "Cost price cannot be higher than selling price"
                )
        
        # Validate stock quantity
        if attrs.get('stock_quantity', 0) < 0:
            raise serializers.ValidationError(
                "Stock quantity cannot be negative"
            )
        
        # Validate expiry date
        if attrs.get('expiry_date') and attrs.get('harvest_date'):
            if attrs['expiry_date'] <= attrs['harvest_date']:
                raise serializers.ValidationError(
                    "Expiry date must be after harvest date"
                )
        
        return attrs
    
    def create(self, validated_data):
        """Create product with seller from request"""
        validated_data['seller'] = self.context['request'].user
        return super().create(validated_data)


class ProductInventoryLogSerializer(serializers.ModelSerializer):
    """Product inventory log serializer"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    
    class Meta:
        model = ProductInventoryLog
        fields = [
            'id', 'product_name', 'variant_name', 'change_type',
            'quantity_change', 'previous_quantity', 'new_quantity',
            'reference_id', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductPriceHistorySerializer(serializers.ModelSerializer):
    """Product price history serializer"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    price_change_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductPriceHistory
        fields = [
            'id', 'product_name', 'variant_name', 'old_price',
            'new_price', 'currency', 'change_reason', 'effective_date',
            'price_change_percentage', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProductSearchSerializer(serializers.Serializer):
    """Product search parameters serializer"""
    
    q = serializers.CharField(required=False, help_text="Search query")
    category = serializers.UUIDField(required=False, help_text="Category ID")
    product_type = serializers.CharField(required=False, help_text="Product type")
    quality_grade = serializers.CharField(required=False, help_text="Quality grade")
    min_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    location = serializers.CharField(required=False, help_text="Origin location")
    in_stock = serializers.BooleanField(required=False, help_text="Only in-stock products")
    featured = serializers.BooleanField(required=False, help_text="Only featured products")
    seller = serializers.UUIDField(required=False, help_text="Seller ID")
    ordering = serializers.ChoiceField(
        choices=[
            'name', '-name', 'price', '-price', 'created_at', '-created_at',
            'rating', '-rating', 'stock_quantity', '-stock_quantity'
        ],
        required=False,
        default='-created_at'
    )