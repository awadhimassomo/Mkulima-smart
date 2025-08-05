"""
Taka Bank Payment Integration Service
"""
import requests
import hashlib
import hmac
import json
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from ..models import Payment, PaymentStatusHistory


class TakaBankService:
    """Service for Taka Bank payment processing"""
    
    # Taka Bank API endpoints (sandbox/production)
    BASE_URL = getattr(settings, 'TAKA_BANK_BASE_URL', 'https://sandbox-api.takabank.co.tz')
    API_KEY = getattr(settings, 'TAKA_BANK_API_KEY', '')
    SECRET_KEY = getattr(settings, 'TAKA_BANK_SECRET', '')
    MERCHANT_ID = getattr(settings, 'TAKA_BANK_MERCHANT_ID', '')
    
    @staticmethod
    def generate_signature(data, secret_key):
        """Generate HMAC signature for request authentication"""
        message = json.dumps(data, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    @staticmethod
    def initiate_payment(payment):
        """Initiate payment with Taka Bank"""
        
        # Prepare payment data
        payment_data = {
            'merchant_id': TakaBankService.MERCHANT_ID,
            'reference': payment.reference_number,
            'amount': str(payment.gross_amount),
            'currency': payment.currency,
            'description': payment.description or f'Payment for Order {payment.order.order_number}',
            'customer': {
                'name': payment.payer.display_name,
                'email': payment.payer.email,
                'phone': payment.payer.phone_number,
            },
            'callback_url': f"{settings.SITE_URL}/api/v1/payments/webhooks/taka-bank/",
            'return_url': f"{settings.FRONTEND_URL}/payment/success/",
            'cancel_url': f"{settings.FRONTEND_URL}/payment/cancelled/",
            'timestamp': timezone.now().isoformat(),
        }
        
        # Generate signature
        signature = TakaBankService.generate_signature(payment_data, TakaBankService.SECRET_KEY)
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {TakaBankService.API_KEY}',
            'X-Signature': signature,
        }
        
        try:
            response = requests.post(
                f'{TakaBankService.BASE_URL}/payments/initiate',
                json=payment_data,
                headers=headers,
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                # Update payment with gateway transaction ID
                payment.gateway_transaction_id = response_data.get('transaction_id')
                payment.gateway_response = response_data
                payment.payment_status = 'processing'
                payment.save()
                
                # Log status change
                PaymentStatusHistory.objects.create(
                    payment=payment,
                    from_status='pending',
                    to_status='processing',
                    notes='Payment initiated with Taka Bank',
                    gateway_response=response_data
                )
                
                return {
                    'success': True,
                    'payment_url': response_data.get('payment_url'),
                    'transaction_id': response_data.get('transaction_id'),
                    'expires_at': response_data.get('expires_at'),
                }
            else:
                # Payment initiation failed
                payment.payment_status = 'failed'
                payment.gateway_response = response_data
                payment.save()
                
                PaymentStatusHistory.objects.create(
                    payment=payment,
                    from_status='pending',
                    to_status='failed',
                    notes=f'Payment initiation failed: {response_data.get("message", "Unknown error")}',
                    gateway_response=response_data
                )
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Payment initiation failed'),
                    'code': response_data.get('error_code')
                }
                
        except requests.RequestException as e:
            # Network or request error
            payment.payment_status = 'failed'
            payment.save()
            
            PaymentStatusHistory.objects.create(
                payment=payment,
                from_status='pending',
                to_status='failed',
                notes=f'Network error: {str(e)}'
            )
            
            return {
                'success': False,
                'error': 'Payment service temporarily unavailable',
                'code': 'NETWORK_ERROR'
            }
    
    @staticmethod
    def check_payment_status(payment):
        """Check payment status with Taka Bank"""
        
        if not payment.gateway_transaction_id:
            return {
                'success': False,
                'error': 'No gateway transaction ID available'
            }
        
        headers = {
            'Authorization': f'Bearer {TakaBankService.API_KEY}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.get(
                f'{TakaBankService.BASE_URL}/payments/{payment.gateway_transaction_id}/status',
                headers=headers,
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200:
                gateway_status = response_data.get('status')
                old_status = payment.payment_status
                
                # Map Taka Bank status to our payment status
                status_mapping = {
                    'pending': 'pending',
                    'processing': 'processing',
                    'completed': 'completed',
                    'failed': 'failed',
                    'cancelled': 'cancelled',
                    'expired': 'failed',
                }
                
                new_status = status_mapping.get(gateway_status, 'pending')
                
                if new_status != old_status:
                    payment.payment_status = new_status
                    payment.gateway_response = response_data
                    
                    if new_status == 'completed':
                        payment.processed_at = timezone.now()
                        payment.is_verified = True
                    
                    payment.save()
                    
                    # Log status change
                    PaymentStatusHistory.objects.create(
                        payment=payment,
                        from_status=old_status,
                        to_status=new_status,
                        notes=f'Status updated from Taka Bank: {gateway_status}',
                        gateway_response=response_data
                    )
                
                return {
                    'success': True,
                    'status': new_status,
                    'gateway_status': gateway_status,
                    'amount': response_data.get('amount'),
                    'transaction_fee': response_data.get('transaction_fee', 0),
                }
            else:
                return {
                    'success': False,
                    'error': response_data.get('message', 'Status check failed')
                }
                
        except requests.RequestException as e:
            return {
                'success': False,
                'error': 'Unable to check payment status',
                'code': 'NETWORK_ERROR'
            }
    
    @staticmethod
    def handle_webhook(webhook_data, signature):
        """Handle Taka Bank webhook notification"""
        
        # Verify webhook signature
        expected_signature = TakaBankService.generate_signature(
            webhook_data, 
            TakaBankService.SECRET_KEY
        )
        
        if not hmac.compare_digest(signature, expected_signature):
            return {
                'success': False,
                'error': 'Invalid webhook signature'
            }
        
        try:
            transaction_id = webhook_data.get('transaction_id')
            status = webhook_data.get('status')
            
            # Find payment by gateway transaction ID
            payment = Payment.objects.get(gateway_transaction_id=transaction_id)
            old_status = payment.payment_status
            
            # Map status
            status_mapping = {
                'completed': 'completed',
                'failed': 'failed',
                'cancelled': 'cancelled',
                'expired': 'failed',
            }
            
            new_status = status_mapping.get(status, payment.payment_status)
            
            if new_status != old_status:
                payment.payment_status = new_status
                payment.gateway_response = webhook_data
                
                if new_status == 'completed':
                    payment.processed_at = timezone.now()
                    payment.is_verified = True
                    payment.fee_amount = Decimal(str(webhook_data.get('transaction_fee', 0)))
                    payment.net_amount = payment.gross_amount - payment.fee_amount
                
                payment.save()
                
                # Log status change
                PaymentStatusHistory.objects.create(
                    payment=payment,
                    from_status=old_status,
                    to_status=new_status,
                    notes=f'Webhook notification: {status}',
                    gateway_response=webhook_data
                )
                
                # Update order payment status if completed
                if new_status == 'completed' and payment.order:
                    payment.order.payment_status = 'paid'
                    payment.order.save()
                    
                    # Update order status to confirmed
                    from apps.orders.services import OrderService
                    if payment.order.order_status == 'pending':
                        OrderService.update_order_status(
                            order=payment.order,
                            new_status='confirmed',
                            notes='Payment confirmed',
                            changed_by=None
                        )
            
            return {
                'success': True,
                'message': 'Webhook processed successfully'
            }
            
        except Payment.DoesNotExist:
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Webhook processing error: {str(e)}'
            }
    
    @staticmethod
    def initiate_refund(refund):
        """Initiate refund with Taka Bank"""
        
        original_payment = refund.original_payment
        
        refund_data = {
            'merchant_id': TakaBankService.MERCHANT_ID,
            'original_transaction_id': original_payment.gateway_transaction_id,
            'refund_reference': refund.refund_number,
            'amount': str(refund.refund_amount),
            'currency': refund.currency,
            'reason': refund.reason_description or 'Customer refund request',
            'timestamp': timezone.now().isoformat(),
        }
        
        signature = TakaBankService.generate_signature(refund_data, TakaBankService.SECRET_KEY)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {TakaBankService.API_KEY}',
            'X-Signature': signature,
        }
        
        try:
            response = requests.post(
                f'{TakaBankService.BASE_URL}/payments/refund',
                json=refund_data,
                headers=headers,
                timeout=30
            )
            
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('status') == 'success':
                refund.gateway_refund_id = response_data.get('refund_id')
                refund.gateway_response = response_data
                refund.refund_status = 'processing'
                refund.save()
                
                return {
                    'success': True,
                    'refund_id': response_data.get('refund_id'),
                    'estimated_completion': response_data.get('estimated_completion'),
                }
            else:
                refund.refund_status = 'failed'
                refund.gateway_response = response_data
                refund.save()
                
                return {
                    'success': False,
                    'error': response_data.get('message', 'Refund initiation failed')
                }
                
        except requests.RequestException as e:
            refund.refund_status = 'failed'
            refund.save()
            
            return {
                'success': False,
                'error': 'Refund service temporarily unavailable'
            }
    
    @staticmethod
    def get_supported_payment_methods():
        """Get supported payment methods from Taka Bank"""
        
        headers = {
            'Authorization': f'Bearer {TakaBankService.API_KEY}',
        }
        
        try:
            response = requests.get(
                f'{TakaBankService.BASE_URL}/payment-methods',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get('payment_methods', [])
            else:
                return []
                
        except requests.RequestException:
            return []