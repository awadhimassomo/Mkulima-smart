"""
Authentication serializers
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, UserVerification


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT token serializer"""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user information to token response
        data.update({
            'user': {
                'id': str(self.user.id),
                'email': self.user.email,
                'full_name': self.user.full_name,
                'user_type': self.user.user_type,
                'account_status': self.user.account_status,
                'is_verified': self.user.is_verified,
                'avatar': self.user.avatar.url if self.user.avatar else None,
            }
        })
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """User registration serializer"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'phone_number', 'user_type',
            'full_name', 'password', 'password_confirm'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'phone_number': {'required': True},
            'user_type': {'required': True},
        }
    
    def validate(self, attrs):
        """Custom validation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already registered")
        
        # Check if phone number already exists
        if User.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError("Phone number already registered")
        
        return attrs
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create user profile
        UserProfile.objects.create(user=user)
        
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """User profile serializer"""
    
    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth', 'gender', 'address_line_1', 'address_line_2',
            'city', 'state_region', 'postal_code', 'country',
            'latitude', 'longitude', 'farm_size_acres', 'primary_crops',
            'farming_experience_years', 'tax_id', 'business_license',
            'website', 'bank_name', 'bank_account_number', 'mobile_money_number'
        ]


class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile"""
    
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'phone_number', 'user_type',
            'account_status', 'full_name', 'avatar', 'location', 'bio',
            'business_name', 'business_registration', 'email_verified',
            'phone_verified', 'identity_verified', 'language', 'currency',
            'email_notifications', 'sms_notifications', 'push_notifications',
            'date_joined', 'profile'
        ]
        read_only_fields = [
            'id', 'email_verified', 'phone_verified', 'identity_verified',
            'date_joined', 'account_status'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    """User update serializer"""
    
    class Meta:
        model = User
        fields = [
            'full_name', 'avatar', 'location', 'bio', 'business_name',
            'business_registration', 'language', 'currency',
            'email_notifications', 'sms_notifications', 'push_notifications'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """Password change serializer"""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password change"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        
        return attrs
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Invalid old password")
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """Email verification serializer"""
    
    verification_token = serializers.CharField(required=True)
    
    def validate_verification_token(self, value):
        """Validate verification token"""
        try:
            verification = UserVerification.objects.get(
                verification_token=value,
                verification_type='email',
                status='pending'
            )
            if verification.is_expired:
                raise serializers.ValidationError("Verification token has expired")
            
            self.context['verification'] = verification
            return value
        except UserVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token")


class PhoneVerificationSerializer(serializers.Serializer):
    """Phone verification serializer"""
    
    verification_code = serializers.CharField(required=True, max_length=6)
    
    def validate_verification_code(self, value):
        """Validate verification code"""
        phone_number = self.context['request'].user.phone_number
        
        try:
            verification = UserVerification.objects.get(
                user__phone_number=phone_number,
                verification_code=value,
                verification_type='phone',
                status='pending'
            )
            if verification.is_expired:
                raise serializers.ValidationError("Verification code has expired")
            
            self.context['verification'] = verification
            return value
        except UserVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid verification code")


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer"""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate email exists"""
        try:
            user = User.objects.get(email=value, is_active=True)
            self.context['user'] = user
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email")


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""
    
    verification_token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate password reset"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        return attrs
    
    def validate_verification_token(self, value):
        """Validate verification token"""
        try:
            verification = UserVerification.objects.get(
                verification_token=value,
                verification_type='password_reset',
                status='pending'
            )
            if verification.is_expired:
                raise serializers.ValidationError("Reset token has expired")
            
            self.context['verification'] = verification
            return value
        except UserVerification.DoesNotExist:
            raise serializers.ValidationError("Invalid reset token")