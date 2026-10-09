"""
Security tests for promotions (R10): injection, mass assignment, CSRF, spoofed counters,
information leaks, privilege boundaries and abuse limits.
"""
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.test import override_settings
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from common.dates import business_today
from promotions.models import Promotion, PromotionDailyStat
from promotions.tests.helpers import (
    make_guest, make_hotel, make_owner, make_promotion, make_staff, make_superadmin)

pytestmark = pytest.mark.django_db
A = '/api/v1/admin-panel'
SEARCH = '/api/v1/properties/search/'
HOME = '/api/v1/promotions/home/'

ATTACKS = [
    "' OR '1'='1", "'; DROP TABLE promotions; --", '" OR ""="', '%', '_', '\\', '%00', '<script>alert(1)</script>',
    '../../etc/passwd', '{{7*7}}', '${7*7}', 'a' * 5000, '‮', '😀' * 50,
]


def admin_client():
    client = APIClient()
    client.force_authenticate(user=make_superadmin())
    return client


@pytest.fixture
def hotel():
    return make_hotel(make_owner('o@example.com'), name='Registan Plaza')


class TestInjection:
    @pytest.mark.parametrize('attack', ATTACKS)
    def test_hotel_search_survives_hostile_text(self, hotel, attack):
        response = admin_client().get(f'{A}/promotion-hotels/', {'q': attack})
        assert response.status_code == 200
        assert Promotion.objects.count() == 0

    @pytest.mark.parametrize('attack', ATTACKS)
    def test_promotion_list_survives_hostile_text(self, hotel, attack):
        make_promotion(hotel)
        response = admin_client().get(f'{A}/promotions/', {'q': attack})
        assert response.status_code == 200
        assert Promotion.objects.count() == 1

    def test_percent_is_a_literal_not_a_wildcard(self, hotel):
        make_promotion(hotel)
        assert admin_client().get(f'{A}/promotions/', {'q': '%'}).json()['count'] == 0

    @pytest.mark.parametrize('attack', ATTACKS[:8])
    def test_search_page_survives_hostile_text(self, hotel, attack):
        make_promotion(hotel)
        assert APIClient().get(SEARCH, {'q': attack}).status_code in (200, 400)

    def test_tables_still_exist_after_attacks(self, hotel):
        client = admin_client()
        for attack in ATTACKS:
            client.get(f'{A}/promotions/', {'q': attack, 'status': attack, 'ordering': attack})
        assert Promotion.objects.count() == 0

    @pytest.mark.parametrize('param', ['status', 'paid', 'ordering', 'from', 'to'])
    def test_other_filters_reject_hostile_values(self, hotel, param):
        assert admin_client().get(f'{A}/promotions/', {param: "x' OR 1=1 --"}).status_code == 400

    @pytest.mark.parametrize('value', ["1 OR 1=1", "1;DROP", "-1", "0x1", "1e3", "٣"])
    def test_home_country_is_strict_integer(self, value):
        assert APIClient().get(HOME, {'country': value}).status_code == 400

    def test_hostile_note_is_stored_as_text_and_returned_as_json(self, hotel):
        first = business_today() + timedelta(days=1)
        response = admin_client().post(f'{A}/promotions/', {
            'property': hotel.pk, 'start_date': first.isoformat(), 'end_date': first.isoformat(),
            'note': '<script>alert(1)</script>'}, format='json')
        assert response.status_code == 201
        assert response['Content-Type'].startswith('application/json')
        assert response['X-Content-Type-Options'] == 'nosniff'
        assert response.json()['note'] == '<script>alert(1)</script>'


