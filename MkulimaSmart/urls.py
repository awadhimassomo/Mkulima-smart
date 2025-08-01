"""
URL configuration for MkulimaSmart project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # Website URLs
    path('', include('website.urls')),

    # Website URLs
    # path('gov/', include('gova_pp.urls')),
    
    # Add more app URLs here
    # path('accounts/', include('accounts.urls')),

    # API endpoints
    path('api/v1/', include('api.v1.urls')),
    
    # Health check
    path('health/', include('core.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Admin site customization
admin.site.site_header = "Kikapu Platform Administration"
admin.site.site_title = "Kikapu Admin"
admin.site.index_title = "Welcome to Kikapu Administration"