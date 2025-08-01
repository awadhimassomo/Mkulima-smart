"""
Products views
"""
from rest_framework import generics, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from .models import ProductCategory, Product, ProductReview
from .serializers import (
    ProductCategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateUpdateSerializer, ProductReviewSerializer, ProductSearchSerializer
)
from .services import ProductService
from .filters import ProductFilter


class ProductCategoryViewSet(ModelViewSet):
    """Product category viewset"""
    
    queryset = ProductCategory.objects.filter(status='active')
    serializer_class = ProductCategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by parent category
        parent = self.request.query_params.get('parent')
        if parent == 'null':
            queryset = queryset.filter(parent__isnull=True)
        elif parent:
            queryset = queryset.filter(parent=parent)
        
        # Filter by agricultural products
        is_agricultural = self.request.query_params.get('is_agricultural')
        if is_agricultural:
            queryset = queryset.filter(is_agricultural=is_agricultural.lower() == 'true')
        
        return queryset


class ProductViewSet(ModelViewSet):
    """Product viewset"""
    
    queryset = Product.objects.filter(
        status='active'
    ).select_related('seller', 'category').prefetch_related('images', 'reviews')
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'tags', 'origin_location']
    ordering_fields = ['name', 'price', 'created_at', 'rating', 'stock_quantity']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # For non-owners, only show available products
        if self.action == 'list' and not self.request.user.is_staff:
            queryset = queryset.filter(is_available=True)
        
        # Filter by seller (for seller's own products)
        if self.action == 'list' and self.request.query_params.get('my_products'):
            if self.request.user.is_authenticated:
                queryset = Product.objects.filter(seller=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set seller to current user"""
        serializer.save(seller=self.request.user)
    
    def perform_update(self, serializer):
        """Only allow seller to update their own products"""
        if serializer.instance.seller != self.request.user and not self.request.user.is_staff:
            raise PermissionError("You can only update your own products")
        serializer.save()
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_to_favorites(self, request, pk=None):
        """Add product to user favorites"""
        product = self.get_object()
        # TODO: Implement favorites functionality
        return Response({'message': 'Added to favorites'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def update_stock(self, request, pk=None):
        """Update product stock"""
        product = self.get_object()
        
        if product.seller != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        quantity = request.data.get('quantity')
        if quantity is None:
            return Response(
                {'error': 'Quantity is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            ProductService.update_stock(
                product=product,
                quantity_change=int(quantity),
                change_type='adjustment',
                notes=request.data.get('notes', ''),
                user=request.user
            )
            
            return Response({
                'message': 'Stock updated successfully',
                'new_stock': product.stock_quantity
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced product search"""
        serializer = ProductSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        products = ProductService.search_products(
            **serializer.validated_data,
            user=request.user
        )
        
        # Paginate results
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        products = self.get_queryset().filter(is_featured=True)[:10]
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def categories_with_products(self, request):
        """Get categories with product counts"""
        categories = ProductService.get_categories_with_product_counts()
        return Response(categories)


class ProductReviewViewSet(ModelViewSet):
    """Product review viewset"""
    
    serializer_class = ProductReviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        product_id = self.kwargs.get('product_pk')
        return ProductReview.objects.filter(
            product_id=product_id,
            is_approved=True
        ).select_related('reviewer')
    
    def perform_create(self, serializer):
        """Create review for product"""
        product_id = self.kwargs.get('product_pk')
        serializer.save(
            reviewer=self.request.user,
            product_id=product_id
        )
        
        # Update product rating
        ProductService.update_product_rating(product_id)


# Individual API Views (for simpler endpoints)
class ProductListView(generics.ListAPIView):
    """Product list API view"""
    queryset = Product.objects.filter(status='active', is_available=True)
    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']


class ProductDetailView(generics.RetrieveAPIView):
    """Product detail API view"""
    queryset = Product.objects.filter(status='active')
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]