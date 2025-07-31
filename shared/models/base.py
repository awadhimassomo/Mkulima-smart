"""
Base models for Kikapu Platform
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class UUIDModel(models.Model):
    """Abstract model with UUID primary key"""
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract model with created and updated timestamps"""
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class SoftDeleteModel(models.Model):
    """Abstract model with soft delete functionality"""
    
    is_deleted = models.BooleanField(_('is deleted'), default=False)
    deleted_at = models.DateTimeField(_('deleted at'), blank=True, null=True)
    
    class Meta:
        abstract = True


class AuditModel(models.Model):
    """Abstract model with audit trail fields"""
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name=_('created by')
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('updated by')
    )
    
    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel, SoftDeleteModel, AuditModel):
    """
    Base model combining all common functionality:
    - UUID primary key
    - Timestamps (created_at, updated_at)
    - Soft delete (is_deleted, deleted_at)
    - Audit trail (created_by, updated_by)
    """
    
    class Meta:
        abstract = True


class StatusModel(models.Model):
    """Abstract model for entities with status"""
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        PENDING = 'pending', _('Pending')
        SUSPENDED = 'suspended', _('Suspended')
    
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    class Meta:
        abstract = True


class AddressModel(models.Model):
    """Abstract model for address information"""
    
    address_line_1 = models.CharField(_('address line 1'), max_length=255, blank=True)
    address_line_2 = models.CharField(_('address line 2'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=100, blank=True)
    state_region = models.CharField(_('state/region'), max_length=100, blank=True)
    postal_code = models.CharField(_('postal code'), max_length=20, blank=True)
    country = models.CharField(_('country'), max_length=100, default='Tanzania')
    
    # Geographic coordinates
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=10,
        decimal_places=7,
        blank=True,
        null=True
    )
    
    class Meta:
        abstract = True
    
    @property
    def full_address(self):
        """Return formatted full address"""
        parts = [
            self.address_line_1,
            self.address_line_2,
            self.city,
            self.state_region,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, parts))


class ContactModel(models.Model):
    """Abstract model for contact information"""
    
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    email = models.EmailField(_('email'), blank=True)
    website = models.URLField(_('website'), blank=True)
    
    class Meta:
        abstract = True


class MetadataModel(models.Model):
    """Abstract model for storing metadata as JSON"""
    
    metadata = models.JSONField(
        _('metadata'),
        default=dict,
        blank=True,
        help_text=_('Additional metadata stored as JSON')
    )
    
    class Meta:
        abstract = True


class PriceModel(models.Model):
    """Abstract model for pricing information"""
    
    class Currency(models.TextChoices):
        TZS = 'TZS', _('Tanzanian Shilling')
        USD = 'USD', _('US Dollar')
        EUR = 'EUR', _('Euro')
    
    price = models.DecimalField(
        _('price'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Price in the specified currency')
    )
    currency = models.CharField(
        _('currency'),
        max_length=3,
        choices=Currency.choices,
        default=Currency.TZS
    )
    
    class Meta:
        abstract = True
    
    @property
    def formatted_price(self):
        """Return formatted price with currency"""
        return f"{self.price} {self.currency}"


class RatingModel(models.Model):
    """Abstract model for rating functionality"""
    
    rating = models.DecimalField(
        _('average rating'),
        max_digits=3,
        decimal_places=2,
        default=0.00,
        help_text=_('Average rating from 0.00 to 5.00')
    )
    rating_count = models.PositiveIntegerField(
        _('rating count'),
        default=0,
        help_text=_('Total number of ratings')
    )
    
    class Meta:
        abstract = True
    
    @property
    def rating_display(self):
        """Return formatted rating display"""
        if self.rating_count == 0:
            return "No ratings"
        return f"{self.rating:.1f} ({self.rating_count} ratings)"


class SEOModel(models.Model):
    """Abstract model for SEO fields"""
    
    slug = models.SlugField(
        _('slug'),
        max_length=255,
        blank=True,
        help_text=_('URL-friendly version of the name')
    )
    meta_title = models.CharField(
        _('meta title'),
        max_length=60,
        blank=True,
        help_text=_('SEO meta title (max 60 characters)')
    )
    meta_description = models.CharField(
        _('meta description'),
        max_length=160,
        blank=True,
        help_text=_('SEO meta description (max 160 characters)')
    )
    
    class Meta:
        abstract = True