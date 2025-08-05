"""
Payments views
"""
import uuid
from rest_framework import generics, status, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import PaymentMethod, Payment, PaymentAccount, PaymentWebhook
from .serializers import (
    PaymentMethodSerializer, PaymentSerializer, PaymentAccountSerializer,
    PaymentCreateSerializer
)
from .services import PaymentService
from apps.orders.models import Order


class PaymentMethodListView(generics.ListAPIView):
    """List available payment methods"""
    queryset = PaymentMethod.objects.filter(is_active=True, status='active')
    serializer_class = PaymentMethodSerializer
    permission_classes = [AllowAny]


class ProcessPaymentView(APIView):
    """Process payment for order"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = PaymentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        order = serializer.context['order']
        payment_method = serializer.context['payment_method']
        payment_account = serializer.context.get('payment_account')
        
        try:
            # Create payment record
            payment = PaymentService.create_payment(
                order=order,
                payment_method=payment_method,
                payer=request.user,
                payment_account=payment_account
            )
            
            # Process payment through gateway
            result = PaymentService.process_payment(payment)
            
            if result['success']:
                response_data = {
                    'payment_id': str(payment.payment_id),
                    'reference_number': payment.reference_number,
                    'status': payment.payment_status,
                    'amount': payment.gross_amount,
                    'currency': payment.currency,
                    'expires_at': payment.expires_at,
                }
                
                # Add gateway-specific data
                if 'payment_url' in result:
                    response_data['payment_url'] = result['payment_url']
                
                if 'payment_instructions' in result:
                    response_data['payment_instructions'] = result['payment_instructions']
                
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response({
                    'error': result['error'],
                    'code': result.get('code', 'PAYMENT_FAILED')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'error': 'Payment processing failed',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusView(APIView):
    """Get payment status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(
                payment_id=payment_id,
                payer=request.user
            )
            
            # Check latest status from gateway
            result = PaymentService.check_payment_status(payment)
            
            # Refresh payment from database
            payment.refresh_from_db()
            
            serializer = PaymentSerializer(payment)
            response_data = serializer.data
            
            if result['success']:
                response_data['gateway_status'] = result.get('gateway_status')
                response_data['last_checked'] = timezone.now()
            
            return Response(response_data)
            
        except Payment.DoesNotExist:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)


class PaymentListView(generics.ListAPIView):
    """List user's payments"""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentService.get_user_payment_history(
            user=self.request.user,
            limit=int(self.request.query_params.get('limit', 20))
        )


class PaymentAccountListView(generics.ListAPIView):
    """List user's payment accounts"""
    serializer_class = PaymentAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentAccount.objects.filter(
            user=self.request.user, 
            status='active'
        ).select_related('payment_method')


class PaymentAccountCreateView(generics.CreateAPIView):
    """Create new payment account"""
    serializer_class = PaymentAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        account = serializer.save(user=self.request.user)
        
        # Validate account details
        is_valid, message = PaymentService.validate_payment_account(
            user=self.request.user,
            payment_method=account.payment_method,
            account_data=serializer.validated_data
        )
        
        if not is_valid:
            account.delete()
            raise serializers.ValidationError(message)


class PaymentWebhookView(APIView):
    """Handle payment gateway webhooks"""
    permission_classes = [AllowAny]
    
    def post(self, request, provider):
        # Get signature from headers
        signature = request.headers.get('X-Signature', '')
        
        # Log webhook for debugging
        webhook = PaymentWebhook.objects.create(
            payment_method_id=self.get_payment_method_for_provider(provider),
            webhook_id=str(uuid.uuid4()),
            event_type=request.data.get('event_type', 'unknown'),
            event_data=request.data,
            headers=dict(request.headers),
            signature=signature,
            status='received'
        )
        
        try:
            # Process webhook
            result = PaymentService.handle_webhook(
                provider=provider,
                webhook_data=request.data,
                signature=signature
            )
            
            if result['success']:
                webhook.status = 'processed'
                webhook.processed_at = timezone.now()
                webhook.save()
                
                return Response({
                    'status': 'success',
                    'message': 'Webhook processed successfully'
                })
            else:
                webhook.status = 'failed'
                webhook.error_message = result['error']
                webhook.save()
                
                return Response({
                    'status': 'error',
                    'message': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            webhook.status = 'failed'
            webhook.error_message = str(e)
            webhook.save()
            
            return Response({
                'status': 'error',
                'message': 'Webhook processing failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_payment_method_for_provider(self, provider):
        """Get payment method ID for provider"""
        try:
            method = PaymentMethod.objects.get(
                provider__icontains=provider.replace('-', ' '),
                is_active=True
            )
            return method.id
        except PaymentMethod.DoesNotExist:
            return None


class PaymentRefundView(APIView):
    """Request payment refund"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, payment_id):
        try:
            payment = Payment.objects.get(
                payment_id=payment_id,
                payer=request.user
            )
            
            refund_amount = request.data.get('refund_amount', payment.gross_amount)
            refund_reason = request.data.get('refund_reason', 'customer_request')
            reason_description = request.data.get('reason_description', '')
            
            # Create refund
            refund = PaymentService.create_refund(
                original_payment=payment,
                refund_amount=refund_amount,
                refund_reason=refund_reason,
                requested_by=request.user
            )
            
            refund.reason_description = reason_description
            refund.save()
            
            # Process refund
            result = PaymentService.process_refund(refund)
            
            return Response({
                'refund_id': refund.refund_number,
                'status': refund.refund_status,
                'amount': refund.refund_amount,
                'processing_info': result
            })
            
        except Payment.DoesNotExist:
            return Response({
                'error': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PaymentStatisticsView(APIView):
    """Get payment statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        stats = PaymentService.get_payment_statistics(
            user=request.user,
            date_from=date_from,
            date_to=date_to
        )
        
        return Response(stats)
    