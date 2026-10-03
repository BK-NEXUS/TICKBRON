"""
R4 security review: permission matrix for EVERY endpoint and role.

The routes come from Django's URL resolver, so a new endpoint is covered (and
must be classified in ACCESS below) without anyone remembering to add it.
For each route and HTTP method, every role outside the allowed set must get
401/403, and every role inside it must get past the permission check (any
status except 401/403) without a server error. Object ids do not exist
(999999), so nothing is changed; the ownership (IDOR) side is covered by the
per-app access tests and test_r4_idor.py.
"""
import re

import pytest
from django.urls import get_resolver
from django.urls.resolvers import URLResolver
from rest_framework.test import APIClient

from permissions.models import Role
from users.models import User

ROLES = ('anonymous', 'guest', 'owner', 'staff', 'superadmin')
PUBLIC = set(ROLES)
AUTHENTICATED = {'guest', 'owner', 'staff', 'superadmin'}
OWNER = {'owner', 'staff', 'superadmin'}
STAFF = {'staff', 'superadmin'}
SUPERADMIN = {'superadmin'}

# First matching (regex on the URL path, methods or None for all) wins.
ACCESS = [
    (r'^/api/(schema|docs|redoc)/$', None, PUBLIC),
    (r'^/api/v1/auth/(register|login|logout|csrf|otp/request|otp/verify)/$', None, PUBLIC),
    (r'^/api/v1/auth/(me|refresh|me/update)/$', None, AUTHENTICATED),
    (r'^/api/v1/properties/', None, PUBLIC),
    (r'^/api/v1/geography/', None, PUBLIC),
    (r'^/api/v1/payments/webhook/payme/$', None, PUBLIC),  # signature-checked, no session
    (r'^/api/v1/payments/transactions/999999/refund/$', None, STAFF),
    (r'^/api/v1/payments/webhooks/', None, STAFF),
    (r'^/api/v1/payments/', None, AUTHENTICATED),
    (r'^/api/v1/me/reviews/property_scores/$', None, PUBLIC),
    (r'^/api/v1/me/', None, AUTHENTICATED),
    (r'^/api/v1/bookings/', None, AUTHENTICATED),
    (r'^/api/v1/$', None, AUTHENTICATED),  # bookings router root
    (r'^/api/v1/partner/', None, OWNER),
    (r'^/api/v1/admin-panel/geography/', None, SUPERADMIN),
    (r'^/api/v1/admin-panel/users/create-hotel-owner/$', None, SUPERADMIN),
    (r'^/api/v1/admin-panel/exchange-rates/(status|\d+/accept)/$', None, SUPERADMIN),  # R6
    (r'^/api/v1/admin-panel/', None, STAFF),
]

# Allowed roles that still get 403 by design, not because of a permission check
FORBIDDEN_BY_DESIGN = {
    ('post', '/api/v1/me/notifications/'),  # notifications are created by the system only
    ('post', '/api/v1/payments/transactions/999999/confirm/'),  # test-mode endpoint, needs DEBUG
}

PATH_VALUES = {'provider': 'payme', 'code': 'UZ', 'country': 'UZ', 'region': '1'}


def _walk(patterns, prefix=''):
    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            yield from _walk(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            yield prefix + str(pattern.pattern), pattern.callback


def _concrete_path(route):
    path = route.replace('^', '').replace('$', '')
    path = re.sub(r'\(\?P<(\w+)>[^)]*\)', lambda m: PATH_VALUES.get(m.group(1), '999999'), path)
    path = re.sub(r'<(?:\w+:)?(\w+)>', lambda m: PATH_VALUES.get(m.group(1), '999999'), path)
    return '/' + path


def _methods(callback):
    actions = getattr(callback, 'actions', None)
    if actions:
        return sorted(actions)
    view = getattr(callback, 'cls', None) or getattr(callback, 'view_class', None)
    return sorted(
        m for m in ('get', 'post', 'put', 'patch', 'delete')
        if m in getattr(view, 'http_method_names', []) and hasattr(view, m)
    )


def _endpoints():
    seen = set()
    for route, callback in _walk(get_resolver().url_patterns):
        if 'format' in route or route.startswith('admin/'):
            continue
        path = _concrete_path(route)
        for method in _methods(callback):
            if (method, path) not in seen:
                seen.add((method, path))
                yield method, path


ENDPOINTS = sorted(_endpoints())


def _allowed(method, path):
    for pattern, methods, roles in ACCESS:
        if re.search(pattern, path) and (methods is None or method in methods):
            return roles
    return None


def test_every_endpoint_is_classified():
    unclassified = [(m, p) for m, p in ENDPOINTS if _allowed(m, p) is None]
    assert not unclassified, f'Add these endpoints to ACCESS: {unclassified}'
    assert len(ENDPOINTS) > 100


@pytest.fixture
def clients(db):
    owner_role, _ = Role.objects.get_or_create(name='hotel-owner')
    users = {
        'guest': User.objects.create_user(email='guest@example.com', password='x'),
        'owner': User.objects.create_user(email='owner@example.com', password='x', role=owner_role),
        'staff': User.objects.create_user(email='staff@example.com', password='x', is_staff=True),
        'superadmin': User.objects.create_user(
            email='root@example.com', password='x', is_staff=True, is_superuser=True,
        ),
    }
    result = {'anonymous': APIClient()}
    for role, user in users.items():
        client = APIClient()
        client.force_authenticate(user=user)
        result[role] = client
    return result


@pytest.mark.django_db
@pytest.mark.parametrize('method, path', ENDPOINTS, ids=[f'{m.upper()} {p}' for m, p in ENDPOINTS])
def test_role_matrix(clients, method, path):
    allowed = _allowed(method, path)
    problems = []
    for role in ROLES:
        client = clients[role]
        client.raise_request_exception = False
        response = getattr(client, method)(path, {}, format='json')
        code = response.status_code
        if role not in allowed:
            if code not in (401, 403):
                problems.append(f'{role} should be refused, got {code}')
        elif code >= 500:
            problems.append(f'{role} got server error {code}')
        elif code in (401, 403) and (method, path) not in FORBIDDEN_BY_DESIGN:
            problems.append(f'{role} should be allowed, got {code}')
    assert not problems, problems
