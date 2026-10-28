"""A photo an owner uploads is stored shrunk (longest side 1600 px) and without the camera's hidden data."""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from common.images import MAX_SIDE
from partner.tests.test_property_create_access import client_for, inventory, owner, owner_role  # noqa: F401
from properties.models import PropertyPhoto, RoomPhoto

pytestmark = pytest.mark.django_db


def big_jpeg():
    exif = Image.Exif()
    exif[0x010F] = 'PrivateCameraMaker'
    buffer = io.BytesIO()
    Image.effect_noise((3200, 2400), 80).convert('RGB').save(buffer, format='JPEG', exif=exif.tobytes())
    return SimpleUploadedFile('IMG_0001.jpg', buffer.getvalue(), content_type='image/jpeg'), buffer.tell()


def stored(photo):
    with photo.photo.open('rb') as handle:
        raw = handle.read()
    return Image.open(io.BytesIO(raw)), raw


def test_a_hotel_photo_is_stored_shrunk(owner, inventory, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    upload, original_size = big_jpeg()
    response = client_for(owner).post(
        f"/api/v1/partner/properties/{inventory['property'].id}/photos/", {'photo': upload}, format='multipart')
    assert response.status_code == 201, response.data
    image, raw = stored(PropertyPhoto.objects.get())
    assert max(image.size) == MAX_SIDE
    assert len(raw) < original_size / 3
    assert b'PrivateCameraMaker' not in raw


def test_a_room_photo_is_stored_shrunk(owner, inventory, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    upload, _ = big_jpeg()
    response = client_for(owner).post(
        f"/api/v1/partner/rooms/{inventory['room'].id}/photos/", {'photo': upload}, format='multipart')
    assert response.status_code == 201, response.data
    image, raw = stored(RoomPhoto.objects.get())
    assert max(image.size) == MAX_SIDE
    assert b'PrivateCameraMaker' not in raw
