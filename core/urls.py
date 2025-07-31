"""
Core URLs for health checks and utilities
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.HealthCheckView.as_view(), name='health-check'),
    path('db/', views.DatabaseHealthView.as_view(), name='db-health'),
]