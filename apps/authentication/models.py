"""
Authentication models for Kikapu Platform
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from shared.models.base import TimeStampedModel
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    """Custom User model extending Django's AbstractUser"""
    
    class UserType(models.TextChoices):
        FARMER = 'farmer', _('Farmer')
        BUYER = 'buyer', _('Buyer') 
        PROCESSOR = 'processor', _('Processor')
        RETAILER = 'retailer', _('Retailer')
        LOGISTICS = 'logistics', _('Logistics Provider')
        ADMIN = 'admin', _('Administrator')
    
    class AccountStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Verification')
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        DEACTIVATED = 'deactivated', _('Deactivated')
    
    # Override email to be required and unique
    email = models.EmailField(_('email address'), unique=True)
    
    # Additional fields
    # phone_number = models.CharField(
    #     _('phone number'), 
    #     max_length=20, 
    #     unique=True,
    #     help_text=_('Phone number with country code (e.g., +255123456789)')
    # )
    phone_number = PhoneNumberField(
        _('phone number'),unique=True, 
        region='TZ',
        help_text=_('Phone number under Tanzania country code')
        )
    user_type = models.CharField(
        _('user type'),
        max_length=20,
        choices=UserType.choices,
        default=UserType.FARMER
    )
    account_status = models.CharField(
        _('account status'),
        max_length=20,
        choices=AccountStatus.choices,
        default=AccountStatus.PENDING
    )
    
    # Profile fields
    full_name = models.CharField(_('full name'), max_length=255, blank=True)
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        blank=True,
        null=True
    )
    location = models.CharField(_('location'), max_length=255, blank=True)
    bio = models.TextField(_('bio'), blank=True)
    
    # Business information
    business_name = models.CharField(_('business name'), max_length=255, blank=True)
    business_registration = models.CharField(_('business registration'), max_length=100, blank=True)
    
    # Verification fields
    email_verified = models.BooleanField(_('email verified'), default=False)
    phone_verified = models.BooleanField(_('phone verified'), default=False)
    identity_verified = models.BooleanField(_('identity verified'), default=False)
    
    # Preferences
    language = models.CharField(
        _('preferred language'),
        max_length=10,
        default='en',
        choices=[
            ('en', _('English')),
            ('sw', _('Swahili')),
            ('fr', _('French')),
        ]
    )
    currency = models.CharField(
        _('preferred currency'),
        max_length=10,
        default='TZS',
        choices=[
            ('TZS', _('Tanzanian Shilling')),
            ('USD', _('US Dollar')),
            ('EUR', _('Euro')),
        ]
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    sms_notifications = models.BooleanField(_('SMS notifications'), default=True)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    
    # Timestamps
    email_verified_at = models.DateTimeField(_('email verified at'), blank=True, null=True)
    phone_verified_at = models.DateTimeField(_('phone verified at'), blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(_('last login IP'), blank=True, null=True)
    
    # Make email the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone_number', 'user_type']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['user_type']),
            models.Index(fields=['account_status']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def display_name(self):
        """Return the best available display name"""
        return self.full_name or self.username or self.email
    
    @property
    def is_verified(self):
        """Check if user is fully verified"""
        return self.email_verified and self.phone_verified
    
    @property
    def is_business_user(self):
        """Check if user is a business user"""
        return self.user_type in [self.UserType.PROCESSOR, self.UserType.RETAILER, self.UserType.LOGISTICS]
    
    def get_full_name(self):
        """Return the full name for the user."""
        return self.full_name or super().get_full_name()


class UserProfile(TimeStampedModel):
    """Extended user profile information"""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    
    # Personal Information
    date_of_birth = models.DateField(_('date of birth'), blank=True, null=True)
    gender = models.CharField(
        _('gender'),
        max_length=1,
        choices=[
            ('m', _('Male')),
            ('f', _('Female')),
            ('o', _('Other')),
            ('p', _('Prefer not to say')),
        ],
        blank=True
    )
    
    # Address Information
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
    
    # Farming specific (for farmers)
    farm_size_acres = models.DecimalField(
        _('farm size (acres)'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    primary_crops = models.JSONField(
        _('primary crops'),
        default=list,
        blank=True,
        help_text=_('List of primary crops grown')
    )
    farming_experience_years = models.PositiveIntegerField(
        _('farming experience (years)'),
        blank=True,
        null=True
    )
    
    # Business specific
    tax_id = models.CharField(_('tax ID'), max_length=50, blank=True)
    business_license = models.CharField(_('business license'), max_length=100, blank=True)
    website = models.URLField(_('website'), blank=True)
    
    # Bank/Payment Information
    bank_name = models.CharField(_('bank name'), max_length=100, blank=True)
    bank_account_number = models.CharField(_('bank account number'), max_length=50, blank=True)
    mobile_money_number = models.CharField(_('mobile money number'), max_length=20, blank=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
    
    def __str__(self):
        return f"{self.user.email}'s Profile"


class UserSession(TimeStampedModel):
    """Track user sessions for security"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_key = models.CharField(_('session key'), max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(_('IP address'))
    user_agent = models.TextField(_('user agent'), blank=True)
    device_info = models.JSONField(_('device info'), default=dict, blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    expires_at = models.DateTimeField(_('expires at'))
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['session_key']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address}"


class UserVerification(TimeStampedModel):
    """Handle user verification processes"""
    
    class VerificationType(models.TextChoices):
        EMAIL = 'email', _('Email Verification')
        PHONE = 'phone', _('Phone Verification')
        IDENTITY = 'identity', _('Identity Verification')
        PASSWORD_RESET = 'password_reset', _('Password Reset')
    
    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        EXPIRED = 'expired', _('Expired')
        FAILED = 'failed', _('Failed')
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    verification_type = models.CharField(
        _('verification type'),
        max_length=20,
        choices=VerificationType.choices
    )
    verification_token = models.CharField(_('verification token'), max_length=100)
    verification_code = models.CharField(_('verification code'), max_length=10, blank=True)  # For SMS/email codes
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )
    expires_at = models.DateTimeField(_('expires at'))
    verified_at = models.DateTimeField(_('verified at'), blank=True, null=True)
    attempts = models.PositiveIntegerField(_('attempts'), default=0)
    max_attempts = models.PositiveIntegerField(_('max attempts'), default=3)
    
    class Meta:
        db_table = 'user_verifications'
        verbose_name = _('User Verification')
        verbose_name_plural = _('User Verifications')
        indexes = [
            models.Index(fields=['verification_token']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['user', 'verification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.verification_type}"
    
    @property
    def is_expired(self):
        """Check if verification is expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def attempts_remaining(self):
        """Get remaining attempts"""
        return max(0, self.max_attempts - self.attempts)