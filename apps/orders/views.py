"""
Orders views
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import Order, OrderItem
from .serializers import (
    OrderListSerializer, OrderDetailSerializer, OrderCreateSerializer,
    OrderUpdateSerializer, OrderStatusUpdateSerializer, OrderSummarySerializer
)
from .services import OrderService
from .filters import OrderFilter


class OrderViewSet(ModelViewSet):
    """Order viewset"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter
    
    def get_queryset(self):
        """Filter orders based on user role"""
        user = self.request.user
        
        if user.is_staff:
            return Order.objects.all()
        
        # Show orders where user is buyer or seller
        return Order.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('buyer', 'seller').prefetch_related('items', 'addresses')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OrderUpdateSerializer
        return OrderDetailSerializer
    
    def perform_create(self, serializer):
        """Create order with buyer as current user"""
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status"""
        order = self.get_object()
        
        # Check permissions
        if not OrderService.check_order_permissions(order, request.user):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = OrderStatusUpdateSerializer(
            data=request.data,
            context={'order': order}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_order = OrderService.update_order_status(
                order=order,
                new_status=serializer.validated_data['new_status'],
                notes=serializer.validated_data.get('notes', ''),
                changed_by=request.user
            )
            
            response_serializer = OrderDetailSerializer(updated_order)
            return Response(response_serializer.data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order"""
        order = self.get_object()
        
        # Check permissions
        if order.buyer != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Only buyer can cancel order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', 'Cancelled by buyer')
        
        try:
            cancelled_order = OrderService.cancel_order(
                order=order,
                reason=reason,
                cancelled_by=request.user
            )
            
            response_serializer = OrderDetailSerializer(cancelled_order)
            return Response(response_serializer.data)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def calculate_summary(self, request):
        """Calculate order summary for checkout"""
        serializer = OrderSummarySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        summary = OrderService.calculate_order_summary(
            items_data=serializer.validated_data['items'],
            discount_code=serializer.validated_data.get('discount_code'),
            buyer=request.user
        )
        
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get current user's orders"""
        orders = OrderService.get_user_order_history(
            user=request.user,
            status=request.query_params.get('status'),
            limit=int(request.query_params.get('limit', 20))
        )
        
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_actions(self, request):
        """Get orders requiring user action"""
        if request.user.user_type in ['farmer', 'processor', 'retailer']:
            orders = OrderService.get_pending_seller_actions(request.user)
        else:
            orders = OrderService.get_buyer_active_orders(request.user)
        
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get order statistics"""
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if request.user.user_type in ['farmer', 'processor', 'retailer']:
            stats = OrderService.get_order_statistics(
                seller=request.user,
                date_from=date_from,
                date_to=date_to
            )
        else:
            stats = OrderService.get_order_statistics(
                buyer=request.user,
                date_from=date_from,
                date_to=date_to
            )
        
        return Response(stats)


# Individual API Views (for simpler endpoints)
class OrderListView(generics.ListCreateAPIView):
    """Order list API view"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).order_by('-order_date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer


class OrderDetailView(generics.RetrieveUpdateAPIView):
    """Order detail API view"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
            Q(buyer=user) | Q(seller=user)
        )
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return OrderUpdateSerializer
        return OrderDetailSerializer