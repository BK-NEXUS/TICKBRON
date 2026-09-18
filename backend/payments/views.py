"""
Views for TICKBRON payment API endpoints.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import PaymentTransaction, WebhookEvent, PaymentAuditLog
from .serializers import (
    PaymentTransactionSerializer, 
    PaymentTransactionCreateSerializer,
    WebhookEventSerializer,
    PaymentAuditLogSerializer
)
from .adapters import get_payment_adapter, PaymentAdapterError
from .webhooks import validate_webhook_request, get_webhook_processor, SignatureValidationError
import logging

logger = logging.getLogger(__name__)


class PaymentTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PaymentTransaction model.
    
    Provides CRUD operations for payment transactions with idempotency support.
    """
    queryset = PaymentTransaction.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PaymentTransactionCreateSerializer
        return PaymentTransactionSerializer
    
    def get_queryset(self):
        """Filter queryset to only show user's own payment transactions."""
        user = self.request.user
        return PaymentTransaction.objects.filter(booking__guest=user)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new payment transaction with idempotency.
        
        Uses idempotency key to prevent duplicate payment attempts.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        idempotency_key = serializer.validated_data['idempotency_key']
        
        # Check for existing transaction with same idempotency key
        try:
            existing_transaction = PaymentTransaction.objects.get(
                idempotency_key=idempotency_key
            )
            # Return existing transaction
            return Response(
                PaymentTransactionSerializer(existing_transaction).data,
                status=status.HTTP_200_OK
            )
        except PaymentTransaction.DoesNotExist:
            # Create new transaction
            transaction_data = serializer.validated_data.copy()
            transaction_data['status'] = 'pending'
            
            # Create payment transaction
            payment_transaction = PaymentTransaction.objects.create(**transaction_data)
            
            # Log audit entry
            PaymentAuditLog.log_action(
                action='payment_initiated',
                payment_transaction=payment_transaction,
                booking=payment_transaction.booking,
                old_status=None,
                new_status='pending',
                actor=request.user,
                ip_address=self._get_client_ip(request),
                details={'user_agent': request.META.get('HTTP_USER_AGENT', '')}
            )
            
            # Initiate payment with provider
            try:
                adapter = get_payment_adapter(payment_transaction.provider)
                provider_response = adapter.initiate_payment(
                    booking=payment_transaction.booking,
                    amount=payment_transaction.amount,
                    currency=payment_transaction.currency,
                    payment_method_token=payment_transaction.payment_method_token
                )
                
                # Update transaction with provider response
                payment_transaction.provider_transaction_id = provider_response.get('provider_transaction_id')
                payment_transaction.provider_response = provider_response
                payment_transaction.status = 'processing'
                payment_transaction.save()
                
                # Log audit entry
                PaymentAuditLog.log_action(
                    action='payment_initiated',
                    payment_transaction=payment_transaction,
                    booking=payment_transaction.booking,
                    old_status='pending',
                    new_status='processing',
                    actor=request.user,
                    ip_address=self._get_client_ip(request),
                    details={'provider_response': provider_response}
                )
                
                return Response(
                    PaymentTransactionSerializer(payment_transaction).data,
                    status=status.HTTP_201_CREATED
                )
                
            except PaymentAdapterError as e:
                # Handle payment adapter error
                payment_transaction.status = 'failed'
                payment_transaction.error_code = 'ADAPTER_ERROR'
                payment_transaction.error_message = str(e)
                payment_transaction.save()
                
                # Log audit entry
                PaymentAuditLog.log_action(
                    action='payment_failed',
                    payment_transaction=payment_transaction,
                    booking=payment_transaction.booking,
                    old_status='pending',
                    new_status='failed',
                    actor=request.user,
                    ip_address=self._get_client_ip(request),
                    details={'error': str(e)}
                )
                
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm a payment transaction.
        
        Initiates confirmation with the payment provider.
        """
        payment_transaction = self.get_object()
        
        if payment_transaction.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Payment cannot be confirmed in current status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            adapter = get_payment_adapter(payment_transaction.provider)
            provider_response = adapter.confirm_payment(
                provider_transaction_id=payment_transaction.provider_transaction_id
            )
            
            # Update transaction status
            old_status = payment_transaction.status
            payment_transaction.status = 'completed'
            payment_transaction.provider_response = provider_response
            payment_transaction.save()
            
            # Update booking payment status
            booking = payment_transaction.booking
            booking.payment_status = 'paid'
            booking.status = 'confirmed'
            booking.save()
            
            # Log audit entries
            PaymentAuditLog.log_action(
                action='payment_completed',
                payment_transaction=payment_transaction,
                booking=booking,
                old_status=old_status,
                new_status='completed',
                actor=request.user,
                ip_address=self._get_client_ip(request),
                details={'provider_response': provider_response}
            )
            
            PaymentAuditLog.log_action(
                action='booking_status_changed',
                booking=booking,
                old_status='pending',
                new_status='confirmed',
                actor=request.user,
                ip_address=self._get_client_ip(request),
                details={'trigger': 'payment_completed'}
            )
            
            return Response(
                PaymentTransactionSerializer(payment_transaction).data,
                status=status.HTTP_200_OK
            )
            
        except PaymentAdapterError as e:
            payment_transaction.status = 'failed'
            payment_transaction.error_code = 'CONFIRM_ERROR'
            payment_transaction.error_message = str(e)
            payment_transaction.save()
            
            PaymentAuditLog.log_action(
                action='payment_failed',
                payment_transaction=payment_transaction,
                booking=payment_transaction.booking,
                old_status=payment_transaction.status,
                new_status='failed',
                actor=request.user,
                ip_address=self._get_client_ip(request),
                details={'error': str(e)}
            )
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Refund a payment transaction.
        
        Initiates refund with the payment provider.
        """
        payment_transaction = self.get_object()
        
        if payment_transaction.status != 'completed':
            return Response(
                {'error': 'Only completed payments can be refunded'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_amount = request.data.get('amount')
        
        try:
            adapter = get_payment_adapter(payment_transaction.provider)
            provider_response = adapter.refund_payment(
                provider_transaction_id=payment_transaction.provider_transaction_id,
                amount=refund_amount
            )
            
            # Update transaction status
            old_status = payment_transaction.status
            payment_transaction.status = 'refunded' if refund_amount else 'partially_refunded'
            payment_transaction.provider_response = provider_response
            payment_transaction.save()
            
            # Update booking payment status
            booking = payment_transaction.booking
            booking.payment_status = 'refunded' if refund_amount else 'partially_refunded'
            booking.save()
            
            # Log audit entry
            PaymentAuditLog.log_action(
                action='payment_refunded',
                payment_transaction=payment_transaction,
                booking=booking,
                old_status=old_status,
                new_status=payment_transaction.status,
                actor=request.user,
                ip_address=self._get_client_ip(request),
                details={'provider_response': provider_response, 'refund_amount': refund_amount}
            )
            
            return Response(
                PaymentTransactionSerializer(payment_transaction).data,
                status=status.HTTP_200_OK
            )
            
        except PaymentAdapterError as e:
            payment_transaction.error_code = 'REFUND_ERROR'
            payment_transaction.error_message = str(e)
            payment_transaction.save()
            
            PaymentAuditLog.log_action(
                action='payment_failed',
                payment_transaction=payment_transaction,
                booking=payment_transaction.booking,
                old_status=payment_transaction.status,
                new_status='failed',
                actor=request.user,
                ip_address=self._get_client_ip(request),
                details={'error': str(e)}
            )
            
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _get_client_ip(self, request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WebhookEvent model (read-only for admin purposes).
    """
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    permission_classes = [IsAuthenticated]


class PaymentAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for PaymentAuditLog model (read-only for audit purposes).
    """
    queryset = PaymentAuditLog.objects.all()
    serializer_class = PaymentAuditLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        # Admin users can see all logs, regular users only their own
        if user.is_staff or user.is_superuser:
            return PaymentAuditLog.objects.all()
        return PaymentAuditLog.objects.filter(actor=user)


@csrf_exempt
@api_view(['POST'])
def webhook_endpoint(request, provider):
    """
    Public webhook endpoint for receiving payment provider webhooks.
    
    This endpoint accepts webhooks from payment providers (Payme, Click, Visa)
    with signature validation and replay protection.
    
    Args:
        request: HTTP request
        provider: Payment provider name (from URL)
    
    Returns:
        Response: HTTP response with status
    """
    try:
        # Validate and extract webhook data
        payload, signature = validate_webhook_request(request)
        
        # Get webhook processor for provider
        processor = get_webhook_processor(provider)
        
        # Process webhook
        webhook_event, is_new = processor.process_webhook(payload, signature)
        
        if is_new:
            return Response(
                {'status': 'success', 'message': 'Webhook processed successfully'},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'status': 'success', 'message': 'Webhook already processed'},
                status=status.HTTP_200_OK
            )
            
    except SignatureValidationError as e:
        logger.error(f"Webhook signature validation failed: {e}")
        return Response(
            {'error': 'Invalid signature', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except ValueError as e:
        logger.error(f"Webhook validation error: {e}")
        return Response(
            {'error': 'Invalid request', 'message': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return Response(
            {'error': 'Processing error', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )