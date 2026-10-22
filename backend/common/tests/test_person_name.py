"""Person names take letters, never digits or symbols (the frontend filters the same way)."""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from rest_framework import status
from rest_framework.test import APIClient

from common.validators import validate_person_name

User = get_user_model()


class ValidatePersonNameTests(SimpleTestCase):
    def test_accepts_names_of_every_alphabet_with_the_usual_punctuation(self):
        for name in ["Olim", "O'tkir", "Oʻtkir", "Алишер Навоий", "Anne-Marie", "J. R. R.", "Jr."]:
            validate_person_name(name)

    def test_refuses_digits_and_symbols(self):
        for name in ["Olim7", "5Karimov", "a@b", "x_y", "Bob<script>", "😀"]:
            with self.assertRaises(ValidationError, msg=name):
                validate_person_name(name)

    def test_empty_is_left_to_the_field_required_rule(self):
        validate_person_name('')


class NameFieldsOnTheApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_refuses_digits_in_the_full_name(self):
        response = self.client.post('/api/v1/auth/register/', {
            'email': 'digits@example.com', 'full_name': 'Ali 99 Valiyev', 'password': 'Str0ng#Passw0rd!',
            'password_confirm': 'Str0ng#Passw0rd!',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='digits@example.com').exists())

    def test_profile_update_refuses_digits_in_names(self):
        user = User.objects.create_user(email='p@example.com', password='Str0ng#Passw0rd!', first_name='Ali', last_name='Vali')
        self.client.force_authenticate(user)
        for field in ('first_name', 'last_name', 'full_name'):
            response = self.client.patch('/api/v1/auth/me/update/', {field: 'Bad9'}, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, field)
        user.refresh_from_db()
        self.assertEqual((user.first_name, user.last_name), ('Ali', 'Vali'))

    def test_profile_update_accepts_a_proper_name(self):
        user = User.objects.create_user(email='q@example.com', password='Str0ng#Passw0rd!')
        self.client.force_authenticate(user)
        response = self.client.patch('/api/v1/auth/me/update/', {'first_name': "O'tkir"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
