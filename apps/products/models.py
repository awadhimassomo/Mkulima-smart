"""
Product models for Kikapu Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from shared.models.base import BaseModel, StatusModel, PriceModel, RatingModel, SEOModel


class ProductCategory(BaseModel, StatusModel, SEOModel):
    """Product categories for organizing products"""
    
    name = models.CharField(_('name'), max_length=100)
    description = models.TextField(_('description'), blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('parent category')
    )
    image = models.ImageField(
        _('category image'),
        upload_to='categories/',
        blank=True,
        null=True
    )
    sort_order = models.PositiveIntegerField(_('sort order'), default=0)
    
    # Category specific fields
    is_agricultural = models.BooleanField(_('is agricultural'), default=True)
    seasonal = models.BooleanField(_('seasonal'), default=False)
    perishable = models.BooleanField(_('perishable'), default=True)
    
    class Meta:
        db_table = 'product_categories'
        verbose_name = _('Product Category')
        verbose_name_plural = _('Product Categories')
        unique_together = ['name', 'parent']
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['parent']),
            models.Index(fields=['is_agricultural']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def full_path(self):
        """Return full category path"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return " > ".join(path)
    
    @property
    def level(self):
        """Return category level (0 for root categories)"""
        level = 0
        parent = self.parent
        while parent:
            level += 1
            parent = parent.parent
        return level


