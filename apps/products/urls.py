"""
Products URL patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'categories', views.ProductCategoryViewSet, basename='categories')
router.register(r'', views.ProductViewSet, basename='products')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Individual view URLs
    path('list/', views.ProductListView.as_view(), name='product-list-simple'),
    path('<uuid:pk>/detail/', views.ProductDetailView.as_view(), name='product-detail-simple'),
]