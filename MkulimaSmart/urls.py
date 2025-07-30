"""
URL configuration for MkulimaSmart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from website.views import (
    HomeView, 
    weather_view, 
    dashboard_preview, 
    register_farm, 
    ContactView
)

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Website URLs
    path('', HomeView.as_view(), name='home'),
    path('weather/', weather_view, name='weather'),
    path('dashboard-preview/', dashboard_preview, name='dashboard_preview'),
    path('register-farm/', register_farm, name='register_farm'),
    path('contact/', ContactView.as_view(), name='contact'),
    
    # Add more app URLs here
    # path('accounts/', include('accounts.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
