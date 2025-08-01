"""
Payments views
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import PaymentMethod, Payment, PaymentAccount
from .serializers import PaymentMethodSerializer, PaymentSerializer, PaymentAccountSerializer


class PaymentMethodListView(generics.ListAPIView):
    """List available payment methods"""
    queryset = PaymentMethod.objects.filter(is_active=True, status='active')
    serializer_class = PaymentMethodSerializer
    permission_classes = [AllowAny]


class ProcessPaymentView(APIView):
    """Process payment for order"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # TODO: Implement payment processing
        return Response({
            'message': 'Payment processing - to be implemented',
            'payment_id': 'pay_123456789'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class PaymentStatusView(APIView):
    """Get payment status"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, payment_id):
        # TODO: Implement payment status check
        return Response({
            'payment_id': payment_id,
            'status': 'pending',
            'message': 'Payment status check - to be implemented'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)


class PaymentAccountListView(generics.ListAPIView):
    """List user's payment accounts"""
    serializer_class = PaymentAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return PaymentAccount.objects.filter(user=self.request.user, status='active')


class PaymentAccountCreateView(generics.CreateAPIView):
    """Create new payment account"""
    serializer_class = PaymentAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PaymentWebhookView(APIView):
    """Handle payment gateway webhooks"""
    permission_classes = [AllowAny]
    
    def post(self, request, provider):
        # TODO: Implement webhook handling for different providers
        return Response({
            'message': f'Webhook received for {provider}',
            'status': 'processed'
        }, status=status.HTTP_200_OK)