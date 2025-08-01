"""
Orders services - Business logic layer
"""
import uuid
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from django.conf import settings
from .models import Order, OrderItem, OrderAddress, OrderStatusHistory


class OrderService:
    """Service class for order business logic"""
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        timestamp = timezone.now().strftime('%Y%m%d')
        random_part = str(uuid.uuid4()).replace('-', '')[:8].upper()
        return f"ORD-{timestamp}-{random_part}"
    
    @staticmethod
    @transaction.atomic
    def create_order(buyer, items_data, seller, order_type='direct_purchase',
                    delivery_method='delivery', required_date=None,
                    notes='', special_instructions='',
                    billing_address_data=None, shipping_address_data=None):
        """Create new order with items and addresses"""
        
        # Generate order number
        order_number = OrderService.generate_order_number()
        
        # Calculate order totals
        subtotal = Decimal('0.00')
        
        # Create order
        order = Order.objects.create(
            order_number=order_number,
            buyer=buyer,
            seller=seller,
            order_type=order_type,
            order_status='pending',
            payment_status='pending',
            delivery_method=delivery_method,
            required_date=required_date,
            notes=notes,
            special_instructions=special_instructions,
            subtotal=Decimal('0.00'),
            tax_amount=Decimal('0.00'),
            shipping_cost=Decimal('0.00'),
            discount_amount=Decimal('0.00'),
            total_amount=Decimal('0.00'),
            currency='TZS'
        )
        
        # Create order items
        for item_data in items_data:
            product = item_data['product']
            variant = item_data.get('variant')
            quantity = item_data['quantity']
            notes = item_data.get('notes', '')
            
            # Determine price (use variant price if available)
            if variant:
                unit_price = variant.final_price
            else:
                unit_price = product.price
            
            # Create order item
            order_item = OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=quantity,
                unit_price=unit_price,
                total_price=quantity * unit_price,
                product_name=product.name,
                product_sku=product.sku,
                product_description=product.description,
                notes=notes
            )
            
            subtotal += order_item.total_price
            
            # Update product stock
            from apps.products.services import ProductService
            if variant:
                # Update variant stock (if implemented)
                pass
            else:
                ProductService.update_stock(
                    product=product,
                    quantity_change=-quantity,
                    change_type='sale',
                    reference_id=order_number,
                    notes=f"Order {order_number}",
                    user=buyer
                )
        
        # Calculate totals
        tax_amount = OrderService.calculate_tax(subtotal)
        shipping_cost = OrderService.calculate_shipping_cost(
            order, delivery_method, buyer
        )
        total_amount = subtotal + tax_amount + shipping_cost
        
        # Update order totals
        order.subtotal = subtotal
        order.tax_amount = tax_amount
        order.shipping_cost = shipping_cost
        order.total_amount = total_amount
        order.save()
        
        # Create addresses
        if billing_address_data:
            OrderAddress.objects.create(
                order=order,
                address_type='billing',
                **billing_address_data
            )
        
        if shipping_address_data:
            OrderAddress.objects.create(
                order=order,
                address_type='shipping',
                **shipping_address_data
            )
        
        # Create initial status history
        OrderStatusHistory.objects.create(
            order=order,
            from_status='',
            to_status='pending',
            changed_by=buyer,
            notes='Order created'
        )
        
        # Send notification to seller
        OrderService.notify_new_order(order)
        
        return order
    
    @staticmethod
    def calculate_tax(subtotal):
        """Calculate tax amount"""
        # Tanzania VAT is 18%
        tax_rate = Decimal('0.18')
        return subtotal * tax_rate
    
    @staticmethod
    def calculate_shipping_cost(order, delivery_method, buyer):
        """Calculate shipping cost based on delivery method and location"""
        if delivery_method == 'pickup':
            return Decimal('0.00')
        
        # Basic shipping cost calculation
        # In production, this would integrate with logistics providers
        base_cost = Decimal('5000.00')  # TZS 5,000 base cost
        
        # Add distance-based cost (simplified)
        if hasattr(buyer, 'profile') and buyer.profile.city:
            # Different rates for different cities
            city_rates = {
                'Dar es Salaam': Decimal('0.00'),  # Free local delivery
                'Mwanza': Decimal('10000.00'),
                'Arusha': Decimal('15000.00'),
                'Dodoma': Decimal('12000.00'),
            }
            
            city_cost = city_rates.get(buyer.profile.city, Decimal('20000.00'))
            return base_cost + city_cost
        
        return base_cost
    
    @staticmethod
    @transaction.atomic
    def update_order_status(order, new_status, notes='', changed_by=None):
        """Update order status with history tracking"""
        old_status = order.order_status
        
        if old_status == new_status:
            return order
        
        # Update order status
        order.order_status = new_status
        
        # Set status-specific timestamps
        if new_status == 'shipped':
            order.shipped_date = timezone.now()
        elif new_status == 'delivered':
            order.delivered_date = timezone.now()
        
        order.save()
        
        # Create status history record
        OrderStatusHistory.objects.create(
            order=order,
            from_status=old_status,
            to_status=new_status,
            changed_by=changed_by,
            notes=notes
        )
        
        # Handle status-specific actions
        if new_status == 'cancelled':
            OrderService.handle_order_cancellation(order)
        elif new_status == 'delivered':
            OrderService.handle_order_delivery(order)
        
        # Send notifications
        OrderService.notify_status_change(order, old_status, new_status)
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order, reason='', cancelled_by=None):
        """Cancel order and restore stock"""
        if not order.can_be_cancelled:
            raise ValueError("Order cannot be cancelled at this stage")
        
        # Restore product stock
        for item in order.items.all():
            from apps.products.services import ProductService
            ProductService.update_stock(
                product=item.product,
                quantity_change=item.quantity,
                change_type='return',
                reference_id=order.order_number,
                notes=f"Order {order.order_number} cancelled: {reason}",
                user=cancelled_by
            )
        
        # Update order status
        OrderService.update_order_status(
            order=order,
            new_status='cancelled',
            notes=reason,
            changed_by=cancelled_by
        )
        
        return order
    
    @staticmethod
    def handle_order_cancellation(order):
        """Handle order cancellation logic"""
        # If payment was made, initiate refund
        from apps.payments.models import Payment
        
        payments = Payment.objects.filter(
            order=order,
            payment_status='completed'
        )
        
        for payment in payments:
            # Create refund request
            from apps.payments.services import PaymentService
            PaymentService.create_refund(
                original_payment=payment,
                refund_amount=payment.gross_amount,
                refund_reason='order_cancelled',
                requested_by=order.buyer
            )
    
    @staticmethod
    def handle_order_delivery(order):
        """Handle order delivery logic"""
        # Update payment status if COD
        if order.delivery_method == 'cash_on_delivery':
            order.payment_status = 'paid'
            order.save()
        
        # Update item statuses
        order.items.update(item_status='delivered')
    
    @staticmethod
    def calculate_order_summary(items_data, discount_code=None, buyer=None):
        """Calculate order summary for checkout"""
        subtotal = Decimal('0.00')
        items_summary = []
        
        for item_data in items_data:
            product = item_data['product']
            variant = item_data.get('variant')
            quantity = item_data['quantity']
            
            # Determine price
            if variant:
                unit_price = variant.final_price
            else:
                unit_price = product.price
            
            item_total = quantity * unit_price
            subtotal += item_total
            
            items_summary.append({
                'product_id': str(product.id),
                'product_name': product.name,
                'variant_id': str(variant.id) if variant else None,
                'variant_name': variant.name if variant else None,
                'quantity': quantity,
                'unit_price': unit_price,
                'total_price': item_total,
            })
        
        # Apply discount
        discount_amount = Decimal('0.00')
        if discount_code:
            discount_amount = OrderService.calculate_discount(
                subtotal, discount_code, buyer
            )
        
        # Calculate other costs
        tax_amount = OrderService.calculate_tax(subtotal - discount_amount)
        shipping_cost = Decimal('5000.00')  # Default shipping
        
        total_amount = subtotal + tax_amount + shipping_cost - discount_amount
        
        return {
            'items': items_summary,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'tax_amount': tax_amount,
            'shipping_cost': shipping_cost,
            'total_amount': total_amount,
            'currency': 'TZS'
        }
    
    @staticmethod
    def calculate_discount(subtotal, discount_code, buyer=None):
        """Calculate discount amount"""
        # Simple discount logic - in production, integrate with coupon system
        discount_codes = {
            'WELCOME10': Decimal('0.10'),  # 10% discount
            'FARMER5': Decimal('0.05'),    # 5% discount for farmers
            'BULK20': Decimal('0.20'),     # 20% discount for bulk orders
        }
        
        if discount_code in discount_codes:
            discount_rate = discount_codes[discount_code]
            
            # Apply user-specific rules
            if discount_code == 'FARMER5' and buyer and buyer.user_type != 'farmer':
                return Decimal('0.00')
            
            if discount_code == 'BULK20' and subtotal < Decimal('100000.00'):
                return Decimal('0.00')
            
            discount_amount = subtotal * discount_rate
            # Cap discount at reasonable amount
            max_discount = Decimal('50000.00')  # TZS 50,000 max
            
            return min(discount_amount, max_discount)
        
        return Decimal('0.00')
    
    @staticmethod
    def get_order_statistics(seller=None, buyer=None, date_from=None, date_to=None):
        """Get order statistics"""
        from django.db.models import Count, Sum, Avg
        
        queryset = Order.objects.all()
        
        if seller:
            queryset = queryset.filter(seller=seller)
        if buyer:
            queryset = queryset.filter(buyer=buyer)
        if date_from:
            queryset = queryset.filter(order_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(order_date__lte=date_to)
        
        stats = queryset.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            average_order_value=Avg('total_amount'),
            pending_orders=Count('id', filter=models.Q(order_status='pending')),
            confirmed_orders=Count('id', filter=models.Q(order_status='confirmed')),
            processing_orders=Count('id', filter=models.Q(order_status='processing')),
            shipped_orders=Count('id', filter=models.Q(order_status='shipped')),
            delivered_orders=Count('id', filter=models.Q(order_status='delivered')),
            cancelled_orders=Count('id', filter=models.Q(order_status='cancelled')),
        )
        
        # Calculate completion rate
        completed = stats['delivered_orders'] or 0
        total = stats['total_orders'] or 0
        stats['completion_rate'] = (completed / total * 100) if total > 0 else 0
        
        return stats
    
    @staticmethod
    def notify_new_order(order):
        """Send notification about new order"""
        # TODO: Integrate with notification service
        print(f"New order notification: {order.order_number} to {order.seller.email}")
    
    @staticmethod
    def notify_status_change(order, old_status, new_status):
        """Send notification about status change"""
        # TODO: Integrate with notification service
        print(f"Order {order.order_number} status changed: {old_status} -> {new_status}")
    
    @staticmethod
    def get_user_order_history(user, status=None, limit=None):
        """Get user's order history"""
        if user.user_type in ['farmer', 'processor', 'retailer']:
            # Get orders where user is seller
            orders = Order.objects.filter(seller=user)
        else:
            # Get orders where user is buyer
            orders = Order.objects.filter(buyer=user)
        
        if status:
            orders = orders.filter(order_status=status)
        
        orders = orders.order_by('-order_date')
        
        if limit:
            orders = orders[:limit]
        
        return orders
    
    @staticmethod
    def check_order_permissions(order, user):
        """Check if user has permissions to view/modify order"""
        if user.is_staff:
            return True
        
        return order.buyer == user or order.seller == user
    
    @staticmethod
    def get_pending_seller_actions(seller):
        """Get orders requiring seller action"""
        return Order.objects.filter(
            seller=seller,
            order_status__in=['pending', 'confirmed']
        ).order_by('order_date')
    
    @staticmethod
    def get_buyer_active_orders(buyer):
        """Get buyer's active orders"""
        return Order.objects.filter(
            buyer=buyer,
            order_status__in=['pending', 'confirmed', 'processing', 'shipped']
        ).order_by('-order_date')