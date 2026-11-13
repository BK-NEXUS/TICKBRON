"""Kishi, qáte formadaǵı yamasa JPEG, PNG yamasa WebP bolmaǵan mehmanxana yamasa xona súwreti paydalanıw kerek ólshemler
menen biykar etiledi."""
import pytest

from common.testing import image_upload
from partner.tests.test_property_create_access import client_for, inventory, owner, owner_role  # noqa: F401
from properties.models import PropertyPhoto, RoomPhoto

pytestmark = pytest.mark.django_db


def post_photo(owner, inventory, kind, upload, **headers):
    target = inventory['property'] if kind == 'property' else inventory['room']
    folder = 'properties' if kind == 'property' else 'rooms'
    return client_for(owner).post(f'/api/v1/partner/{folder}/{target.id}/photos/', {'photo': upload}, format='multipart', **headers)


@pytest.mark.parametrize('kind,model', [('property', PropertyPhoto), ('room', RoomPhoto)])
class TestPhotoRules:
    def test_a_picture_that_is_too_small_is_refused_and_not_stored(self, owner, inventory, settings, tmp_path, kind, model):
        settings.MEDIA_ROOT = tmp_path
        response = post_photo(owner, inventory, kind, image_upload(800, 500))
        assert response.status_code == 400
        text = str(response.data['photo'])
        assert 'too small' in text and '800 x 500' in text and 'at least 1200 x 800 px' in text and '1600 x 1067 px' in text
        assert model.objects.count() == 0

    def test_a_portrait_picture_is_refused_for_its_shape(self, owner, inventory, settings, tmp_path, kind, model):
        settings.MEDIA_ROOT = tmp_path
        response = post_photo(owner, inventory, kind, image_upload(1200, 1800))
        assert response.status_code == 400
        assert 'wrong shape' in str(response.data['photo']) and '4:3 to 16:9' in str(response.data['photo'])
        assert model.objects.count() == 0

    def test_a_gif_is_refused(self, owner, inventory, settings, tmp_path, kind, model):
        settings.MEDIA_ROOT = tmp_path
        response = post_photo(owner, inventory, kind, image_upload(1600, 1067, fmt='GIF'))
        assert response.status_code == 400
        assert 'not a JPG, PNG or WebP' in str(response.data['photo'])
        assert model.objects.count() == 0

    def test_a_good_picture_is_stored_and_named_by_what_it_really_is(self, owner, inventory, settings, tmp_path, kind, model):
        settings.MEDIA_ROOT = tmp_path
        response = post_photo(owner, inventory, kind, image_upload(1600, 1067, fmt='PNG', name='holiday.jpg'))
        assert response.status_code == 201, response.data
        assert model.objects.get().photo.name.endswith('.webp')

    def test_the_refusal_is_said_in_the_page_language(self, owner, inventory, settings, tmp_path, kind, model):
        settings.MEDIA_ROOT = tmp_path
        response = post_photo(owner, inventory, kind, image_upload(800, 500), HTTP_ACCEPT_LANGUAGE='uz')
        assert response.status_code == 400
        text = str(response.data['photo'])
        assert 'too small' not in text and '800 x 500' in text and '1200 x 800' in text
