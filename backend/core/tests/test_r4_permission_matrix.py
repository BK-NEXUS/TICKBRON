"""
R4 qáwipsizlik tekseriwi: HÁR endpoint hám rol ushın ruxsat matricası.

Route lar Django nıń URL resolver inen keledi, sol sebepli jańa endpoint qaplanadı (hám
tómendegi ACCESS ke klassifikaciya etiliwi kerek), hesh kim qosıwdı este tutpastan.
Hár route hám HTTP metod ushın ruxsat etilgen toplamnan tısqarıdaǵı hár rol
401/403 alıwı kerek, hám ishindegi hár rol ruxsat tekseriwinen (401/403 den basqa qálegen
status) server qátelik siz ótiwi kerek. Obyekt id leri joq (999999), sol sebepli hesh nárse ózgermeydi;
iyelik (IDOR) tárepi hár app tıń kirisiw testleri hám test_r4_idor.py de qaplanǵan.
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

# Birinshi sáykes kelgen (URL jolında regex, metodlar yamasa hámmesi ushın None) jeńedi.
ACCESS = [
    (r'^/api/(schema|docs|redoc)/$', None, STAFF),  # L-2: endpoint inventarı, DEBUG sırtında tek staff
    (r'^/(healthz|readyz)/$', None, PUBLIC),  # A09: load balancer ushın tekseriwler, maǵlıwmat joq
    (r'^/api/v1/auth/(register|register/verify|register/resend|login|login/email-code|login/email-code/resend|logout|csrf|password-reset/request|password-reset/confirm|login/2fa)/$', None, PUBLIC),
    (r'^/api/v1/auth/(me|refresh|me/update|password/change|2fa/setup|2fa/confirm)/$', None, AUTHENTICATED),
    (r'^/api/v1/properties/', None, PUBLIC),
    (r'^/api/v1/geography/', None, PUBLIC),
    (r'^/api/v1/promotions/', None, PUBLIC),  # R10: bas bet karuseli hám klik sanaǵıshı
    (r'^/api/v1/me/reviews/(property_scores|public)/$', None, PUBLIC),  # mehmanxananıń tastıyıqlanǵan sharhları
    (r'^/api/v1/me/', None, AUTHENTICATED),
    (r'^/api/v1/chat/', None, AUTHENTICATED),  # qollap-quwatlaw chatı: akkauntıń óz thread i
    (r'^/api/v1/bookings/', None, AUTHENTICATED),
    (r'^/api/v1/$', None, AUTHENTICATED),  # bron router tamırı
    (r'^/api/v1/partner/', None, OWNER),
    (r'^/api/v1/admin-panel/geography/', None, SUPERADMIN),
    (r'^/api/v1/admin-panel/users/create-hotel-owner/$', None, SUPERADMIN),
    (r'^/api/v1/admin-panel/users/create-admin/$', None, SUPERADMIN),
    (r'^/api/v1/admin-panel/users/\d+/2fa-reset/$', None, SUPERADMIN),
    (r'^/api/v1/admin-panel/commission/\d+/rate/$', None, SUPERADMIN),  # procent super admin niń sheshimi
    (r'^/api/v1/admin-panel/exchange-rates/(status|\d+/accept)/$', None, SUPERADMIN),  # R6
    (r'^/api/v1/admin-panel/auto-completion/status/$', None, SUPERADMIN),  # R12
    (r'^/api/v1/admin-panel/promotions/', ('post', 'patch', 'put', 'delete'), SUPERADMIN),  # R10: ózgerisler
    (r'^/api/v1/admin-panel/$', None, STAFF),
    (r'^/api/v1/admin-panel/(amenities|audit-log|bookings|chat|commission|customers|exchange-rates|no-show-reports'
     r'|promotion-hotels|promotions|properties|reviews|statistics|status|users)/', None, STAFF),
]

# Ruxsat etilgen rollar ele dizayn boyınsha 403 aladı, ruxsat tekseriwinen emes
FORBIDDEN_BY_DESIGN = {
    ('post', '/api/v1/me/notifications/'),  # bildiriwlerdi tek sistema jaratadı
    ('post', '/api/v1/auth/login/2fa/'),  # hámmege ashıq, biraq sol session dıń parol qádemi islenbegenshe 401
    ('post', '/api/v1/auth/login/email-code/'),  # sol sıyaqlı: sol session dıń parol qádemi islenbegenshe 401
    ('post', '/api/v1/auth/login/email-code/resend/'),
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


def test_new_admin_routes_are_not_silently_staff_level():
    # A06/A01: hámmesin qaplaytuǵın qaǵıyda hár jańa /admin-panel/ route ın staff dárejesinde ún-túnsiz ótkizdi,
    # pulǵa tiyetuǵının da. Jańa topar ACCESS ke anıq dárejesi menen qosılıwı kerek.
    catch_all = [pattern for pattern, methods, _ in ACCESS if pattern == r'^/api/v1/admin-panel/' and methods is None]
    assert not catch_all


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
