"""
Óz DRF exception handler i ushın testler.
"""
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory
from common.exception_handlers import custom_exception_handler


class CustomExceptionHandlerTest(TestCase):
    """custom_exception_handler ushın testler."""

    def setUp(self):
        self.factory = APIRequestFactory()

    def _context(self):
        return {'request': self.factory.get('/'), 'view': None}

    def test_dict_validation_error_uses_uniform_format(self):
        """Maydan kiltli ValidationError (keń tarqalǵan jaǵday) aldınan isleytuǵın edi."""
        exc = ValidationError({'non_field_errors': ['Something is wrong.']})

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('message', response.data['error'])

    def test_string_validation_error_does_not_500(self):
        """
        Ápiwayı qatar menen kóterilgen ValidationError response.data da tuwrı dizim (dict emes)
        payda etedi. Handler diń zapas oraw ı response.data.get(...) di shártsiz shaqırar edi hám
        AttributeError menen qulap, 400 di islenbegen 500 ge aylandırar edi.
        """
        exc = ValidationError('This property is already in your favorites.')

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('code', response.data['error'])
        self.assertIn('This property is already in your favorites.', response.data['error']['message'])

    def test_list_validation_error_does_not_500(self):
        """Ápiwayı dizim menen kóterilgen ValidationError de izbe-iz islenwi kerek."""
        exc = ValidationError(['First problem.', 'Second problem.'])

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
        self.assertIn('First problem.', response.data['error']['message'])
        self.assertIn('Second problem.', response.data['error']['message'])

    def test_field_errors_make_a_readable_message(self):
        """QA F7: xabar Python dump edi ({'category': [ErrorDetail(string=...)]}); details burınǵıday qaladı."""
        exc = ValidationError({'category': ['This field is required.'], 'name': ['Too long.', 'Bad.']})

        response = custom_exception_handler(exc, self._context())

        message = response.data['error']['message']
        self.assertEqual(message, 'category: This field is required. name: Too long. Bad.')
        self.assertNotIn('ErrorDetail', message)
        self.assertEqual(response.data['error']['details']['category'], ['This field is required.'])

    def test_non_field_errors_have_no_field_prefix(self):
        exc = ValidationError({'non_field_errors': ['Something is wrong.']})

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.data['error']['message'], 'Something is wrong.')

    def test_nested_errors_are_flattened(self):
        exc = ValidationError({'translations': {'en': {'name': ['Required.']}}})

        response = custom_exception_handler(exc, self._context())

        self.assertEqual(response.data['error']['message'], 'translations: en: name: Required.')