class TestMassAssignment:
    def test_create_ignores_server_controlled_fields(self, hotel):
        first = business_today() + timedelta(days=1)
        other_user = make_guest()
        response = admin_client().post(f'{A}/promotions/', {
            'property': hotel.pk, 'start_date': first.isoformat(), 'end_date': first.isoformat(),
            'status': 'active', 'paid_at': '2026-01-01T00:00:00Z', 'paid_marked_by': other_user.pk,
            'created_by': other_user.pk, 'is_deleted': True, 'is_active': False, 'id': 9999,
            'cancelled_reason': 'x'}, format='json')
        assert response.status_code == 201
        promotion = Promotion.objects.get()
        assert promotion.pk != 9999
        assert (promotion.status, promotion.paid_at, promotion.paid_marked_by_id) == ('scheduled', None, None)
        assert promotion.created_by_id != other_user.pk
        assert (promotion.is_deleted, promotion.is_active, promotion.cancelled_reason) == (False, True, '')

    def test_patch_cannot_revive_a_cancelled_or_ended_promotion(self, hotel):
        promotion = make_promotion(hotel, status='cancelled')
        response = admin_client().patch(f'{A}/promotions/{promotion.pk}/', {'priority': 1}, format='json')
        assert response.status_code == 400
        promotion.refresh_from_db()
        assert promotion.status == 'cancelled'

    def test_patch_cannot_clear_payment_or_move_hotel(self, hotel):
        promotion = make_promotion(hotel)
        paid_at = promotion.paid_at
        admin_client().patch(f'{A}/promotions/{promotion.pk}/', {
            'paid_at': None, 'property': make_hotel(make_owner('x@example.com'), name='X').pk,
            'status': 'ended'}, format='json')
        promotion.refresh_from_db()
        assert promotion.paid_at == paid_at and promotion.property_id == hotel.pk and promotion.status == 'active'


class TestSessionSecurity:
    def test_state_changing_calls_need_a_csrf_token_with_a_real_session(self, hotel):
        admin = make_superadmin('csrf@example.com')
        client = APIClient(enforce_csrf_checks=True)
        client.login(email=admin.email, password='Pass12345!')
        first = (business_today() + timedelta(days=1)).isoformat()
        response = client.post(f'{A}/promotions/', {'property': hotel.pk, 'start_date': first, 'end_date': first},
                               format='json')
        assert response.status_code == 403
        assert Promotion.objects.count() == 0

    def test_mark_paid_needs_csrf_too(self, hotel):
        admin = make_superadmin('csrf2@example.com')
        promotion = make_promotion(hotel, paid=False)
        client = APIClient(enforce_csrf_checks=True)
        client.login(email=admin.email, password='Pass12345!')
        assert client.post(f'{A}/promotions/{promotion.pk}/mark-paid/').status_code == 403
        promotion.refresh_from_db()
        assert promotion.paid_at is None

    def test_deactivated_admin_is_refused(self, hotel):
        admin = make_superadmin('gone@example.com')
        client = APIClient()
        assert client.login(email=admin.email, password='Pass12345!')
        assert client.get(f'{A}/promotions/').status_code == 200
        admin.is_active = False
        admin.save()
        assert client.get(f'{A}/promotions/').status_code in (401, 403)

    def test_former_staff_loses_access(self, hotel):
        staff = make_staff()
        staff.is_staff = False
        staff.save()
        client = APIClient()
        client.force_authenticate(user=staff)
        assert client.get(f'{A}/promotions/').status_code == 403

    def test_staff_cannot_escalate_through_any_write(self, hotel):
        staff = make_staff()
        promotion = make_promotion(hotel, paid=False)
        client = APIClient()
        client.force_authenticate(user=staff)
        calls = [('post', f'{A}/promotions/'), ('patch', f'{A}/promotions/{promotion.pk}/'),
                 ('post', f'{A}/promotions/{promotion.pk}/mark-paid/'),
                 ('post', f'{A}/promotions/{promotion.pk}/cancel/'), ('put', f'{A}/promotions/{promotion.pk}/'),
                 ('delete', f'{A}/promotions/{promotion.pk}/')]
        for method, url in calls:
            assert getattr(client, method)(url, {'reason': 'x'}, format='json').status_code in (403, 405), url
        promotion.refresh_from_db()
        assert promotion.paid_at is None and promotion.status == 'active'

    def test_hotel_owner_cannot_promote_or_read_own_promotion(self, hotel):
        promotion = make_promotion(hotel, paid=False)
        client = APIClient()
        client.force_authenticate(user=hotel.owner)
        assert client.get(f'{A}/promotions/{promotion.pk}/').status_code == 403
        assert client.post(f'{A}/promotions/{promotion.pk}/mark-paid/').status_code == 403
        assert client.get(f'{A}/promotions/{promotion.pk}/stats/').status_code == 403

    def test_delete_and_put_are_not_exposed(self, hotel):
        promotion = make_promotion(hotel)
        client = admin_client()
        assert client.delete(f'{A}/promotions/{promotion.pk}/').status_code == 405
        assert client.put(f'{A}/promotions/{promotion.pk}/', {}, format='json').status_code == 405
        assert Promotion.objects.filter(pk=promotion.pk, is_deleted=False).exists()


