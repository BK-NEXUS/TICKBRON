"""
OTP service for phone-based authentication.

This module provides OTP generation and verification with test mode support.
"""
import logging
from django.conf import settings
from common.exceptions import ExternalServiceException
from users.models import User

logger = logging.getLogger(__name__)


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
    
    def send_otp(self, phone_number: str) -> dict:
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
            return self._mock_send_otp(phone_number)
        
        # No real SMS provider is integrated yet; surface a 503 instead of a 500
        raise ExternalServiceException('SMS provider is not configured.', service_name='SMS')
    
    def _mock_send_otp(self, phone_number: str) -> dict:
        """
        Mock OTP sending for test mode.
        
        Generates an OTP code and returns it in the response for testing.
        User must already exist with the phone number.
        """
        try:
            # Find user by phone number (user must already exist)
            try:
                user = User.objects.get(phone_number=phone_number)
            except User.DoesNotExist:
                return {
                    'success': False,
                    'message': 'User not found with this phone number. Please register first.'
                }
            
            # Generate OTP
            otp_code = user.generate_otp()
            
            logger.info(f"[SMS_TEST_MODE] OTP generated for {phone_number}: {otp_code}")
            
            return {
                'success': True,
                'message': 'Test mode: OTP code generated successfully',
                'otp_code': otp_code  # Only returned in test mode
            }
        except Exception as e:
            logger.error(f"Error generating OTP: {e}")
            return {
                'success': False,
                'message': f'Error generating OTP: {str(e)}'
            }
    
    def verify_otp(self, phone_number: str, otp_code: str) -> dict:
        """
        Verify OTP code for the given phone number.
        
        Args:
            phone_number: Phone number associated with OTP
            otp_code: OTP code to verify
            
        Returns:
            dict: Response with success status and user info if valid
        """
        try:
            user = User.objects.get(phone_number=phone_number)
            
            if user.verify_otp(otp_code):
                logger.info(f"OTP verified successfully for {phone_number}")
                return {
                    'success': True,
                    'message': 'OTP verified successfully',
                    'user_id': user.id
                }
            else:
                logger.warning(f"OTP verification failed for {phone_number}")
                return {
                    'success': False,
                    'message': 'Invalid or expired OTP code'
                }
        except User.DoesNotExist:
            logger.warning(f"User not found for phone number: {phone_number}")
            return {
                'success': False,
                'message': 'User not found for this phone number'
            }
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return {
                'success': False,
                'message': f'Error verifying OTP: {str(e)}'
            }
