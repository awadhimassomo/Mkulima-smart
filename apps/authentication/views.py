"""
Authentication views
"""
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import UserVerification
from .serializers import (
    CustomTokenObtainPairSerializer, UserRegistrationSerializer,
    UserSerializer, UserUpdateSerializer, PasswordChangeSerializer,
    EmailVerificationSerializer, PhoneVerificationSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from .services import AuthenticationService

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view"""
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send verification email
        AuthenticationService.send_email_verification(user)
        
        return Response({
            'message': 'Registration successful. Please check your email for verification.',
            'user_id': str(user.id),
            'email': user.email
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """User logout endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(generics.RetrieveUpdateAPIView):
    """User profile endpoint"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserSerializer


class ChangePasswordView(APIView):
    """Change password endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)


class EmailVerificationView(APIView):
    """Email verification endpoint"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verification = serializer.context['verification']
        user = verification.user
        
        # Mark email as verified
        user.email_verified = True
        user.email_verified_at = timezone.now()
        if user.account_status == 'pending':
            user.account_status = 'active'
        user.save()
        
        # Mark verification as completed
        verification.status = 'completed'
        verification.verified_at = timezone.now()
        verification.save()
        
        return Response({
            'message': 'Email verified successfully'
        }, status=status.HTTP_200_OK)


class ResendEmailVerificationView(APIView):
    """Resend email verification"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.email_verified:
            return Response({
                'message': 'Email already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        AuthenticationService.send_email_verification(user)
        
        return Response({
            'message': 'Verification email sent'
        }, status=status.HTTP_200_OK)


class PhoneVerificationView(APIView):
    """Phone verification endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PhoneVerificationSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        verification = serializer.context['verification']
        user = verification.user
        
        # Mark phone as verified
        user.phone_verified = True
        user.phone_verified_at = timezone.now()
        user.save()
        
        # Mark verification as completed
        verification.status = 'completed'
        verification.verified_at = timezone.now()
        verification.save()
        
        return Response({
            'message': 'Phone verified successfully'
        }, status=status.HTTP_200_OK)


class SendPhoneVerificationView(APIView):
    """Send phone verification code"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.phone_verified:
            return Response({
                'message': 'Phone already verified'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        AuthenticationService.send_phone_verification(user)
        
        return Response({
            'message': 'Verification code sent to your phone'
        }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Request password reset"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.context['user']
        AuthenticationService.send_password_reset(user)
        
        return Response({
            'message': 'Password reset instructions sent to your email'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """Confirm password reset"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        verification = serializer.context['verification']
        user = verification.user
        
        # Reset password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Mark verification as completed
        verification.status = 'completed'
        verification.verified_at = timezone.now()
        verification.save()
        
        return Response({
            'message': 'Password reset successfully'
        }, status=status.HTTP_200_OK)