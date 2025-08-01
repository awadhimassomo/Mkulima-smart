"""
Authentication URL patterns
"""
from django.urls import path
from . import views

urlpatterns = [
    # JWT Token endpoints
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Password management
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Verification endpoints
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('resend-email-verification/', views.ResendEmailVerificationView.as_view(), name='resend_email_verification'),
    path('verify-phone/', views.PhoneVerificationView.as_view(), name='verify_phone'),
    path('send-phone-verification/', views.SendPhoneVerificationView.as_view(), name='send_phone_verification'),
]