"""
Products admin configuration
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    ProductCategory, Product, ProductImage, ProductVariant,
    ProductReview, ProductInventoryLog, ProductPriceHistory
)


class ProductImageInline(admin.TabularInline):
    """Inline for product images"""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']


class ProductVariantInline(admin.TabularInline):
    """Inline for product variants"""
    model = ProductVariant
    extra = 0
    fields = ['name', 'sku', 'stock_quantity', 'price_adjustment', 'is_active']


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """Product category admin"""
    
    list_display = ['name', 'parent', 'is_agricultural', 'seasonal', 'status', 'sort_order']
    list_filter = ['is_agricultural', 'seasonal', 'perishable', 'status', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'parent', 'image')
        }),
        (_('SEO'), {
            'fields': ('slug', 'meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('Category Properties'), {
            'fields': ('is_agricultural', 'seasonal', 'perishable')
        }),
        (_('Display'), {
            'fields': ('status', 'sort_order')
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin"""
    
    list_display = [
        'name', 'seller', 'category', 'product_type', 'price', 
        'stock_quantity', 'status', 'is_featured', 'created_at'
    ]
    list_filter = [
        'product_type', 'quality_grade', 'status', 'is_featured', 
        'is_available', 'category', 'created_at'
    ]
    search_fields = ['name', 'sku', 'description', 'seller__email']
    ordering = ['-created_at']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at', 'rating', 'rating_count']
    
    inlines = [ProductImageInline, ProductVariantInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'short_description', 'category', 
                      'product_type', 'seller')
        }),
        (_('Product Details'), {
            'fields': ('sku', 'barcode', 'quality_grade', 'origin_location', 
                      'harvest_date', 'expiry_date')
        }),
        (_('Measurements'), {
            'fields': ('weight_kg', 'unit_of_measure')
        }),
        (_('Inventory'), {
            'fields': ('stock_quantity', 'minimum_order_quantity', 'maximum_order_quantity')
        }),
        (_('Pricing'), {
            'fields': ('price', 'currency', 'cost_price', 'wholesale_price', 'retail_price')
        }),
        (_('Logistics'), {
            'fields': ('requires_cold_storage', 'fragile', 'hazardous')
        }),
        (_('Additional Information'), {
            'fields': ('nutritional_info', 'certifications', 'tags'),
            'classes': ('collapse',)
        }),
        (_('SEO'), {
            'fields': ('slug', 'meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        (_('Status & Visibility'), {
            'fields': ('status', 'is_featured', 'is_available', 'published_at')
        }),
        (_('Statistics'), {
            'fields': ('rating', 'rating_count'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('seller', 'category')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Product image admin"""
    
    list_display = ['product', 'alt_text', 'is_primary', 'sort_order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    ordering = ['product', 'sort_order']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """Product variant admin"""
    
    list_display = ['product', 'name', 'sku', 'stock_quantity', 'final_price', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__name', 'name', 'sku']
    ordering = ['product', 'name']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Product review admin"""
    
    list_display = [
        'product', 'reviewer', 'rating', 'is_verified_purchase', 
        'is_approved', 'helpful_count', 'created_at'
    ]
    list_filter = ['rating', 'is_verified_purchase', 'is_approved', 'created_at']
    search_fields = ['product__name', 'reviewer__email', 'title', 'comment']
    ordering = ['-created_at']
    readonly_fields = ['helpful_count', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Review Details'), {
            'fields': ('product', 'reviewer', 'rating', 'title', 'comment')
        }),
        (_('Status'), {
            'fields': ('is_verified_purchase', 'is_approved')
        }),
        (_('Additional'), {
            'fields': ('images', 'helpful_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductInventoryLog)
class ProductInventoryLogAdmin(admin.ModelAdmin):
    """Product inventory log admin"""
    
    list_display = [
        'product', 'variant', 'change_type', 'quantity_change', 
        'new_quantity', 'reference_id', 'created_at'
    ]
    list_filter = ['change_type', 'created_at']
    search_fields = ['product__name', 'reference_id', 'notes']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # These are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # These should not be modified


@admin.register(ProductPriceHistory)
class ProductPriceHistoryAdmin(admin.ModelAdmin):
    """Product price history admin"""
    
    list_display = [
        'product', 'variant', 'old_price', 'new_price', 
        'currency', 'effective_date', 'created_at'
    ]
    list_filter = ['currency', 'effective_date', 'created_at']
    search_fields = ['product__name', 'change_reason']
    ordering = ['-effective_date']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # These are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # These should not be modified