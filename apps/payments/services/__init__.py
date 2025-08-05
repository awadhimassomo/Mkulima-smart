"""
Payment services - Business logic layer
"""
import uuid
from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from ..models import Payment, PaymentMethod, PaymentRefund
from .taka_bank import TakaBankService


class PaymentService:
    """Main payment service orchestrator"""
    
    @staticmethod
    @transaction.atomic
    def create_payment(order, payment_method, payer, payment_account=None):
        """Create a new payment record"""
        
        # Generate payment reference
        reference_number = PaymentService.generate_payment_reference()
        
        # Calculate fees
        fee_amount = payment_method.calculate_fee(order.total_amount)
        net_amount = order.total_amount - fee_amount
        
        # Create payment record
        payment = Payment.objects.create(
            reference_number=reference_number,
            payment_type='order_payment',
            payment_status='pending',
            payer=payer,
            payee=order.seller,
            payment_method=payment_method,
            order=order,
            gross_amount=order.total_amount,
            fee_amount=fee_amount,
            net_amount=net_amount,
            currency=order.currency,
            description=f'Payment for Order {order.order_number}',
            expires_at=timezone.now() + timezone.timedelta(minutes=30)
        )
        
        return payment
    
    @staticmethod
    def process_payment(payment):
        """Process payment through appropriate gateway"""
        
        payment_method = payment.payment_method
        
        if payment_method.provider.lower() == 'taka bank':
            return TakaBankService.initiate_payment(payment)
        elif payment_method.method_type == 'mobile_money':
            return PaymentService.process_mobile_money(payment)
        elif payment_method.method_type == 'bank_transfer':
            return PaymentService.process_bank_transfer(payment)
        else:
            return {
                'success': False,
                'error': 'Payment method not supported',
                'code': 'UNSUPPORTED_METHOD'
            }
    
    @staticmethod
    def process_mobile_money(payment):
        """Process mobile money payment (M-Pesa, Tigo Pesa, etc.)"""
        
        # For MVP, we'll simulate mobile money processing
        # In production, integrate with actual mobile money APIs
        
        payment.payment_status = 'processing'
        payment.gateway_transaction_id = f'mm_{uuid.uuid4().hex[:12]}'
        payment.save()
        
        # Simulate processing time and return payment URL/instructions
        return {
            'success': True,
            'payment_instructions': {
                'method': 'USSD',
                'code': '*150*00#',
                'reference': payment.reference_number,
                'amount': str(payment.gross_amount),
                'merchant': 'Kikapu Platform',
                'instructions': [
                    f'Dial *150*00# from your {payment.payment_method.provider} line',
                    'Select option 4 (Pay Bill)',
                    f'Enter business number: 400200',
                    f'Enter reference: {payment.reference_number}',
                    f'Enter amount: {payment.gross_amount}',
                    'Enter your PIN to confirm'
                ]
            },
            'expires_in_minutes': 30
        }
    
    @staticmethod
    def process_bank_transfer(payment):
        """Process bank transfer payment"""
        
        payment.payment_status = 'processing'
        payment.gateway_transaction_id = f'bt_{uuid.uuid4().hex[:12]}'
        payment.save()
        
        return {
            'success': True,
            'payment_instructions': {
                'method': 'Bank Transfer',
                'bank_details': {
                    'bank_name': 'CRDB Bank',
                    'account_name': 'Kikapu Platform Ltd',
                    'account_number': '0150-12345678-00',
                    'swift_code': 'CORUTZTZ',
                    'reference': payment.reference_number,
                    'amount': str(payment.gross_amount),
                },
                'instructions': [
                    'Transfer the exact amount to the account above',
                    f'Use reference: {payment.reference_number}',
                    'Payment will be verified within 2-4 hours',
                    'Keep your transfer receipt for records'
                ]
            },
            'verification_time': '2-4 hours'
        }
    
    @staticmethod
    def check_payment_status(payment):
        """Check payment status across all gateways"""
        
        if payment.payment_method.provider.lower() == 'taka bank':
            return TakaBankService.check_payment_status(payment)
        else:
            # For other methods, return current status
            return {
                'success': True,
                'status': payment.payment_status,
                'gateway_status': payment.payment_status,
            }
    
    @staticmethod
    @transaction.atomic
    def create_refund(original_payment, refund_amount, refund_reason, requested_by):
        """Create a refund request"""
        
        if not original_payment.can_be_refunded:
            raise ValueError("Payment cannot be refunded")
        
        if refund_amount > original_payment.gross_amount:
            raise ValueError("Refund amount cannot exceed original payment")
        
        # Generate refund number
        refund_number = PaymentService.generate_refund_reference()
        
        # Calculate refund fee (if applicable)
        refund_fee = Decimal('0.00')
        if refund_amount > Decimal('10000.00'):  # Fee for large refunds
            refund_fee = refund_amount * Decimal('0.02')  # 2% fee
        
        net_refund = refund_amount - refund_fee
        
        refund = PaymentRefund.objects.create(
            original_payment=original_payment,
            refund_number=refund_number,
            refund_reason=refund_reason,
            refund_status='requested',
            refund_amount=refund_amount,
            refund_fee=refund_fee,
            net_refund=net_refund,
            currency=original_payment.currency,
            requested_by=requested_by
        )
        
        return refund
    
    @staticmethod
    def process_refund(refund):
        """Process refund through appropriate gateway"""
        
        original_payment = refund.original_payment
        payment_method = original_payment.payment_method
        
        if payment_method.provider.lower() == 'taka bank':
            return TakaBankService.initiate_refund(refund)
        else:
            # For other methods, mark as approved for manual processing
            refund.refund_status = 'approved'
            refund.approved_at = timezone.now()
            refund.save()
            
            return {
                'success': True,
                'message': 'Refund approved for manual processing',
                'processing_time': '3-5 business days'
            }
    
    @staticmethod
    def handle_webhook(provider, webhook_data, signature):
        """Handle webhook from payment providers"""
        
        if provider.lower() == 'taka-bank':
            return TakaBankService.handle_webhook(webhook_data, signature)
        else:
            return {
                'success': False,
                'error': 'Unsupported webhook provider'
            }
    
    @staticmethod
    def generate_payment_reference():
        """Generate unique payment reference"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M')
        random_part = str(uuid.uuid4()).replace('-', '')[:6].upper()
        return f"PAY-{timestamp}-{random_part}"
    
    @staticmethod
    def generate_refund_reference():
        """Generate unique refund reference"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M')
        random_part = str(uuid.uuid4()).replace('-', '')[:6].upper()
        return f"REF-{timestamp}-{random_part}"
    
    @staticmethod
    def get_payment_statistics(user=None, date_from=None, date_to=None):
        """Get payment statistics"""
        from django.db.models import Count, Sum, Avg
        
        payments = Payment.objects.all()
        
        if user:
            payments = payments.filter(payer=user)
        if date_from:
            payments = payments.filter(initiated_at__gte=date_from)
        if date_to:
            payments = payments.filter(initiated_at__lte=date_to)
        
        stats = payments.aggregate(
            total_payments=Count('id'),
            total_amount=Sum('gross_amount'),
            total_fees=Sum('fee_amount'),
            average_amount=Avg('gross_amount'),
            successful_payments=Count('id', filter=models.Q(payment_status='completed')),
            failed_payments=Count('id', filter=models.Q(payment_status='failed')),
            pending_payments=Count('id', filter=models.Q(payment_status='pending')),
        )
        
        # Calculate success rate
        total = stats['total_payments'] or 0
        successful = stats['successful_payments'] or 0
        stats['success_rate'] = (successful / total * 100) if total > 0 else 0
        
        return stats
    
    @staticmethod
    def get_user_payment_history(user, limit=20):
        """Get user's payment history"""
        
        payments = Payment.objects.filter(
            payer=user
        ).select_related(
            'payment_method', 'order'
        ).order_by('-initiated_at')[:limit]
        
        return payments
    
    @staticmethod
    def validate_payment_account(user, payment_method, account_data):
        """Validate payment account details"""
        
        # Basic validation based on payment method type
        if payment_method.method_type == 'mobile_money':
            phone = account_data.get('phone_number')
            if not phone or len(phone) < 10:
                return False, "Invalid phone number"
        
        elif payment_method.method_type == 'bank_transfer':
            account_number = account_data.get('account_number')
            if not account_number or len(account_number) < 8:
                return False, "Invalid account number"
        
        return True, "Valid"