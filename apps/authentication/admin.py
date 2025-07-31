"""
Authentication admin configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserProfile, UserSession, UserVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin"""
    
    list_display = [
        'email', 'username', 'full_name', 'user_type', 
        'account_status', 'is_verified', 'date_joined'
    ]
    list_filter = [
        'user_type', 'account_status', 'email_verified', 
        'phone_verified', 'is_staff', 'is_active', 'date_joined'
    ]
    search_fields = ['email', 'username', 'full_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('email', 'full_name', 'phone_number', 'avatar', 'location', 'bio')
        }),
        (_('User Type & Status'), {
            'fields': ('user_type', 'account_status')
        }),
        (_('Business Information'), {
            'fields': ('business_name', 'business_registration')
        }),
        (_('Verification'), {
            'fields': ('email_verified', 'phone_verified', 'identity_verified',
                      'email_verified_at', 'phone_verified_at')
        }),
        (_('Preferences'), {
            'fields': ('language', 'currency', 'email_notifications', 
                      'sms_notifications', 'push_notifications')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'last_login_ip')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'phone_number', 'user_type', 'password1', 'password2'),
        }),
    )
    
    readonly_fields = ['date_joined', 'last_login', 'email_verified_at', 'phone_verified_at']
    
    def is_verified(self, obj):
        return obj.is_verified
    is_verified.boolean = True
    is_verified.short_description = 'Verified'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User profile admin"""
    
    list_display = ['user', 'city', 'country', 'farm_size_acres', 'created_at']
    list_filter = ['country', 'gender', 'created_at']
    search_fields = ['user__email', 'user__full_name', 'city', 'business_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('User'), {'fields': ('user',)}),
        (_('Personal Information'), {
            'fields': ('date_of_birth', 'gender')
        }),
        (_('Address'), {
            'fields': ('address_line_1', 'address_line_2', 'city', 'state_region', 
                      'postal_code', 'country', 'latitude', 'longitude')
        }),
        (_('Farming Information'), {
            'fields': ('farm_size_acres', 'primary_crops', 'farming_experience_years')
        }),
        (_('Business Information'), {
            'fields': ('tax_id', 'business_license', 'website')
        }),
        (_('Payment Information'), {
            'fields': ('bank_name', 'bank_account_number', 'mobile_money_number')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User session admin"""
    
    list_display = ['user', 'ip_address', 'is_active', 'expires_at', 'created_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'ip_address', 'session_key']
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(UserVerification)
class UserVerificationAdmin(admin.ModelAdmin):
    """User verification admin"""
    
    list_display = [
        'user', 'verification_type', 'status', 'attempts', 
        'expires_at', 'verified_at', 'created_at'
    ]
    list_filter = ['verification_type', 'status', 'created_at']
    search_fields = ['user__email', 'verification_token', 'verification_code']
    readonly_fields = ['created_at', 'updated_at', 'verification_token']
    
    def has_add_permission(self, request):
        return False