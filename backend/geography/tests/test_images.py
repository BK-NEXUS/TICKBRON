"""
Pictures of countries and regions (plan .ai/PLAN_GEO_IMAGES.md): required when the super admin creates one,
random stored names, the usual image checks, old file removed on replace/delete, `image_url` in the public API.
"""
import io
import os

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from geography.models import City, Country, Region
from users.models import User

ADMIN = '/api/v1/admin-panel/geography'
PUBLIC = '/api/v1/geography'


def picture(name='flag.png', size=(40, 30), color=(200, 30, 30), fmt='PNG'):
    buffer = io.BytesIO()
    Image.new('RGB', size, color).save(buffer, format=fmt)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def client(db):
    admin = User.objects.create_superuser(email='admin@example.com', password='AdminPassword#123')
    api = APIClient()
    api.force_authenticate(user=admin)
    return api


COUNTRY = {'code': 'XC', 'currency': 'USD', 'name_uz': 'Cland', 'name_ru': 'Цландия', 'name_en': 'Cland'}


@pytest.fixture
def country(db):
    return Country.objects.create(code='XD', name_uz='Dland', name_ru='Дландия', name_en='Dland', currency='USD')


@pytest.mark.django_db
class TestCountryPicture:
    def test_a_new_country_needs_a_picture(self, client):
        response = client.post(f'{ADMIN}/countries/', COUNTRY, format='multipart')
        assert response.status_code == 400
        assert 'image' in response.data['error']['details']
        assert not Country.objects.filter(code='XC').exists()

    def test_create_with_a_picture_stores_a_random_name_and_returns_the_url(self, client):
        response = client.post(f'{ADMIN}/countries/', {**COUNTRY, 'image': picture('my private flag.png')}, format='multipart')
        assert response.status_code == 201, response.data
        stored = Country.objects.get(code='XC').image.name
        assert stored.startswith('geography/countries/') and stored.endswith('.png')
        assert 'private' not in stored
        assert response.data['image_url'].endswith(stored)
        assert 'image' not in response.data or not isinstance(response.data['image'], str)

    @pytest.mark.parametrize('upload', [
        SimpleUploadedFile('x.png', b'not an image', content_type='image/png'),
        SimpleUploadedFile('x.bmp', b'BM' + b'0' * 200, content_type='image/bmp'),
    ])
    def test_a_bad_file_is_400_and_creates_nothing(self, client, upload):
        response = client.post(f'{ADMIN}/countries/', {**COUNTRY, 'image': upload}, format='multipart')
        assert response.status_code == 400
        assert 'image' in response.data['error']['details']
        assert not Country.objects.filter(code='XC').exists()

    def test_a_huge_pixel_count_is_refused(self, client):
        response = client.post(f'{ADMIN}/countries/', {**COUNTRY, 'image': picture(size=(12000, 12000), fmt='PNG')}, format='multipart')
        assert response.status_code == 400
        assert 'image' in response.data['error']['details']

    def test_edit_without_a_picture_keeps_the_old_one(self, client, country):
        country.image.save('a.png', picture(), save=True)
        before = country.image.name
        response = client.patch(f'{ADMIN}/countries/{country.pk}/', {'name_en': 'Dland2'}, format='json')
        assert response.status_code == 200
        country.refresh_from_db()
        assert country.image.name == before

    def test_replacing_the_picture_removes_the_old_file(self, client, country):
        country.image.save('a.png', picture(), save=True)
        old_path = country.image.path
        response = client.patch(f'{ADMIN}/countries/{country.pk}/', {'image': picture('b.png', color=(0, 0, 255))}, format='multipart')
        assert response.status_code == 200, response.data
        country.refresh_from_db()
        assert country.image.name != os.path.relpath(old_path, country.image.storage.location)
        assert not os.path.exists(old_path)
        assert os.path.exists(country.image.path)

    def test_deleting_the_country_removes_its_file(self, client, country):
        country.image.save('a.png', picture(), save=True)
        path = country.image.path
        assert client.delete(f'{ADMIN}/countries/{country.pk}/').status_code == 204
        assert not os.path.exists(path)

    def test_a_country_that_cannot_be_deleted_keeps_its_file(self, client, country):
        country.image.save('a.png', picture(), save=True)
        Region.objects.create(country=country, name_uz='R', name_ru='Р', name_en='R')
        assert client.delete(f'{ADMIN}/countries/{country.pk}/').status_code == 409
        assert os.path.exists(country.image.path)


