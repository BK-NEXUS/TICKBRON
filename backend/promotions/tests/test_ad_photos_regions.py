"""
Ad photos (up to 10 per promotion, set by the super-admin), what the banner shows, and the per-region view
of the advertising panel (.ai/PLAN_AD_REGIONS.md).
"""
import shutil
import tempfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from geography.models import City
from promotions import service
from promotions.models import Promotion, PromotionPhoto
from promotions.tests.helpers import make_guest, make_hotel, make_owner, make_promotion, make_staff, make_superadmin
from properties.models import PropertyPhoto

pytestmark = pytest.mark.django_db
A = '/api/v1/admin-panel'
HOME = '/api/v1/promotions/home/'
GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)
MEDIA = tempfile.mkdtemp()


@pytest.fixture(autouse=True)
def media_root():
    with override_settings(MEDIA_ROOT=MEDIA):
        yield
    shutil.rmtree(MEDIA, ignore_errors=True)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def admin():
    return client_for(make_superadmin())


@pytest.fixture
def hotel():
    return make_hotel(make_owner('o@example.com'), name='Registan Plaza')


@pytest.fixture
def promo(hotel):
    return make_promotion(hotel)


def gif(name='ad.gif', content=GIF):
    return SimpleUploadedFile(name, content, content_type='image/gif')


def upload(client, promo, **kwargs):
    return client.post(f'{A}/promotions/{promo.pk}/photos/', {'photo': kwargs.pop('file', None) or gif()}, format='multipart')


class TestAdPhotos:
    def test_super_admin_adds_photos_in_order_with_random_names(self, admin, promo):
        first = upload(admin, promo)
        second = upload(admin, promo, file=gif('my private name.gif'))

        assert (first.status_code, second.status_code) == (201, 201)
        assert second.json()['display_order'] > first.json()['display_order']
        stored = PromotionPhoto.objects.get(pk=second.json()['id']).photo.name
        assert stored.startswith(f'promotions/{promo.pk}/') and stored.endswith('.gif')
        assert 'private' not in stored

    def test_an_ad_holds_at_most_ten_photos(self, admin, promo):
        for _ in range(service.MAX_PHOTOS):
            assert upload(admin, promo).status_code == 201

        response = upload(admin, promo)

        assert response.status_code == 400
        assert response.json()['code'] == 'too_many_photos'
        assert PromotionPhoto.objects.filter(promotion=promo).count() == service.MAX_PHOTOS

    def test_a_deleted_photo_frees_its_place(self, admin, promo):
        ids = [upload(admin, promo).json()['id'] for _ in range(service.MAX_PHOTOS)]
        assert admin.delete(f'{A}/promotions/{promo.pk}/photos/{ids[0]}/').status_code == 204

        assert upload(admin, promo).status_code == 201

    def test_a_file_that_is_not_a_picture_is_refused(self, admin, promo):
        response = upload(admin, promo, file=gif('evil.gif', b'<script>alert(1)</script>'))

        assert response.status_code == 400
        assert response.json()['code'] == 'bad_image'
        assert PromotionPhoto.objects.count() == 0

    @pytest.mark.parametrize('state', ['ended', 'cancelled'])
    def test_photos_are_only_for_ads_that_can_still_change(self, admin, hotel, state):
        done = make_promotion(hotel, status=state)

        response = upload(admin, done)

        assert response.status_code == 400
        assert response.json()['code'] == 'bad_status'

    def test_delete_removes_the_photo_and_a_foreign_photo_is_404(self, admin, hotel, promo):
        other = make_promotion(make_hotel(make_owner('o2@example.com'), name='Other'))
        mine = upload(admin, promo).json()['id']
        theirs = upload(admin, other).json()['id']

        assert admin.delete(f'{A}/promotions/{promo.pk}/photos/{theirs}/').status_code == 404
        assert admin.delete(f'{A}/promotions/{promo.pk}/photos/{mine}/').status_code == 204
        assert PromotionPhoto.objects.get(pk=mine).is_deleted
        assert admin.delete(f'{A}/promotions/{promo.pk}/photos/{mine}/').status_code == 404

    def test_staff_can_read_but_not_change(self, admin, promo):
        upload(admin, promo)
        staff = client_for(make_staff())

        assert len(staff.get(f'{A}/promotions/{promo.pk}/photos/').json()) == 1
        assert upload(staff, promo).status_code == 403

    def test_guests_and_anonymous_have_no_access(self, promo):
        assert APIClient().get(f'{A}/promotions/{promo.pk}/photos/').status_code in (401, 403)
        assert client_for(make_guest()).get(f'{A}/promotions/{promo.pk}/photos/').status_code == 403

    def test_changes_are_written_to_the_audit_log(self, admin, promo):
        photo_id = upload(admin, promo).json()['id']
        admin.delete(f'{A}/promotions/{promo.pk}/photos/{photo_id}/')

        rows = AdminAccessLog.objects.filter(action__in=('promotion_photo_add', 'promotion_photo_remove')).order_by('id')
        assert [row.action for row in rows] == ['promotion_photo_add', 'promotion_photo_remove']
        assert rows[0].details == {'promotion_id': promo.pk, 'property_id': promo.property_id, 'object_id': photo_id}

    def test_the_promotion_lists_its_live_photos(self, admin, promo):
        keep = upload(admin, promo).json()['id']
        gone = upload(admin, promo).json()['id']
        admin.delete(f'{A}/promotions/{promo.pk}/photos/{gone}/')

        row = admin.get(f'{A}/promotions/{promo.pk}/').json()
        listed = admin.get(f'{A}/promotions/').json()['results'][0]

        assert [photo['id'] for photo in row['photos']] == [keep]
        assert row['photos'][0]['photo_url'].endswith('.gif')
        assert listed['photos_count'] == 1


class TestBannerPhotos:
    def banner(self):
        return APIClient().get(HOME).json()['results'][0]

    def test_the_banner_shows_the_ad_photos_when_the_ad_has_some(self, admin, hotel, promo):
        PropertyPhoto.objects.create(property=hotel, photo='properties/x/photos/hotel.gif', is_primary=True)
        for _ in range(3):
            upload(admin, promo)

        photos = self.banner()['promo_photos']

        assert len(photos) == 3
        assert all(url.startswith('/media/promotions/') or 'promotions/' in url for url in photos)

    def test_without_ad_photos_the_banner_shows_the_hotel_photos_cover_first_at_most_ten(self, hotel, promo):
        for number in range(12):
            PropertyPhoto.objects.create(
                property=hotel, photo=f'properties/x/photos/{number}.gif', display_order=number + 1)
        cover = PropertyPhoto.objects.create(
            property=hotel, photo='properties/x/photos/cover.gif', is_primary=True, display_order=99)

        photos = self.banner()['promo_photos']

        assert len(photos) == service.MAX_PHOTOS
        assert photos[0].endswith('cover.gif')
        assert photos[1].endswith('0.gif')
        assert cover.photo.url.endswith(photos[0].split('/')[-1])

    def test_a_banner_without_any_photo_has_an_empty_list(self, promo):
        assert self.banner()['promo_photos'] == []

    def test_deleted_ad_photos_are_not_shown(self, admin, hotel, promo):
        photo_id = upload(admin, promo).json()['id']
        admin.delete(f'{A}/promotions/{promo.pk}/photos/{photo_id}/')
        PropertyPhoto.objects.create(property=hotel, photo='properties/x/photos/h.gif', is_primary=True)

        assert [url.split('/')[-1] for url in self.banner()['promo_photos']] == ['h.gif']


def city_of(region_name):
    return City.objects.filter(region__name_en=region_name).first()


class TestRegionPanel:
    @pytest.fixture
    def world(self):
        owner = make_owner('o@example.com')
        samarkand = make_hotel(owner, name='Samarkand Inn', city_ref=city_of('Samarkand'))
        bukhara = make_hotel(owner, name='Bukhara Inn', city_ref=city_of('Bukhara'))
        waiting = make_hotel(owner, name='Samarkand Later', city_ref=city_of('Samarkand'))
        return {
            'running': make_promotion(samarkand), 'bukhara': make_promotion(bukhara),
            'future': make_promotion(waiting, start_offset=10), 'samarkand': samarkand, 'bukhara_hotel': bukhara,
        }

    def regions(self, client):
        response = client.get(f'{A}/promotions/regions/')
        assert response.status_code == 200
        return {row['name_en']: row for row in response.json()}

    def test_every_region_is_listed_with_what_runs_and_what_waits(self, admin, world):
        rows = self.regions(admin)

        samarkand = rows['Samarkand']
        assert (samarkand['running'], samarkand['waiting']) == (1, 1)
        assert [hotel['name'] for hotel in samarkand['hotels']] == ['Samarkand Inn']
        assert (rows['Bukhara']['running'], rows['Bukhara']['waiting']) == (1, 0)
        # A region nobody advertises in is still there, so the admin sees where ads can be sold
        assert rows['Tashkent']['running'] == 0 and rows['Tashkent']['hotels'] == []

    def test_unpaid_and_cancelled_ads_do_not_run(self, admin, world):
        unpaid = make_promotion(world['bukhara_hotel'], start_offset=40, paid=False)
        make_promotion(world['samarkand'], start_offset=20, status='cancelled')

        rows = self.regions(admin)

        assert rows['Bukhara']['running'] == 1
        assert rows['Bukhara']['waiting'] == 1
        assert rows['Samarkand']['waiting'] == 1
        assert unpaid.pk

    def test_busiest_regions_come_first(self, admin, world):
        make_promotion(make_hotel(make_owner('o3@example.com'), name='Second', city_ref=city_of('Bukhara')), start_offset=0)

        names = [row['name_en'] for row in admin.get(f'{A}/promotions/regions/').json()]

        assert names[0] == 'Bukhara'

    def test_the_list_can_be_limited_to_one_region(self, admin, world):
        region_id = world['samarkand'].region_ref_id

        ids = {row['id'] for row in admin.get(f'{A}/promotions/', {'region': region_id}).json()['results']}

        assert ids == {world['running'].pk, world['future'].pk}

    @pytest.mark.parametrize('value', ['abc', '0', '-3'])
    def test_a_bad_region_is_a_400(self, admin, value):
        response = admin.get(f'{A}/promotions/', {'region': value})

        assert response.status_code == 400
        assert response.json()['code'] == 'invalid_query'

    def test_staff_read_and_guests_cannot(self, world):
        assert client_for(make_staff()).get(f'{A}/promotions/regions/').status_code == 200
        assert client_for(make_guest()).get(f'{A}/promotions/regions/').status_code == 403
        assert APIClient().get(f'{A}/promotions/regions/').status_code in (401, 403)


class TestPromotionModel:
    def test_photo_rows_belong_to_the_promotion(self, promo):
        row = PromotionPhoto.objects.create(promotion=promo, photo='promotions/1/a.gif', display_order=1)

        assert list(promo.photos.all()) == [row]
        assert Promotion.objects.get(pk=promo.pk).photos.count() == 1
