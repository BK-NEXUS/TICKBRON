"""
TICKBRON Backend ushın óz exception handler leri.

API exception ları ushın birdey qátelik juwapların hám log lawdı támiyinleydi.
"""
import logging
from django.conf import settings
from django.core.exceptions import BadRequest, SuspiciousOperation
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from .exceptions import TickBronException
from .security_log import log_security_event

logger = logging.getLogger('tickbron')


def readable_text(detail):
    """DRF qátelik denesiniń ápiwayı teksti ('field: text'), hesh qashan Python dump emes."""
    if isinstance(detail, dict):
        parts = []
        for field, value in detail.items():
            text = readable_text(value)
            parts.append(text if field == 'non_field_errors' else f'{field}: {text}')
        return ' '.join(parts)
    if isinstance(detail, (list, tuple)):
        return ' '.join(readable_text(item) for item in detail)
    return str(detail)


def _log_refusal(exc, context, event):
    """Qabıllanbaǵan soraw ushın qáwipsizlik waqıyası; exception teksti log qa jazılmaydı (ol kirisiwdi qaytalawı múmkin)."""
    view = context.get('view')
    log_security_event(event, context.get('request'), view=view.__class__.__name__ if view is not None else 'unknown')


def custom_exception_handler(exc, context):
    """
    TICKBRON API ushın óz exception handler i.

    Durıs log lawdı menen birdey qátelik juwapların támiyinleydi.
    """
    # Aldın REST framework tiń ádettegi exception handler in shaqırıw
    response = exception_handler(exc, context)

    # Django tiń óz "soraw jaramsız" qátelikleri shaqırıwshınıń qátesi, server qátesi emes
    if response is None and isinstance(exc, (SuspiciousOperation, BadRequest)):
        logger.warning(f"Bad request: {exc.__class__.__name__}")
        return Response(
            {'error': {'code': 'bad_request', 'message': 'The request could not be processed.', 'details': None}},
            status=status.HTTP_400_BAD_REQUEST
        )

    # psycopg2 NUL belgisin soraw Python den shıqpastan aldın qabıllamaydı: shaqırıwshı database saqlay almaytuǵın nárse jiberdi
    if response is None and isinstance(exc, ValueError) and 'NUL (0x00)' in str(exc):
        logger.warning('Refused a NUL character that reached the database layer')
        return Response(
            {'error': {'code': 'invalid_input', 'message': 'The request contains a character that is not allowed.',
                       'details': None}},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Juwap None bolsa, ol API emes exception
    if response is None:
        # Kútilmegen exception lardı log qa jazıw
        logger.error(
            f"Unexpected exception: {exc.__class__.__name__} - {str(exc)}",
            exc_info=True,
            extra={'context': context}
        )

        # Standart qátelik juwabın qaytarıw
        return Response(
            {
                'error': {
                    'code': 'internal_error',
                    'message': 'An unexpected error occurred. Please try again later.',
                    'details': str(exc) if settings.DEBUG else None
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # TICKBRON óz exception ların islew
    if isinstance(exc, TickBronException):
        # Exception dı log qa jazıw (exception klasında aldınan log qa jazılǵan)
        logger.info(
            f"TICKBRON exception: {exc.__class__.__name__} - {str(exc)}",
            extra={'context': context}
        )

        # Rate limit exception ları ushın retry-after header in qosıw
        headers = {}
        if hasattr(exc, 'retry_after') and exc.retry_after:
            headers['Retry-After'] = str(exc.retry_after)

        # Standart qátelik juwabın qaytarıw
        return Response(
            {
                'error': {
                    'code': exc.default_code,
                    'message': str(exc.default_detail),
                    'details': str(exc) if exc.detail != exc.default_detail else None
                }
            },
            status=exc.status_code,
            headers=headers
        )

    # Validation qátelikların log qa jazıw
    if response.status_code == status.HTTP_400_BAD_REQUEST:
        logger.warning(
            f"Validation error: {str(exc)}",
            extra={'context': context}
        )

    # Ruxsat qátelikların, hám hár qabıllanbaǵan sorawdı qáwipsizlik waqıyası retinde log qa jazıw (kim, qayaqtan, qaysı URL)
    if response.status_code == status.HTTP_403_FORBIDDEN:
        logger.warning(
            f"Permission denied: {str(exc)}",
            extra={'context': context}
        )
        _log_refusal(exc, context, 'csrf_failed' if str(exc).startswith('CSRF Failed') else 'permission_denied')
    if response.status_code == status.HTTP_401_UNAUTHORIZED:
        _log_refusal(exc, context, 'unauthenticated')

    # Tabılmaǵan qátelikların log qa jazıw
    if response.status_code == status.HTTP_404_NOT_FOUND:
        logger.info(
            f"Resource not found: {str(exc)}",
            extra={'context': context}
        )

    # Rate limit qátelikların log qa jazıw
    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        logger.warning(
            f"Rate limit exceeded: {str(exc)}",
            extra={'context': context}
        )
        _log_refusal(exc, context, 'throttled')

    # Server qátelikların log qa jazıw
    if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger.error(
            f"Server error: {exc.__class__.__name__} - {str(exc)}",
            exc_info=True,
            extra={'context': context}
        )

    # Qátelik juwabı formatın standartlastırıw
    if hasattr(response, 'data'):
        original_data = response.data
        # Bar maǵlıwmattı, aldınan oralmaǵan bolsa, qátelik formatına oraw
        if not isinstance(original_data, dict) or 'error' not in original_data:
            if isinstance(original_data, dict):
                code = original_data.get('code', 'error')
                message = original_data.get('detail') or readable_text(original_data)
                details = original_data
            else:
                # Ápiwayı qatar/dizim menen kóterilgen ValidationError (mısalı
                # raise serializers.ValidationError('some message')) response.data di dict emes,
                # ErrorDetail dıń tuwrı dizimi etip qaldıradı.
                # original_data.get(...) bul jerde AttributeError kótergen bolar edi hám
                # bul 400 di islenbegen 500 ge aylandırar edi.
                items = original_data if isinstance(original_data, list) else [original_data]
                code = 'error'
                message = ' '.join(str(item) for item in items)
                details = {'non_field_errors': items}
            response.data = {
                'error': {
                    'code': code,
                    'message': message,
                    'details': details
                }
            }

    return response