class TestCounterAbuse:
    def test_spoofed_forwarded_header_cannot_create_new_visitors(self, hotel):
        promotion = make_promotion(hotel)
        for number in range(30):
            APIClient(REMOTE_ADDR='10.0.0.1', HTTP_X_FORWARDED_FOR=f'203.0.113.{number}').post(
                f'/api/v1/promotions/{promotion.pk}/click/')
        assert PromotionDailyStat.objects.get(promotion=promotion).clicks == 1

    def test_cookie_and_user_agent_changes_do_not_inflate(self, hotel):
        promotion = make_promotion(hotel)
        for number in range(10):
            APIClient(REMOTE_ADDR='10.0.0.2', HTTP_USER_AGENT=f'bot-{number}', HTTP_COOKIE=f'sessionid=x{number}').post(
                f'/api/v1/promotions/{promotion.pk}/click/')
        assert PromotionDailyStat.objects.get(promotion=promotion).clicks == 1

    def test_hundred_refreshes_count_once(self, hotel):
        promotion = make_promotion(hotel)
        client = APIClient(REMOTE_ADDR='10.0.0.3')
        for _ in range(100):
            client.get(HOME)
        assert PromotionDailyStat.objects.get(promotion=promotion).impressions == 1

    def test_click_on_a_promotion_that_is_not_shown_is_not_counted(self, hotel):
        cases = ({'paid': False}, {'status': 'paused'}, {'status': 'cancelled'}, {'start_offset': 5})
        for index, kwargs in enumerate(cases):
            promotion = make_promotion(make_hotel(make_owner(f'case{index}@example.com'), name=f'Case{index}'),
                                       **kwargs)
            assert APIClient().post(f'/api/v1/promotions/{promotion.pk}/click/').status_code == 404
        assert PromotionDailyStat.objects.count() == 0

    def test_click_endpoint_is_throttled(self):
        client = APIClient(REMOTE_ADDR='10.7.7.7')
        with patch('promotions.views.TESTING', False):
            codes = [client.post('/api/v1/promotions/1/click/').status_code for _ in range(70)]
        assert 429 in codes

    def test_home_endpoint_is_throttled(self):
        client = APIClient(REMOTE_ADDR='10.7.7.8')
        with patch('promotions.views.TESTING', False):
            codes = [client.get(HOME).status_code for _ in range(70)]
        assert 429 in codes

    def test_counters_are_exact_under_many_visitors(self, hotel):
        promotion = make_promotion(hotel)
        for number in range(25):
            APIClient(REMOTE_ADDR=f'10.1.0.{number}').post(f'/api/v1/promotions/{promotion.pk}/click/')
        assert PromotionDailyStat.objects.get(promotion=promotion).clicks == 25


class TestLeaks:
    def test_public_endpoints_hide_owner_contact_and_payment_data(self, hotel):
        promotion = make_promotion(hotel)
        promotion.note = 'secret internal invoice 777'
        promotion.save(update_fields=['note'])
        for url in (HOME, SEARCH):
            text = APIClient().get(url).content.decode()
            for secret in ('o@example.com', 'secret internal invoice', 'price_amount', 'paid_at', 'paid_marked_by',
                           'cancelled_reason', 'created_by', 'owner@', '"owner"'):
                assert secret not in text, (url, secret)

    def test_public_card_has_no_owner_object(self, hotel):
        make_promotion(hotel)
        item = APIClient().get(HOME).json()['results'][0]
        assert 'owner' not in item and 'owner_id' not in item

    def test_hotel_search_for_admin_does_not_expose_owner_email(self, hotel):
        text = admin_client().get(f'{A}/promotion-hotels/', {'q': 'registan'}).content.decode()
        assert 'o@example.com' not in text and 'owner' not in text

    def test_audit_details_hold_only_whitelisted_non_personal_keys(self, hotel):
        client = admin_client()
        first = (business_today() + timedelta(days=1)).isoformat()
        created = client.post(f'{A}/promotions/', {'property': hotel.pk, 'start_date': first, 'end_date': first,
                                                   'price_amount': '100', 'note': 'call +998901234567'},
                              format='json').json()
        client.post(f'{A}/promotions/{created["id"]}/mark-paid/')
        client.post(f'{A}/promotions/{created["id"]}/cancel/', {'reason': 'phone +998901234567'}, format='json')
        for row in AdminAccessLog.objects.filter(action__startswith='promotion_'):
            assert set(row.details) <= AdminAccessLog.DETAIL_KEYS
            assert '998901234567' not in str(row.details)

    def test_audit_log_cannot_be_edited_or_deleted(self, hotel):
        client = admin_client()
        first = (business_today() + timedelta(days=1)).isoformat()
        client.post(f'{A}/promotions/', {'property': hotel.pk, 'start_date': first, 'end_date': first}, format='json')
        row = AdminAccessLog.objects.get(action='promotion_create')
        with pytest.raises(PermissionError):
            row.delete()
        with pytest.raises(PermissionError):
            AdminAccessLog.objects.all().delete()

    def test_errors_do_not_leak_internals(self, hotel):
        response = admin_client().post(f'{A}/promotions/', {'property': hotel.pk, 'start_date': 'x'}, format='json')
        text = response.content.decode()
        for leak in ('Traceback', 'File "', 'django.db', 'psycopg', 'SELECT '):
            assert leak not in text

    def test_unknown_id_and_forbidden_look_different_only_by_status(self, hotel):
        assert admin_client().get(f'{A}/promotions/999999/').status_code == 404
        assert APIClient().get(f'{A}/promotions/999999/').status_code in (401, 403)


class TestInputLimits:
    def test_huge_page_size_is_capped(self, hotel):
        for index in range(3):
            make_promotion(make_hotel(make_owner(f'p{index}@example.com'), name=f'P{index}'))
        response = admin_client().get(f'{A}/promotions/', {'page_size': 100000})
        assert response.status_code == 200
        assert len(response.json()['results']) <= 100

    def test_huge_or_negative_numbers_are_rejected(self, hotel):
        first = (business_today() + timedelta(days=1)).isoformat()
        client = admin_client()
        for field, value in (('priority', 10**12), ('priority', -5), ('price_amount', '1e30'),
                             ('price_amount', '-1'), ('price_amount', 'NaN'), ('price_amount', 'Infinity')):
            body = {'property': hotel.pk, 'start_date': first, 'end_date': first, field: value}
            assert client.post(f'{A}/promotions/', body, format='json').status_code == 400, (field, value)
        assert Promotion.objects.count() == 0

    def test_absurd_dates_are_rejected(self, hotel):
        client = admin_client()
        for start, end in (('0001-01-01', '0001-01-02'), ('9999-12-30', '9999-12-31'), ('2026-13-45', '2026-13-46'),
                           ('2026-10-10', '2036-10-10')):
            body = {'property': hotel.pk, 'start_date': start, 'end_date': end}
            assert client.post(f'{A}/promotions/', body, format='json').status_code == 400, (start, end)

    def test_wrong_json_shapes_are_rejected_not_500(self, hotel):
        client = admin_client()
        for body in ([], 'text', None, {'property': [1]}, {'property': {'a': 1}}, {'property': None}):
            response = client.post(f'{A}/promotions/', body, format='json')
            assert response.status_code == 400, body

    def test_oversized_json_body_is_handled(self, hotel):
        first = (business_today() + timedelta(days=1)).isoformat()
        response = admin_client().post(f'{A}/promotions/', {
            'property': hotel.pk, 'start_date': first, 'end_date': first, 'note': 'x' * 2_000_000}, format='json')
        assert response.status_code == 400

    def test_duplicate_overlapping_floods_create_one_row(self, hotel):
        first = (business_today() + timedelta(days=1)).isoformat()
        client = admin_client()
        codes = [client.post(f'{A}/promotions/', {'property': hotel.pk, 'start_date': first, 'end_date': first},
                             format='json').status_code for _ in range(10)]
        assert codes.count(201) == 1 and codes.count(400) == 9
        assert Promotion.objects.count() == 1


class TestDeploymentSettings:
    def test_sessions_cookies_are_httponly_and_samesite(self):
        from django.conf import settings
        assert settings.SESSION_COOKIE_HTTPONLY is True
        assert settings.CSRF_COOKIE_HTTPONLY is True
        assert settings.SESSION_COOKIE_SAMESITE in ('Lax', 'Strict')

    def test_public_endpoints_do_not_set_cookies_or_cache_publicly(self, hotel):
        make_promotion(hotel)
        response = APIClient().get(HOME)
        assert 'Set-Cookie' not in response.headers
        assert 'public' not in response.headers.get('Cache-Control', '')
