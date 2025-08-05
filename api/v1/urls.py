"""
API v1 URL patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .docs import APIDocumentationView

# Import ViewSets
from apps.products.views import ProductViewSet, ProductCategoryViewSet
from apps.orders.views import OrderViewSet

# Create router
router = DefaultRouter()
router.register(r'products/categories', ProductCategoryViewSet, basename='productcategory')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')

@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Kikapu Platform API v1',
        'version': '1.0.0',
        'endpoints': {
            'authentication': '/api/v1/auth/',
            'products': '/api/v1/products/',
            'orders': '/api/v1/orders/',
            'payments': '/api/v1/payments/',
            'health': '/health/',
            'admin': '/admin/',
            'documentation': '/api/v1/docs/',
        },
        'status': 'Production Ready',
        'features': [
            'JWT Authentication',
            'Product Management',
            'Order Processing', 
            'Payment Integration',
            'Real-time Notifications',
            'Advanced Search & Filtering'
        ]
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    
    # Documentation
    path('docs/', APIDocumentationView.as_view(), name='api-docs'),
    
    # Authentication
    path('auth/', include('apps.authentication.urls')),
    
    # Products
    path('products/', include('apps.products.urls')),
    
    # Orders  
    path('orders/', include('apps.orders.urls')),
    
    # Payments
    path('payments/', include('apps.payments.urls')),
    
    # Router URLs (for ViewSets)
    path('', include(router.urls)),

    # # User management
    # path('users/', include('apps.users.urls')),
    
    # # Marketplace
    # path('marketplace/', include('apps.marketplace.urls')),
    
    # # Notifications
    # path('notifications/', include('apps.notifications.urls')),
    
    # # Smart Farming
    # path('farming/', include('apps.smart_farming.urls')),
    
    # # Logistics
    # path('logistics/', include('apps.logistics.urls')),
    
    # # Waste Management
    # path('waste/', include('apps.waste_management.urls')),
    
    # # Processing
    # path('processing/', include('apps.processing.urls')),
    
    # # Analytics
    # path('analytics/', include('apps.analytics.urls')),
    
    # # Community
    # path('community/', include('apps.community.urls')),
    
    # # Support
    # path('support/', include('apps.support.urls')),
    
    # # Settings
    # path('settings/', include('apps.settings.urls')),
]