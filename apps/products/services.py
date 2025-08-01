"""
Products services - Business logic layer
"""
from django.db import transaction
from django.db.models import Q, Count, Avg, F
from django.utils import timezone
from decimal import Decimal
from .models import (
    Product, ProductCategory, ProductInventoryLog, 
    ProductPriceHistory, ProductReview
)


class ProductService:
    """Service class for product business logic"""
    
    @staticmethod
    def search_products(q=None, category=None, product_type=None, 
                       quality_grade=None, min_price=None, max_price=None,
                       location=None, in_stock=None, featured=None,
                       seller=None, ordering='-created_at', user=None):
        """Advanced product search with filters"""
        
        queryset = Product.objects.filter(
            status='active'
        ).select_related('seller', 'category').prefetch_related('images')
        
        # Only show available products for non-staff users
        if not (user and user.is_staff):
            queryset = queryset.filter(is_available=True)
        
        # Text search
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(tags__icontains=q) |
                Q(origin_location__icontains=q)
            )
        
        # Category filter
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Product type filter
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Quality grade filter
        if quality_grade:
            queryset = queryset.filter(quality_grade=quality_grade)
        
        # Price range filter
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        
        # Location filter
        if location:
            queryset = queryset.filter(origin_location__icontains=location)
        
        # Stock filter
        if in_stock:
            queryset = queryset.filter(stock_quantity__gt=0)
        
        # Featured filter
        if featured:
            queryset = queryset.filter(is_featured=True)
        
        # Seller filter
        if seller:
            queryset = queryset.filter(seller_id=seller)
        
        # Apply ordering
        if ordering:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @staticmethod
    def get_categories_with_product_counts():
        """Get categories with product counts"""
        categories = ProductCategory.objects.filter(
            status='active'
        ).annotate(
            product_count=Count('products', filter=Q(
                products__status='active',
                products__is_available=True
            ))
        ).order_by('sort_order', 'name')
        
        return [
            {
                'id': str(category.id),
                'name': category.name,
                'description': category.description,
                'image': category.image.url if category.image else None,
                'product_count': category.product_count,
                'is_agricultural': category.is_agricultural,
                'seasonal': category.seasonal,
                'perishable': category.perishable,
            }
            for category in categories
        ]
    
    @staticmethod
    @transaction.atomic
    def update_stock(product, quantity_change, change_type, notes='', 
                    reference_id='', user=None):
        """Update product stock with logging"""
        
        if not isinstance(quantity_change, int):
            raise ValueError("Quantity change must be an integer")
        
        previous_quantity = product.stock_quantity
        new_quantity = previous_quantity + quantity_change
        
        if new_quantity < 0:
            raise ValueError("Insufficient stock")
        
        # Update product stock
        product.stock_quantity = new_quantity
        product.save(update_fields=['stock_quantity'])
        
        # Log the change
        ProductInventoryLog.objects.create(
            product=product,
            change_type=change_type,
            quantity_change=quantity_change,
            previous_quantity=previous_quantity,
            new_quantity=new_quantity,
            reference_id=reference_id,
            notes=notes,
            created_by=user
        )
        
        return product
    
    @staticmethod
    @transaction.atomic
    def update_price(product, new_price, change_reason='', user=None):
        """Update product price with history logging"""
        
        if new_price <= 0:
            raise ValueError("Price must be greater than zero")
        
        old_price = product.price
        
        # Update product price
        product.price = new_price
        product.save(update_fields=['price'])
        
        # Log price change
        ProductPriceHistory.objects.create(
            product=product,
            old_price=old_price,
            new_price=new_price,
            currency=product.currency,
            change_reason=change_reason,
            effective_date=timezone.now(),
            created_by=user
        )
        
        return product
    
    @staticmethod
    def update_product_rating(product_id):
        """Update product average rating based on reviews"""
        try:
            product = Product.objects.get(id=product_id)
            
            # Calculate average rating
            reviews = ProductReview.objects.filter(
                product=product,
                is_approved=True
            )
            
            if reviews.exists():
                avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
                rating_count = reviews.count()
                
                product.rating = round(avg_rating, 2)
                product.rating_count = rating_count
            else:
                product.rating = 0.00
                product.rating_count = 0
            
            product.save(update_fields=['rating', 'rating_count'])
            return product
            
        except Product.DoesNotExist:
            raise ValueError("Product not found")
    
    @staticmethod
    def get_product_statistics(product):
        """Get comprehensive product statistics"""
        reviews = ProductReview.objects.filter(product=product, is_approved=True)
        
        # Rating distribution
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[f'{i}_star'] = reviews.filter(rating=i).count()
        
        # Recent reviews
        recent_reviews = reviews.order_by('-created_at')[:5]
        
        # Inventory movements
        recent_inventory = ProductInventoryLog.objects.filter(
            product=product
        ).order_by('-created_at')[:10]
        
        # Price history
        price_history = ProductPriceHistory.objects.filter(
            product=product
        ).order_by('-effective_date')[:10]
        
        return {
            'total_reviews': reviews.count(),
            'average_rating': product.rating,
            'rating_distribution': rating_distribution,
            'recent_reviews': [
                {
                    'rating': review.rating,
                    'title': review.title,
                    'reviewer': review.reviewer.display_name,
                    'created_at': review.created_at
                }
                for review in recent_reviews
            ],
            'stock_movements': [
                {
                    'change_type': log.change_type,
                    'quantity_change': log.quantity_change,
                    'new_quantity': log.new_quantity,
                    'created_at': log.created_at,
                    'notes': log.notes
                }
                for log in recent_inventory
            ],
            'price_history': [
                {
                    'old_price': history.old_price,
                    'new_price': history.new_price,
                    'change_reason': history.change_reason,
                    'effective_date': history.effective_date
                }
                for history in price_history
            ]
        }
    
    @staticmethod
    def get_seller_products_summary(seller):
        """Get summary of seller's products"""
        products = Product.objects.filter(seller=seller)
        
        total_products = products.count()
        active_products = products.filter(status='active', is_available=True).count()
        out_of_stock = products.filter(stock_quantity=0).count()
        low_stock = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F('minimum_order_quantity')
        ).count()
        
        # Revenue calculations (from completed orders)
        from apps.orders.models import Order, OrderItem
        
        total_revenue = OrderItem.objects.filter(
            product__seller=seller,
            order__order_status='delivered'
        ).aggregate(
            total=models.Sum(F('quantity') * F('unit_price'))
        )['total'] or Decimal('0.00')
        
        return {
            'total_products': total_products,
            'active_products': active_products,
            'out_of_stock_products': out_of_stock,
            'low_stock_products': low_stock,
            'total_revenue': total_revenue,
            'featured_products': products.filter(is_featured=True).count(),
        }
    
    @staticmethod
    def get_trending_products(limit=10):
        """Get trending products based on recent activity"""
        from django.db.models import Count
        from datetime import timedelta
        
        # Get products with most orders in last 7 days
        week_ago = timezone.now() - timedelta(days=7)
        
        trending = Product.objects.filter(
            status='active',
            is_available=True,
            order_items__order__order_date__gte=week_ago
        ).annotate(
            recent_orders=Count('order_items')
        ).order_by('-recent_orders', '-rating')[:limit]
        
        return trending
    
    @staticmethod
    def get_recommended_products(user, limit=10):
        """Get recommended products for user"""
        if not user.is_authenticated:
            # For anonymous users, return featured products
            return Product.objects.filter(
                status='active',
                is_available=True,
                is_featured=True
            )[:limit]
        
        # For logged-in users, basic recommendation based on:
        # 1. Products from same categories as previously ordered
        # 2. Products from same location
        # 3. Highly rated products
        
        from apps.orders.models import OrderItem
        
        # Get user's order history
        user_orders = OrderItem.objects.filter(
            order__buyer=user
        ).values_list('product__category', flat=True).distinct()
        
        if user_orders:
            # Recommend products from same categories
            recommended = Product.objects.filter(
                status='active',
                is_available=True,
                category__in=user_orders
            ).exclude(
                seller=user  # Don't recommend user's own products
            ).order_by('-rating', '-created_at')[:limit]
        else:
            # For new users, recommend highly rated products
            recommended = Product.objects.filter(
                status='active',
                is_available=True,
                rating__gte=4.0
            ).order_by('-rating', '-created_at')[:limit]
        
        return recommended
    
    @staticmethod
    def check_product_availability(product, quantity):
        """Check if product is available for given quantity"""
        if not product.is_available or product.status != 'active':
            return False, "Product is not available"
        
        if product.stock_quantity < quantity:
            return False, f"Only {product.stock_quantity} units available"
        
        if quantity < product.minimum_order_quantity:
            return False, f"Minimum order quantity is {product.minimum_order_quantity}"
        
        if product.maximum_order_quantity and quantity > product.maximum_order_quantity:
            return False, f"Maximum order quantity is {product.maximum_order_quantity}"
        
        if product.is_expired:
            return False, "Product has expired"
        
        return True, "Available"
    
    @staticmethod
    def bulk_update_prices(products_data, user=None):
        """Bulk update product prices"""
        updated_products = []
        
        with transaction.atomic():
            for data in products_data:
                try:
                    product = Product.objects.get(id=data['product_id'])
                    ProductService.update_price(
                        product=product,
                        new_price=data['new_price'],
                        change_reason=data.get('reason', 'Bulk price update'),
                        user=user
                    )
                    updated_products.append(product)
                except Product.DoesNotExist:
                    continue
        
        return updated_products
    
    @staticmethod
    def get_low_stock_products(seller=None, threshold=None):
        """Get products with low stock"""
        queryset = Product.objects.filter(status='active')
        
        if seller:
            queryset = queryset.filter(seller=seller)
        
        if threshold:
            queryset = queryset.filter(stock_quantity__lte=threshold)
        else:
            # Use minimum order quantity as threshold
            queryset = queryset.filter(stock_quantity__lte=F('minimum_order_quantity'))
        
        return queryset.order_by('stock_quantity')
    
    @staticmethod
    def get_expiring_products(days_ahead=7, seller=None):
        """Get products expiring within specified days"""
        from datetime import date, timedelta
        
        expiry_date = date.today() + timedelta(days=days_ahead)
        
        queryset = Product.objects.filter(
            status='active',
            expiry_date__isnull=False,
            expiry_date__lte=expiry_date
        )
        
        if seller:
            queryset = queryset.filter(seller=seller)
        
        return queryset.order_by('expiry_date')
    
    @staticmethod
    def generate_sku(category, product_name):
        """Generate unique SKU for product"""
        import re
        
        # Get category prefix (first 3 letters)
        category_prefix = re.sub(r'[^A-Z]', '', category.name.upper())[:3]
        
        # Get product prefix (first 3 letters)
        product_prefix = re.sub(r'[^A-Z]', '', product_name.upper())[:3]
        
        # Get next number
        prefix = f"{category_prefix}{product_prefix}"
        last_product = Product.objects.filter(
            sku__startswith=prefix
        ).order_by('-sku').first()
        
        if last_product:
            try:
                last_number = int(last_product.sku[len(prefix):])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        return f"{prefix}{next_number:03d}"