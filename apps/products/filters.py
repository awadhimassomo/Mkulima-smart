"""
Products filters
"""
import django_filters
from django.db.models import Q
from .models import Product, ProductCategory


class ProductFilter(django_filters.FilterSet):
    """Filter set for products"""
    
    # Text search
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Category filters
    category = django_filters.ModelChoiceFilter(
        queryset=ProductCategory.objects.filter(status='active'),
        label='Category'
    )
    category_name = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains',
        label='Category Name'
    )
    
    # Price range
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    price_range = django_filters.RangeFilter(field_name='price')
    
    # Product type and quality
    product_type = django_filters.ChoiceFilter(choices=Product.ProductType.choices)
    quality_grade = django_filters.ChoiceFilter(choices=Product.QualityGrade.choices)
    
    # Location
    location = django_filters.CharFilter(
        field_name='origin_location',
        lookup_expr='icontains',
        label='Origin Location'
    )
    
    # Seller
    seller = django_filters.UUIDFilter(field_name='seller__id')
    seller_name = django_filters.CharFilter(
        field_name='seller__full_name',
        lookup_expr='icontains'
    )
    
    # Stock status
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    
    # Product status
    featured = django_filters.BooleanFilter(field_name='is_featured')
    available = django_filters.BooleanFilter(field_name='is_available')
    
    # Rating
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Expiry filters
    expires_within_days = django_filters.NumberFilter(method='filter_expires_within_days')
    
    class Meta:
        model = Product
        fields = [
            'search', 'category', 'category_name', 'min_price', 'max_price',
            'product_type', 'quality_grade', 'location', 'seller',
            'seller_name', 'in_stock', 'low_stock', 'featured',
            'available', 'min_rating', 'created_after', 'created_before'
        ]
    
    def filter_search(self, queryset, name, value):
        """Custom search filter"""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value) |
                Q(short_description__icontains=value) |
                Q(tags__icontains=value) |
                Q(sku__icontains=value) |
                Q(origin_location__icontains=value)
            )
        return queryset
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products in stock"""
        if value:
            return queryset.filter(stock_quantity__gt=0)
        elif value is False:
            return queryset.filter(stock_quantity=0)
        return queryset
    
    def filter_low_stock(self, queryset, name, value):
        """Filter products with low stock"""
        if value:
            return queryset.filter(
                stock_quantity__gt=0,
                stock_quantity__lte=models.F('minimum_order_quantity')
            )
        return queryset
    
    def filter_expires_within_days(self, queryset, name, value):
        """Filter products expiring within specified days"""
        if value:
            from datetime import date, timedelta
            expiry_date = date.today() + timedelta(days=int(value))
            return queryset.filter(
                expiry_date__isnull=False,
                expiry_date__lte=expiry_date
            )
        return queryset