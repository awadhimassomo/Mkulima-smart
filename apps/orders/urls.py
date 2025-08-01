"""
Orders URL patterns
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'', views.OrderViewSet, basename='orders')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Individual view URLs
    path('list/', views.OrderListView.as_view(), name='order-list-simple'),
    path('<uuid:pk>/detail/', views.OrderDetailView.as_view(), name='order-detail-simple'),
]