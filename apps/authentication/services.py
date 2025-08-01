"""
Authentication services - Business logic layer
"""
import secrets
import uuid
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model
from .models import UserVerification

User = get_user_model()


class AuthenticationService:
    """Service class for authentication business logic"""
    
    @staticmethod
    def send_email_verification(user):
        """Send email verification to user"""
        # Generate verification token
        token = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(hours=24)
        
        # Create or update verification record
        verification, created = UserVerification.objects.get_or_create(
            user=user,
            verification_type='email',
            status='pending',
            defaults={
                'verification_token': token,
                'expires_at': expires_at,
            }
        )
        
        if not created:
            verification.verification_token = token
            verification.expires_at = expires_at
            verification.attempts = 0
            verification.save()
        
        # Send email (in production, use proper email template)
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{token}"
        
        subject = 'Verify Your Kikapu Account'
        message = f"""
        Hello {user.display_name},
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        This link expires in 24 hours.
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        Kikapu Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return verification
    
    @staticmethod
    def send_phone_verification(user):
        """Send SMS verification code to user"""
        # Generate 6-digit code
        code = str(secrets.randbelow(999999)).zfill(6)
        expires_at = timezone.now() + timedelta(minutes=10)
        
        # Create or update verification record
        verification, created = UserVerification.objects.get_or_create(
            user=user,
            verification_type='phone',
            status='pending',
            defaults={
                'verification_code': code,
                'verification_token': str(uuid.uuid4()),
                'expires_at': expires_at,
            }
        )
        
        if not created:
            verification.verification_code = code
            verification.expires_at = expires_at
            verification.attempts = 0
            verification.save()
        
        # TODO: Integrate with SMS provider (e.g., Twilio, Africa's Talking)
        # For now, we'll log the code (in production, send actual SMS)
        print(f"SMS Verification Code for {user.phone_number}: {code}")
        
        return verification
    
    @staticmethod
    def send_password_reset(user):
        """Send password reset email to user"""
        # Generate reset token
        token = str(uuid.uuid4())
        expires_at = timezone.now() + timedelta(hours=2)
        
        # Create verification record
        verification = UserVerification.objects.create(
            user=user,
            verification_type='password_reset',
            verification_token=token,
            expires_at=expires_at,
            status='pending'
        )
        
        # Send email
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{token}"
        
        subject = 'Reset Your Kikapu Password'
        message = f"""
        Hello {user.display_name},
        
        You requested to reset your password. Click the link below to create a new password:
        {reset_url}
        
        This link expires in 2 hours.
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        Kikapu Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return verification
    
    @staticmethod
    def verify_user_credentials(email, password):
        """Verify user credentials for login"""
        try:
            user = User.objects.get(email=email, is_active=True)
            if user.check_password(password):
                return user
            return None
        except User.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_stats(user):
        """Get user statistics"""
        if user.user_type == 'farmer':
            from apps.products.models import Product
            from apps.orders.models import Order
            
            stats = {
                'total_products': Product.objects.filter(seller=user).count(),
                'active_products': Product.objects.filter(
                    seller=user, 
                    status='active',
                    is_available=True
                ).count(),
                'total_sales': Order.objects.filter(
                    seller=user,
                    order_status='delivered'
                ).count(),
                'pending_orders': Order.objects.filter(
                    seller=user,
                    order_status__in=['pending', 'confirmed', 'processing']
                ).count(),
            }
        elif user.user_type == 'buyer':
            from apps.orders.models import Order
            
            stats = {
                'total_orders': Order.objects.filter(buyer=user).count(),
                'completed_orders': Order.objects.filter(
                    buyer=user,
                    order_status='delivered'
                ).count(),
                'pending_orders': Order.objects.filter(
                    buyer=user,
                    order_status__in=['pending', 'confirmed', 'processing', 'shipped']
                ).count(),
                'cancelled_orders': Order.objects.filter(
                    buyer=user,
                    order_status='cancelled'
                ).count(),
            }
        else:
            stats = {
                'account_age_days': (timezone.now() - user.date_joined).days,
                'last_login_days_ago': (
                    timezone.now() - user.last_login
                ).days if user.last_login else None,
            }
        
        return stats
    
    @staticmethod
    def update_user_session(user, request):
        """Update user session information"""
        from .models import UserSession
        
        # Get or create session
        session_key = request.session.session_key
        if session_key:
            session, created = UserSession.objects.get_or_create(
                user=user,
                session_key=session_key,
                defaults={
                    'ip_address': AuthenticationService.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'expires_at': timezone.now() + timedelta(days=30),
                }
            )
            
            if not created:
                session.ip_address = AuthenticationService.get_client_ip(request)
                session.user_agent = request.META.get('HTTP_USER_AGENT', '')
                session.save()
        
        # Update user's last login IP
        user.last_login_ip = AuthenticationService.get_client_ip(request)
        user.save(update_fields=['last_login_ip'])
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @staticmethod
    def cleanup_expired_verifications():
        """Clean up expired verification records"""
        expired_verifications = UserVerification.objects.filter(
            expires_at__lt=timezone.now(),
            status='pending'
        )
        
        count = expired_verifications.update(status='expired')
        return count
    
    @staticmethod
    def get_verification_statistics():
        """Get verification statistics"""
        from django.db.models import Count
        
        stats = UserVerification.objects.values('verification_type', 'status').annotate(
            count=Count('id')
        )
        
        return {
            'total_verifications': UserVerification.objects.count(),
            'by_type_and_status': list(stats)
        }