class Product(BaseModel, StatusModel, PriceModel, RatingModel, SEOModel):
    """Main product model"""
    
    class ProductType(models.TextChoices):
        FRESH_PRODUCE = 'fresh_produce', _('Fresh Produce')
        PROCESSED_FOOD = 'processed_food', _('Processed Food')
        SEEDS = 'seeds', _('Seeds')
        FERTILIZER = 'fertilizer', _('Fertilizer')
        TOOLS = 'tools', _('Tools & Equipment')
        LIVESTOCK = 'livestock', _('Livestock')
        DAIRY = 'dairy', _('Dairy Products')
        GRAINS = 'grains', _('Grains & Cereals')
        SPICES = 'spices', _('Spices & Herbs')
        OTHER = 'other', _('Other')
    
    class QualityGrade(models.TextChoices):
        PREMIUM = 'premium', _('Premium')
        GRADE_A = 'grade_a', _('Grade A')
        GRADE_B = 'grade_b', _('Grade B')
        STANDARD = 'standard', _('Standard')
        ORGANIC = 'organic', _('Organic Certified')
    
    # Basic Information
    name = models.CharField(_('product name'), max_length=200)
    description = models.TextField(_('description'))
    short_description = models.CharField(_('short description'), max_length=255, blank=True)
    
    # Categorization
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name=_('category')
    )
    product_type = models.CharField(
        _('product type'),
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.FRESH_PRODUCE
    )
    
    # Seller Information
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_('seller')
    )
    
    # Product Details
    sku = models.CharField(
        _('SKU'),
        max_length=50,
        unique=True,
        help_text=_('Stock Keeping Unit - unique product identifier')
    )
    barcode = models.CharField(_('barcode'), max_length=50, blank=True)
    
    # Quality & Specifications
    quality_grade = models.CharField(
        _('quality grade'),
        max_length=20,
        choices=QualityGrade.choices,
        default=QualityGrade.STANDARD
    )
    origin_location = models.CharField(_('origin location'), max_length=255, blank=True)
    harvest_date = models.DateField(_('harvest date'), blank=True, null=True)
    expiry_date = models.DateField(_('expiry date'), blank=True, null=True)
    
    # Measurements
    weight_kg = models.DecimalField(
        _('weight (kg)'),
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True
    )
    unit_of_measure = models.CharField(
        _('unit of measure'),
        max_length=20,
        choices=[
            ('kg', _('Kilogram')),
            ('g', _('Gram')),
            ('lb', _('Pound')),
            ('piece', _('Piece')),
            ('bunch', _('Bunch')),
            ('bag', _('Bag')),
            ('crate', _('Crate')),
            ('liter', _('Liter')),
            ('ml', _('Milliliter')),
        ],
        default='kg'
    )
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(_('stock quantity'), default=0)
    minimum_order_quantity = models.PositiveIntegerField(_('minimum order quantity'), default=1)
    maximum_order_quantity = models.PositiveIntegerField(
        _('maximum order quantity'),
        blank=True,
        null=True
    )
    
    # Pricing
    cost_price = models.DecimalField(
        _('cost price'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_('Cost price (for profit calculation)')
    )
    wholesale_price = models.DecimalField(
        _('wholesale price'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    retail_price = models.DecimalField(
        _('retail price'),
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Logistics
    requires_cold_storage = models.BooleanField(_('requires cold storage'), default=False)
    fragile = models.BooleanField(_('fragile'), default=False)
    hazardous = models.BooleanField(_('hazardous'), default=False)
    
    # Additional Information
    nutritional_info = models.JSONField(
        _('nutritional information'),
        default=dict,
        blank=True
    )
    certifications = models.JSONField(
        _('certifications'),
        default=list,
        blank=True,
        help_text=_('List of certifications (organic, fair trade, etc.)')
    )
    tags = models.JSONField(
        _('tags'),
        default=list,
        blank=True,
        help_text=_('Search tags for better discoverability')
    )
    
    # Visibility & Featured
    is_featured = models.BooleanField(_('is featured'), default=False)
    is_available = models.BooleanField(_('is available'), default=True)
    published_at = models.DateTimeField(_('published at'), blank=True, null=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller']),
            models.Index(fields=['category']),
            models.Index(fields=['product_type']),
            models.Index(fields=['sku']),
            models.Index(fields=['status', 'is_available']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.seller.display_name}"
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self):
        """Check if product is low in stock (less than minimum order quantity)"""
        return self.stock_quantity <= self.minimum_order_quantity
    
    @property
    def is_expired(self):
        """Check if product is expired"""
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.expiry_date
    
    @property
    def days_to_expiry(self):
        """Get days until expiry"""
        if not self.expiry_date:
            return None
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage"""
        if not self.cost_price or self.cost_price == 0:
            return None
        return ((self.price - self.cost_price) / self.cost_price) * 100


class ProductImage(BaseModel):
    """Product images"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('product')
    )
    image = models.ImageField(
        _('image'),
        upload_to='products/',
        help_text=_('Product image')
    )
    alt_text = models.CharField(
        _('alt text'),
        max_length=255,
        blank=True,
        help_text=_('Alternative text for accessibility')
    )
    is_primary = models.BooleanField(_('is primary'), default=False)
    sort_order = models.PositiveIntegerField(_('sort order'), default=0)
    
    class Meta:
        db_table = 'product_images'
        verbose_name = _('Product Image')
        verbose_name_plural = _('Product Images')
        ordering = ['sort_order', 'created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['is_primary']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - Image {self.sort_order}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(
                product=self.product,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(BaseModel, PriceModel):
    """Product variants (size, color, packaging, etc.)"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants',
        verbose_name=_('product')
    )
    name = models.CharField(_('variant name'), max_length=100)
    sku = models.CharField(_('variant SKU'), max_length=50, unique=True)
    
    # Variant attributes
    attributes = models.JSONField(
        _('variant attributes'),
        default=dict,
        help_text=_('Key-value pairs of variant attributes (size, color, etc.)')
    )
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(_('stock quantity'), default=0)
    weight_kg = models.DecimalField(
        _('weight (kg)'),
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True
    )
    
    # Pricing override
    price_adjustment = models.DecimalField(
        _('price adjustment'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_('Price adjustment from base product price')
    )
    
    is_active = models.BooleanField(_('is active'), default=True)
    
    class Meta:
        db_table = 'product_variants'
        verbose_name = _('Product Variant')
        verbose_name_plural = _('Product Variants')
        unique_together = ['product', 'name']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['sku']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    @property
    def final_price(self):
        """Calculate final price with adjustment"""
        return self.product.price + self.price_adjustment
    
    @property
    def is_in_stock(self):
        """Check if variant is in stock"""
        return self.stock_quantity > 0


class ProductReview(BaseModel):
    """Product reviews and ratings"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('product')
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        verbose_name=_('reviewer')
    )
    
    # Review content
    rating = models.PositiveIntegerField(
        _('rating'),
        choices=[(i, i) for i in range(1, 6)],
        help_text=_('Rating from 1 to 5 stars')
    )
    title = models.CharField(_('review title'), max_length=200, blank=True)
    comment = models.TextField(_('comment'), blank=True)
    
    # Review metadata
    is_verified_purchase = models.BooleanField(_('verified purchase'), default=False)
    is_approved = models.BooleanField(_('is approved'), default=True)
    helpful_count = models.PositiveIntegerField(_('helpful count'), default=0)
    
    # Review images
    images = models.JSONField(
        _('review images'),
        default=list,
        blank=True,
        help_text=_('List of image URLs uploaded by reviewer')
    )
    
    class Meta:
        db_table = 'product_reviews'
        verbose_name = _('Product Review')
        verbose_name_plural = _('Product Reviews')
        unique_together = ['product', 'reviewer']  # One review per user per product
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['reviewer']),
            models.Index(fields=['rating']),
            models.Index(fields=['is_approved']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.rating}★ by {self.reviewer.display_name}"


class ProductInventoryLog(BaseModel):
    """Track inventory changes"""
    
    class ChangeType(models.TextChoices):
        PURCHASE = 'purchase', _('Purchase/Restock')
        SALE = 'sale', _('Sale')
        ADJUSTMENT = 'adjustment', _('Manual Adjustment')
        DAMAGE = 'damage', _('Damage/Loss')
        EXPIRY = 'expiry', _('Expiry')
        RETURN = 'return', _('Return')
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_logs',
        verbose_name=_('product')
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='inventory_logs',
        blank=True,
        null=True,
        verbose_name=_('variant')
    )
    
    change_type = models.CharField(
        _('change type'),
        max_length=20,
        choices=ChangeType.choices
    )
    quantity_change = models.IntegerField(_('quantity change'))  # Can be negative
    previous_quantity = models.PositiveIntegerField(_('previous quantity'))
    new_quantity = models.PositiveIntegerField(_('new quantity'))
    
    # Reference information
    reference_id = models.CharField(
        _('reference ID'),
        max_length=100,
        blank=True,
        help_text=_('Order ID, Purchase ID, etc.')
    )
    notes = models.TextField(_('notes'), blank=True)
    
    class Meta:
        db_table = 'product_inventory_logs'
        verbose_name = _('Product Inventory Log')
        verbose_name_plural = _('Product Inventory Logs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['variant']),
            models.Index(fields=['change_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.change_type} ({self.quantity_change:+d})"


class ProductPriceHistory(BaseModel):
    """Track product price changes"""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_history',
        verbose_name=_('product')
    )
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name='price_history',
        blank=True,
        null=True,
        verbose_name=_('variant')
    )
    
    old_price = models.DecimalField(_('old price'), max_digits=12, decimal_places=2)
    new_price = models.DecimalField(_('new price'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('currency'), max_length=3, default='TZS')
    
    # Change metadata
    change_reason = models.CharField(
        _('change reason'),
        max_length=255,
        blank=True,
        help_text=_('Reason for price change')
    )
    effective_date = models.DateTimeField(_('effective date'))
    
    class Meta:
        db_table = 'product_price_history'
        verbose_name = _('Product Price History')
        verbose_name_plural = _('Product Price History')
        ordering = ['-effective_date']
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['variant']),
            models.Index(fields=['effective_date']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.old_price} → {self.new_price} {self.currency}"
    
    @property
    def price_change_percentage(self):
        """Calculate percentage change"""
        if self.old_price == 0:
            return 0
        return ((self.new_price - self.old_price) / self.old_price) * 100