"""
Management command to create test data for development
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.products.models import ProductCategory, Product
from apps.payments.models import PaymentMethod
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test data for development'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data...'))
        
        # Create test users
        if not User.objects.filter(email='farmer@test.com').exists():
            farmer = User.objects.create_user(
                username='farmer1',
                email='farmer@test.com',
                password='testpass123',
                phone_number='+255123456789',
                user_type='farmer',
                full_name='John Farmer',
                account_status='active',
                email_verified=True,
                phone_verified=True
            )
            self.stdout.write(f'Created farmer: {farmer.email}')
        
        if not User.objects.filter(email='buyer@test.com').exists():
            buyer = User.objects.create_user(
                username='buyer1',
                email='buyer@test.com',
                password='testpass123',
                phone_number='+255987654321',
                user_type='buyer',
                full_name='Jane Buyer',
                account_status='active',
                email_verified=True,
                phone_verified=True
            )
            self.stdout.write(f'Created buyer: {buyer.email}')
        
        # Create product categories
        vegetables_cat, created = ProductCategory.objects.get_or_create(
            name='Vegetables',
            defaults={
                'description': 'Fresh vegetables',
                'is_agricultural': True,
                'seasonal': False,
                'perishable': True,
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(f'Created category: {vegetables_cat.name}')
        
        fruits_cat, created = ProductCategory.objects.get_or_create(
            name='Fruits',
            defaults={
                'description': 'Fresh fruits',
                'is_agricultural': True,
                'seasonal': True,
                'perishable': True,
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(f'Created category: {fruits_cat.name}')
        
        # Create test products
        farmer = User.objects.get(email='farmer@test.com')
        
        tomatoes, created = Product.objects.get_or_create(
            sku='TOM001',
            defaults={
                'name': 'Fresh Tomatoes',
                'description': 'Organic red tomatoes, freshly harvested',
                'short_description': 'Fresh organic tomatoes',
                'category': vegetables_cat,
                'product_type': 'fresh_produce',
                'seller': farmer,
                'quality_grade': 'organic',
                'origin_location': 'Arusha, Tanzania',
                'weight_kg': Decimal('1.0'),
                'unit_of_measure': 'kg',
                'stock_quantity': 100,
                'minimum_order_quantity': 1,
                'price': Decimal('3000.00'),
                'currency': 'TZS',
                'cost_price': Decimal('2000.00'),
                'status': 'active',
                'is_available': True,
                'is_featured': True
            }
        )
        if created:
            self.stdout.write(f'Created product: {tomatoes.name}')
        
        bananas, created = Product.objects.get_or_create(
            sku='BAN001',
            defaults={
                'name': 'Sweet Bananas',
                'description': 'Fresh sweet bananas from Kilimanjaro region',
                'short_description': 'Sweet ripe bananas',
                'category': fruits_cat,
                'product_type': 'fresh_produce',
                'seller': farmer,
                'quality_grade': 'grade_a',
                'origin_location': 'Moshi, Tanzania',
                'weight_kg': Decimal('0.5'),
                'unit_of_measure': 'bunch',
                'stock_quantity': 50,
                'minimum_order_quantity': 1,
                'price': Decimal('2500.00'),
                'currency': 'TZS',
                'cost_price': Decimal('1500.00'),
                'status': 'active',
                'is_available': True,
                'is_featured': False
            }
        )
        if created:
            self.stdout.write(f'Created product: {bananas.name}')
        
        # Create payment methods
        mobile_money, created = PaymentMethod.objects.get_or_create(
            name='M-Pesa',
            defaults={
                'method_type': 'mobile_money',
                'provider': 'Vodacom',
                'is_active': True,
                'is_default': True,
                'processing_fee_percentage': Decimal('1.5'),
                'processing_fee_fixed': Decimal('100.00'),
                'supported_currencies': ['TZS'],
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(f'Created payment method: {mobile_money.name}')
        
        bank_transfer, created = PaymentMethod.objects.get_or_create(
            name='Bank Transfer',
            defaults={
                'method_type': 'bank_transfer',
                'provider': 'CRDB Bank',
                'is_active': True,
                'is_default': False,
                'processing_fee_percentage': Decimal('0.5'),
                'processing_fee_fixed': Decimal('500.00'),
                'supported_currencies': ['TZS', 'USD'],
                'status': 'active'
            }
        )
        if created:
            self.stdout.write(f'Created payment method: {bank_transfer.name}')
        
        self.stdout.write(
            self.style.SUCCESS('Test data created successfully!')
        )
        self.stdout.write(
            self.style.WARNING('Test login credentials:')
        )
        self.stdout.write('Farmer: farmer@test.com / testpass123')
        self.stdout.write('Buyer: buyer@test.com / testpass123')