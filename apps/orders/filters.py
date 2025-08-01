"""
Orders filters
"""
import django_filters
from django.db.models import Q
from .models import Order


class OrderFilter(django_filters.FilterSet):
    """Filter set for orders"""
    
    # Status filters
    order_status = django_filters.ChoiceFilter(choices=Order.OrderStatus.choices)
    payment_status = django_filters.ChoiceFilter(choices=Order.PaymentStatus.choices)
    
    # Order type
    order_type = django_filters.ChoiceFilter(choices=Order.OrderType.choices)
    
    # Date filters
    order_date_from = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='gte')
    order_date_to = django_filters.DateTimeFilter(field_name='order_date', lookup_expr='lte')
    
    required_date_from = django_filters.DateTimeFilter(field_name='required_date', lookup_expr='gte')
    required_date_to = django_filters.DateTimeFilter(field_name='required_date', lookup_expr='lte')
    
    # Amount filters
    min_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    max_amount = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    
    # User filters
    buyer = django_filters.UUIDFilter(field_name='buyer__id')
    seller = django_filters.UUIDFilter(field_name='seller__id')
    
    # Text search
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Delivery method
    delivery_method = django_filters.ChoiceFilter(
        choices=[
            ('pickup', 'Pickup'),
            ('delivery', 'Delivery'),
            ('shipping', 'Shipping'),
        ]
    )
    
    class Meta:
        model = Order
        fields = [
            'order_status', 'payment_status', 'order_type', 'delivery_method',
            'order_date_from', 'order_date_to', 'required_date_from', 'required_date_to',
            'min_amount', 'max_amount', 'buyer', 'seller', 'search'
        ]
    
    def filter_search(self, queryset, name, value):
        """Custom search filter"""
        if value:
            return queryset.filter(
                Q(order_number__icontains=value) |
                Q(tracking_number__icontains=value) |
                Q(notes__icontains=value) |
                Q(buyer__email__icontains=value) |
                Q(seller__email__icontains=value) |
                Q(buyer__full_name__icontains=value) |
                Q(seller__full_name__icontains=value)
            )
        return queryset