@pytest.mark.django_db
class TestRegionPicture:
    def body(self, country, **extra):
        return {'country': country.pk, 'name_uz': 'Sharq', 'name_ru': 'Восток', 'name_en': 'East', **extra}

    def test_a_new_region_needs_a_picture(self, client, country):
        response = client.post(f'{ADMIN}/regions/', self.body(country), format='multipart')
        assert response.status_code == 400
        assert 'image' in response.data['error']['details']

    def test_create_with_a_picture(self, client, country):
        response = client.post(f'{ADMIN}/regions/', self.body(country, image=picture()), format='multipart')
        assert response.status_code == 201, response.data
        stored = Region.objects.get(name_en='East').image.name
        assert stored.startswith('geography/regions/')
        assert response.data['image_url'].endswith(stored)

    def test_cities_have_no_picture_field(self, client, country):
        region = Region.objects.create(country=country, name_uz='R', name_ru='Р', name_en='R')
        response = client.post(f'{ADMIN}/cities/', {'region': region.pk, 'name_uz': 'C', 'name_ru': 'С', 'name_en': 'C'}, format='json')
        assert response.status_code == 201
        assert 'image_url' not in response.data


@pytest.mark.django_db
class TestPublicPictures:
    def test_rows_with_and_without_a_picture(self, client, country):
        other = Country.objects.create(code='XE', name_uz='E', name_ru='Е', name_en='E', currency='USD')
        country.image.save('a.png', picture(), save=True)
        rows = {row['code']: row for row in APIClient().get(f'{PUBLIC}/countries/').data}
        assert rows['XD']['image_url'].endswith(country.image.name)
        assert rows['XE']['image_url'] is None
        assert 'image' not in rows['XD']
        assert other.image.name in (None, '')

    def test_regions_list_has_image_url(self, client, country):
        region = Region.objects.create(country=country, name_uz='R', name_ru='Р', name_en='R')
        region.image.save('r.png', picture(), save=True)
        rows = APIClient().get(f'{PUBLIC}/countries/{country.code}/regions/').data
        assert rows[0]['image_url'].endswith(region.image.name)

    def test_cities_list_is_unchanged(self, client, country):
        region = Region.objects.create(country=country, name_uz='R', name_ru='Р', name_en='R')
        City.objects.create(region=region, name_uz='C', name_ru='С', name_en='C')
        rows = APIClient().get(f'{PUBLIC}/regions/{region.pk}/cities/').data
        assert 'image_url' not in rows[0]


@pytest.mark.django_db
class TestMultipartKeepsRowsVisible:
    def test_a_form_without_is_active_creates_a_visible_row_and_can_hide_it(self, client, country):
        created = client.post(f'{ADMIN}/countries/', {**COUNTRY, 'image': picture()}, format='multipart')
        assert created.data['is_active'] is True
        hidden = client.post(f'{ADMIN}/countries/', {**COUNTRY, 'code': 'XF', 'name_en': 'F', 'image': picture(), 'is_active': 'false'}, format='multipart')
        assert hidden.data['is_active'] is False

    def test_a_form_edit_without_is_active_does_not_hide_the_row(self, client, country):
        response = client.patch(f'{ADMIN}/countries/{country.pk}/', {'name_en': 'Renamed'}, format='multipart')
        assert response.status_code == 200
        country.refresh_from_db()
        assert country.is_active is True
