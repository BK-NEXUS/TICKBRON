"""
Views for TICKBRON payment API endpoints.
"""
import sys
import os
from decimal import Decimal, InvalidOperation
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, serializers, viewsets, status
from rest_framework.decorators import (
    action, api_view, authentication_classes, permission_classes, throttle_classes
)
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from bookings.models import Booking
from bookings.state_machine import BookingState, BookingStateMachine
from common.request import get_client_ip
from .models import PaymentTransaction, WebhookEvent, PaymentAuditLog
from .serializers import (
    PaymentTransactionSerializer,
    PaymentTransactionCreateSerializer,
    WebhookEventSerializer,
    PaymentAuditLogSerializer
)
from .adapters import get_payment_adapter, PaymentAdapterError
from .webhooks import (
    validate_webhook_request, get_webhook_processor, SignatureValidationError,
    WebhookNotConfiguredError, WebhookNotSupportedError
)
import logging

logger = logging.getLogger(__name__)

# Check if running in test mode
TESTING = 'pytest' in sys.modules or os.getenv('PYTEST_CURRENT_TEST')


class PaymentRateThrottle(UserRateThrottle):
    """Rate throttle for payment initiation - 20 requests per minute per user."""
    rate = '20/min'
    scope = 'payment'

    def allow_request(self, request, view):
        # Disable throttling during tests
        if TESTING:
            return True
        return super().allow_request(request, view)


class PaymentTransactionViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    ViewSet for PaymentTransaction model.

    Create, list and retrieve with idempotency support, plus the confirm and
    refund actions. Transactions are never updated or deleted through the API,
    so the payment audit trail stays intact (PUT/PATCH/DELETE return 405).
    """
    queryset = PaymentTransaction.objects.all()
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentRateThrottle]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return PaymentTransactionCreateSerializer
        return PaymentTransactionSerializer
    
    def get_queryset(self):
        """Filter queryset to only show user's own payment transactions."""
        user = self.request.user
        if self.action == 'refund' and user.is_staff:
            # Staff refund other users' payments
            return PaymentTransaction.objects.all()
        return PaymentTransaction.objects.filter(booking__guest=user)

    @staticmethod
    def _parse_refund_amount(raw_amount, paid_amount):
        """
        Return (refund_amount, error). A missing amount means a full refund.
        """
        if raw_amount in (None, ''):
            return paid_amount, None
        try:
            amount = Decimal(str(raw_amount))
        except (InvalidOperation, ValueError):
            return None, 'Refund amount must be a number'
        if not amount.is_finite() or amount <= 0:
            return None, 'Refund amount must be greater than zero'
        if amount > paid_amount:
            return None, 'Refund amount cannot exceed the payment amount'
        return amount, None
    
    def create(self, request, *args, **kwargs):
        """
        Create a new payment transaction with idempotency.
        
        Uses idempotency key to prevent duplicate payment attempts.
        """
        # Idempotent replay is checked before validation: once the original
        # request has gone through, the booking may no longer be 'pending'
        existing_response = self._existing_transaction_response(request.data.get('idempotency_key'))
        if existing_response is not None:
            return existing_response

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        transaction_data = serializer.validated_data.copy()
        transaction_data['status'] = 'pending'
        # Audit fields come from the request itself, never from the body
        transaction_data['client_ip'] = self._get_client_ip(request)
        transaction_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')

        # A concurrent request with the same key loses the unique-constraint
        # race and gets the winner's transaction back (model save() runs
        # full_clean, so the clash can surface as either error type)
        try:
            with transaction.atomic():
                payment_transaction = PaymentTransaction.objects.create(**transaction_data)
        except (IntegrityError, DjangoValidationError):
            existing_response = self._existing_transaction_response(transaction_data['idempotency_key'])
            if existing_response is not None:
                return existing_response
            raise

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

        except NotImplementedError:
            # No production integration for this provider yet
            payment_transaction.status = 'failed'
            payment_transaction.error_code = 'PROVIDER_UNAVAILABLE'
            payment_transaction.error_message = 'Payment provider is not configured.'
            payment_transaction.save()
            return self._provider_unavailable_response()

        except PaymentAdapterError as e:
            # Handle payment adapter error. error_message/audit details are
            # internal records (staff-only), but the client response must not
            # echo str(e) -- it may carry adapter/provider internals.
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
                {'error': 'Payment could not be processed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """
        Confirm a payment transaction (local development mock flow only).

        Real payments are confirmed by the provider webhook, never by the
        client. This endpoint only works when both PAYMENT_TEST_MODE and
        DEBUG are enabled; otherwise it returns 403.
        """
        if not (settings.PAYMENT_TEST_MODE and settings.DEBUG):
            return Response(
                {'error': 'Payments are confirmed by the payment provider, not by the client.'},
                status=status.HTTP_403_FORBIDDEN
            )

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

            # Transaction and booking change together: if the booking can no
            # longer be confirmed (e.g. it was cancelled), the payment is not
            # left marked as completed
            old_status = payment_transaction.status
            try:
                with transaction.atomic():
                    booking = Booking.objects.select_for_update().get(pk=payment_transaction.booking_id)
                    booking.confirm_booking()
                    payment_transaction.status = 'completed'
                    payment_transaction.provider_response = provider_response
                    payment_transaction.save()
            except DjangoValidationError:
                payment_transaction.refresh_from_db()
                return Response(
                    {'error': 'Booking can no longer be confirmed'},
                    status=status.HTTP_409_CONFLICT
                )

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

            return Response(
                PaymentTransactionSerializer(payment_transaction).data,
                status=status.HTTP_200_OK
            )

        except NotImplementedError:
            return self._provider_unavailable_response()
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
                {'error': 'Payment could not be confirmed.'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def refund(self, request, pk=None):
        """
        Refund a payment transaction (staff only).

        Request body:
            amount: optional; omitted means a full refund, a smaller positive
                amount is a partial refund, more than the payment is rejected
            cancel_booking: optional boolean (default false); true also cancels
                the booking and releases its rooms
            cancellation_reason: optional text stored on the cancelled booking

        Everything happens in one database transaction with the payment row
        locked, so a payment cannot be refunded twice and a failure leaves
        nothing half done. If the booking cannot be cancelled, the provider is
        not asked to refund.
        """
        try:
            cancel_booking = serializers.BooleanField().to_internal_value(
                request.data.get('cancel_booking', False)
            )
        except serializers.ValidationError:
            return Response({'error': 'cancel_booking must be true or false'}, status=status.HTTP_400_BAD_REQUEST)
        cancellation_reason = str(request.data.get('cancellation_reason') or 'Refunded and cancelled by staff')[:500]

        tx_id = self.get_object().pk
        try:
            with transaction.atomic():
                payment_transaction = PaymentTransaction.objects.select_for_update().get(pk=tx_id)
                if payment_transaction.status != 'completed':
                    return Response(
                        {'error': 'Only completed payments can be refunded'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                refund_amount, error = self._parse_refund_amount(
                    request.data.get('amount'), payment_transaction.amount
                )
                if error:
                    return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
                new_status = 'refunded' if refund_amount == payment_transaction.amount else 'partially_refunded'

                booking = Booking.objects.select_for_update().get(pk=payment_transaction.booking_id)
                if cancel_booking:
                    can_cancel, _ = BookingStateMachine.validate_transition(
                        BookingState(booking.status), BookingState('cancelled')
                    )
                    if not can_cancel:
                        return Response(
                            {'error': f'Booking in status {booking.status} cannot be cancelled; nothing was refunded'},
                            status=status.HTTP_400_BAD_REQUEST
                        )

                adapter = get_payment_adapter(payment_transaction.provider)
                provider_response = adapter.refund_payment(
                    provider_transaction_id=payment_transaction.provider_transaction_id,
                    amount=refund_amount
                )

                old_status = payment_transaction.status
                details = {
                    'provider_response': provider_response,
                    'refund_amount': str(refund_amount),
                    'cancel_booking': cancel_booking,
                }
                payment_transaction.status = new_status
                payment_transaction.provider_response = provider_response
                payment_transaction.save()

                # A booking that was never marked paid (e.g. payment captured after it
                # was cancelled) keeps its payment status; the refund itself still stands.
                try:
                    with transaction.atomic():
                        booking.update_payment_status(new_status)
                except DjangoValidationError:
                    details['booking_payment_status'] = f'unchanged ({booking.payment_status})'

                if cancel_booking:
                    # Releases the booked rooms and logs booking_status_changed
                    booking.cancel_booking(cancellation_reason)

                PaymentAuditLog.log_action(
                    action='payment_refunded',
                    payment_transaction=payment_transaction,
                    booking=booking,
                    old_status=old_status,
                    new_status=payment_transaction.status,
                    actor=request.user,
                    ip_address=self._get_client_ip(request),
                    details=details
                )

        except NotImplementedError:
            return self._provider_unavailable_response()
        except PaymentAdapterError as e:
            # The atomic block rolled back; record the failure on its own
            payment_transaction = PaymentTransaction.objects.get(pk=tx_id)
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
                {'error': 'Payment could not be refunded.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = PaymentTransactionSerializer(payment_transaction).data
        data['booking_status'] = booking.status
        return Response(data, status=status.HTTP_200_OK)

    def _provider_unavailable_response(self):
        """503 for providers whose production integration is not implemented yet."""
        return Response(
            {'error': 'Payment provider is not configured.'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    def _existing_transaction_response(self, idempotency_key):
        """
        Response for a reused idempotency key, or None if the key is unused.

        The owner gets their original transaction back; a key belonging to
        another user is rejected without revealing that transaction.
        """
        if not idempotency_key:
            return None
        existing = PaymentTransaction.objects.select_related('booking').filter(
            idempotency_key=idempotency_key
        ).first()
        if existing is None:
            return None
        if existing.booking.guest_id != self.request.user.id:
            raise serializers.ValidationError(
                {'idempotency_key': ['This idempotency key has already been used.']}
            )
        return Response(PaymentTransactionSerializer(existing).data, status=status.HTTP_200_OK)

    def _get_client_ip(self, request):
        """Get client IP address from request."""
        return get_client_ip(request)


class WebhookEventViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for WebhookEvent model (read-only, staff only).
    
    Webhook payloads contain payment details and guest PII from every
    booking, so regular users must not see them.
    """
    queryset = WebhookEvent.objects.all()
    serializer_class = WebhookEventSerializer
    permission_classes = [IsAdminUser]


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
@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
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
            
    except WebhookNotConfiguredError as e:
        # Fail closed; 503 so the provider retries once the secret is configured
        logger.error(f"Webhook rejected: {e}")
        return Response(
            {'error': 'Webhook verification is not configured'},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    except WebhookNotSupportedError as e:
        logger.error(f"Webhook rejected: {e}")
        return Response(
            {'error': 'Webhooks are not supported for this provider'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except SignatureValidationError as e:
        logger.error(f"Webhook signature validation failed: {e}")
        return Response(
            {'error': 'Invalid signature'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except ValueError as e:
        logger.error(f"Webhook validation error: {e}")
        return Response(
            {'error': 'Invalid request'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        return Response(
            {'error': 'Processing error'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )