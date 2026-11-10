"""
Ad photos (up to 10 per promotion, set by the super-admin), what the banner shows, and the per-region view
of the advertising panel (.ai/PLAN_AD_REGIONS.md).
"""
import io
import shutil
import tempfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from django.test import override_settings
from rest_framework.test import APIClient

from admin_panel.models import AdminAccessLog
from common.testing import image_upload
from geography.models import Region
from promotions import service
from promotions.models import Promotion, PromotionPhoto
from promotions.tests.helpers import make_guest, make_hotel, make_owner, make_promotion, make_staff, make_superadmin
from properties.models import PropertyPhoto

pytestmark = pytest.mark.django_db
A = '/api/v1/admin-panel'
HOME = '/api/v1/promotions/home/'
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


def banner(name='ad.jpg', width=1920, height=720, **options):
    return image_upload(width, height, name=name, **options)


def upload(client, promo, **kwargs):
    return client.post(f'{A}/promotions/{promo.pk}/photos/', {'photo': kwargs.pop('file', None) or banner()}, format='multipart')


class TestAdPhotos:
    def test_super_admin_adds_photos_in_order_with_random_names(self, admin, promo):
        first = upload(admin, promo)
        second = upload(admin, promo, file=banner('my private name.jpg'))

        assert (first.status_code, second.status_code) == (201, 201)
        assert second.json()['display_order'] > first.json()['display_order']
        stored = PromotionPhoto.objects.get(pk=second.json()['id']).photo.name
        assert stored.startswith(f'promotions/{promo.pk}/') and stored.endswith('.jpg')
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
        response = upload(admin, promo, file=SimpleUploadedFile('evil.gif', b'<script>alert(1)</script>', content_type='image/gif'))

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
        assert row['photos'][0]['photo_url'].endswith('.jpg')
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


def region_of(region_name):
    return Region.objects.filter(name_en=region_name).first()


class TestRegionPanel:
    @pytest.fixture
    def world(self):
        owner = make_owner('o@example.com')
        samarkand = make_hotel(owner, name='Samarkand Inn', region_ref=region_of('Samarkand'))
        bukhara = make_hotel(owner, name='Bukhara Inn', region_ref=region_of('Bukhara'))
        waiting = make_hotel(owner, name='Samarkand Later', region_ref=region_of('Samarkand'))
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
        make_promotion(make_hotel(make_owner('o3@example.com'), name='Second', region_ref=region_of('Bukhara')), start_offset=0)

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


class TestAdBannerRules:
    """An ad banner is at least 1600 x 600 px, from 16:9 to 16:5; it is stored at most 2400 px wide."""

    def test_a_banner_that_is_too_small_is_refused(self, admin, promo):
        response = upload(admin, promo, file=banner(width=1200, height=450))
        assert response.status_code == 400
        assert response.json()['code'] == 'bad_image'
        text = response.json()['error']
        assert 'too small' in text and '1200 x 450' in text and 'at least 1600 x 600 px' in text and '1920 x 720 px' in text
        assert not PromotionPhoto.objects.filter(promotion=promo).exists()

    def test_a_square_picture_is_refused_for_its_shape(self, admin, promo):
        response = upload(admin, promo, file=banner(width=1800, height=1800))
        assert response.status_code == 400
        assert 'wrong shape' in response.json()['error'] and '16:9 to 16:5' in response.json()['error']

    def test_a_gif_is_refused(self, admin, promo):
        response = upload(admin, promo, file=banner('ad.gif', fmt='GIF'))
        assert response.status_code == 400
        assert 'not a JPG, PNG or WebP' in response.json()['error']

    def test_a_wide_banner_is_stored_at_most_2400_px_wide_without_camera_data(self, admin, promo):
        response = upload(admin, promo, file=banner(width=3600, height=1350))
        assert response.status_code == 201, response.json()
        with PromotionPhoto.objects.get(pk=response.json()['id']).photo.open('rb') as handle:
            raw = handle.read()
        assert Image.open(io.BytesIO(raw)).size == (2400, 900)
