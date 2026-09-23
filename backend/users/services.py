"""
OTP service for phone-based authentication.

This module provides OTP generation and verification with test mode support.
"""
import logging
from django.conf import settings
from django.db import transaction
from common.exceptions import ExternalServiceException
from users import lockout
from users.models import User

logger = logging.getLogger(__name__)


# The same responses whether or not the number is registered or locked, so the
# OTP endpoints do not reveal which phone numbers have accounts
OTP_REQUESTED_MESSAGE = 'If this phone number is registered, a verification code has been sent.'
OTP_INVALID_MESSAGE = 'Invalid or expired OTP code'


class OTPService:
    """
    Service for managing OTP-based phone authentication.
    """
    
    def __init__(self):
        self.test_mode = getattr(settings, 'SMS_TEST_MODE', True)
    
    def _is_test_mode(self) -> bool:
        """Check if SMS test mode is enabled."""
        return self.test_mode
    
    def _log_test_mode_call(self, method_name: str, **kwargs):
        """Log a call that's being routed through test mode."""
        logger.info(
            f"[SMS_TEST_MODE] {method_name} called. "
            f"Parameters: {kwargs}"
        )
    
    def send_otp(self, phone_number: str, client_ip: str = None) -> dict:
        """
        Send OTP code to the given phone number.
        
        In test mode, the OTP code is returned in the response instead of
        being sent via SMS.
        
        Args:
            phone_number: Phone number to send OTP to
            
        Returns:
            dict: Response with success status and OTP code (in test mode)
        """
        if self._is_test_mode():
            self._log_test_mode_call('send_otp', phone_number=phone_number)
            return self._mock_send_otp(phone_number, client_ip)
        
        # No real SMS provider is integrated yet; surface a 503 instead of a 500
        raise ExternalServiceException('SMS provider is not configured.', service_name='SMS')
    
    def _mock_send_otp(self, phone_number: str, client_ip: str = None) -> dict:
        """
        Mock OTP sending for test mode.

        Generates an OTP code and returns it in the response for testing.
        Unknown and locked numbers get the same success response without a
        code, so callers cannot tell them apart from registered numbers.
        """
        try:
            user = User.objects.filter(phone_number=phone_number).first()

            # A locked account gets no new code, so re-requesting cannot restart guessing
            if user is None or lockout.is_locked(user, client_ip):
                return {'success': True, 'message': OTP_REQUESTED_MESSAGE}

            # Generate OTP (the code itself is never logged)
            otp_code = user.generate_otp()

            logger.info(f"[SMS_TEST_MODE] OTP generated for {phone_number}")

            return {
                'success': True,
                'message': OTP_REQUESTED_MESSAGE,
                'otp_code': otp_code  # Only returned in test mode
            }
        except Exception as e:
            logger.error(f"Error generating OTP: {e}")
            return {
                'success': False,
                'message': f'Error generating OTP: {str(e)}'
            }
    
    def verify_otp(self, phone_number: str, otp_code: str, client_ip: str = None) -> dict:
        """
        Verify OTP code for the given phone number.
        
        Args:
            phone_number: Phone number associated with OTP
            otp_code: OTP code to verify
            
        Returns:
            dict: Response with success status and user info if valid
        """
        try:
            # Row lock serializes concurrent guesses so attempt counters cannot be raced
            with transaction.atomic():
                user = User.objects.select_for_update().get(phone_number=phone_number)
                
                # Check the lock before looking at the code, so a locked account
                # never reveals whether a guess was correct
                if lockout.is_locked(user, client_ip):
                    return {'success': False, 'message': OTP_INVALID_MESSAGE}
                
                if user.verify_otp(otp_code):
                    logger.info(f"OTP verified successfully for {phone_number}")
                    return {
                        'success': True,
                        'message': 'OTP verified successfully',
                        'user_id': user.id
                    }
                
                # Failures count toward the lockout across all issued codes,
                # so requesting a new code does not reset the budget
                lockout.record_failure(user, client_ip)
                logger.warning(f"OTP verification failed for {phone_number}")
                return {'success': False, 'message': OTP_INVALID_MESSAGE}
        except User.DoesNotExist:
            logger.warning(f"OTP verification for unknown phone number: {phone_number}")
            return {'success': False, 'message': OTP_INVALID_MESSAGE}
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return {
                'success': False,
                'message': f'Error verifying OTP: {str(e)}'
            }
