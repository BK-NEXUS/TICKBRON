"""
Every text the API can show a visitor is worded in the page language: the plain English messages of the
bookings, accounts, users, properties, geography, currency, promotions and admin code are wrapped in
gettext and translated in the uz and ru catalogs (locale/). A new refusal text with no translation fails here.
"""
import ast
import pathlib

import pytest
from django.core.cache import cache
from django.utils import translation
from rest_framework.test import APIClient

from properties.models import Property, PropertyType
from users.models import User

BACKEND = pathlib.Path(__file__).resolve().parents[2]
APPS = ['bookings', 'users', 'accounts', 'properties', 'promotions', 'admin_panel', 'geography', 'currency', 'partner', 'common']
# Raised or returned to a client: these calls carry the text
CARRIERS = {'ValidationError', 'Response', 'JsonResponse', 'PermissionDenied', 'NotFound', 'ParseError'}
GETTEXT = {'_', 'gettext', 'gettext_lazy', '_lazy'}
# Not shown to visitors: the payments tables are dropped (cash only); the generic server envelope is the client's own fallback
LEFT_ALONE = {'payments', 'common/exception_handlers.py', 'common/middleware.py', 'common/decorators.py'}
# The hotel page shows its own translated "not found" text; the client reads this one only as a status
ENGLISH_BY_DESIGN = {('properties/views.py', 'Property not found'), ('properties/views.py', 'Property with ID ')}


def call_name(call):
    func = call.func
    return func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', '')


def sources():
    for app in APPS:
        for path in sorted((BACKEND / app).rglob('*.py')):
            relative = str(path.relative_to(BACKEND))
            if '/tests/' in relative or 'migrations' in relative or 'management' in relative or path.name.startswith('test_'):
                continue
            if any(relative.startswith(left) or relative == left for left in LEFT_ALONE):
                continue
            yield relative, ast.parse(path.read_text())


def inside(node, parents, names):
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.Call) and call_name(node) in names:
            return True
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
            return False
    return False


def parent_map(tree):
    return {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}


def texts():
    """(file, line, msgid, wrapped) for every literal English sentence a carrier call is given."""
    for relative, tree in sources():
        parents = parent_map(tree)
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Constant) and isinstance(node.value, str)):
                continue
            wrapped = inside(node, parents, GETTEXT)
            if not inside(node, parents, CARRIERS) or isinstance(parents.get(node), ast.Expr):
                continue
            if len(node.value.split()) >= 3 and node.value[:1].isupper() and (relative, node.value) not in ENGLISH_BY_DESIGN:
                yield relative, node.lineno, node.value, wrapped


def test_no_plain_english_sentence_is_sent_to_a_client():
    plain = [f'{file}:{line} {text[:60]!r}' for file, line, text, wrapped in texts() if not wrapped]
    assert not plain, 'wrap in gettext and add to locale/uz and locale/ru:\n' + '\n'.join(plain)


@pytest.mark.parametrize('language', ['uz', 'ru'])
def test_every_wrapped_text_has_a_translation(language):
    with translation.override(language):
        missing = sorted({f'{file}:{line} {text[:70]!r}' for file, line, text, wrapped in texts()
                          if wrapped and translation.gettext(text) == text})
    assert not missing, '\n'.join(missing)


@pytest.fixture(autouse=True)
def clean_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestEndpointsAnswerInTheLanguage:
    def test_favorite_twice(self):
        user = User.objects.create_user(email='guest@example.com', password='x')
        hotel = Property.objects.create(
            owner=user, property_type=PropertyType.objects.create(name='Hotel', slug='hotel'), status='active',
            max_guests=2, bedrooms=1, bathrooms=1, city='Tashkent', country='Uzbekistan', base_price=50, currency='USD')
        client = APIClient()
        client.force_authenticate(user=user)
        client.post('/api/v1/me/favorites/', {'property': hotel.id}, format='json')

        uz = client.post('/api/v1/me/favorites/', {'property': hotel.id}, format='json', HTTP_ACCEPT_LANGUAGE='uz')
        en = client.post('/api/v1/me/favorites/', {'property': hotel.id}, format='json')

        assert en.data['error']['message'] == 'This property is already in your favorites.'
        assert uz.data['error']['message'] == "Bu mehmonxona allaqachon sevimlilaringizda."

    def test_wrong_current_password(self):
        user = User.objects.create_user(email='guest@example.com', password='Old-Password#2026')
        client = APIClient()
        client.force_authenticate(user=user)
        body = {'current_password': 'wrong', 'password': 'Fresh9Grape#Tower42', 'password_confirm': 'Fresh9Grape#Tower42'}

        ru = client.post('/api/v1/auth/password/change/', body, format='json', HTTP_ACCEPT_LANGUAGE='ru')

        assert ru.status_code == 400
        assert ru.data['current_password'] == ['Текущий пароль неверный.']
