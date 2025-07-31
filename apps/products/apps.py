"""
Products app configuration
"""
from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = 'Products'
    
    def ready(self):
        # Import signals when app is ready
        try:
            from . import signals
        except ImportError:
            pass