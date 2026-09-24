"""
Tests for the custom DRF exception handler.
"""
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from common.exception_handlers import custom_exception_handler


class CustomExceptionHandlerTest(TestCase):
    """Tests for custom_exception_handler."""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _context(self):
        return {'request': self.factory.get('/'), 'view': None}

    def test_dict_validation_error_uses_uniform_format(self):
        """A field-keyed ValidationError (the common case) already worked."""
        exc = ValidationError({'non_field_errors': ['Something is wrong.']})

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])

    def test_string_validation_error_does_not_500(self):
        """
        A ValidationError raised with a plain string produces a bare list in
        response.data (not a dict). The handler's fallback wrapping used to
        call response.data.get(...) unconditionally and crash with
        AttributeError, turning a 400 into an unhandled 500.
        """
        exc = ValidationError('This property is already in your favorites.')

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('This property is already in your favorites.', response.data['error']['message'])

    def test_list_validation_error_does_not_500(self):
        """A ValidationError raised with a plain list must also be handled uniformly."""
        exc = ValidationError(['First problem.', 'Second problem.'])

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('First problem.', response.data['error']['message'])
        self.assertIn('Second problem.', response.data['error']['message'])
