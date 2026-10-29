"""`shrink_photos` shrinks stored hotel and room photos; it only reports by default and changes files with --apply."""
import io
from io import StringIO

import pytest
from django.core.management import call_command
from PIL import Image

from common.images import MAX_SIDE
from partner.tests.test_property_create_access import (inventory,  # noqa: F401
                                                       owner, owner_role)
from properties.models import PropertyPhoto, RoomPhoto

pytestmark = pytest.mark.django_db


def big_jpeg_bytes(side=(3200, 2400)):
    buffer = io.BytesIO()
    Image.effect_noise(side, 80).convert('RGB').save(buffer, format='JPEG')
    return buffer.getvalue()


@pytest.fixture
def stored(inventory, settings, tmp_path):
    """One full size hotel photo and one full size room photo already in storage."""
    settings.MEDIA_ROOT = tmp_path
    from django.core.files.base import ContentFile
    hotel_photo = PropertyPhoto(property=inventory['property'])
    hotel_photo.photo.save('old_hotel.jpg', ContentFile(big_jpeg_bytes()), save=True)
    room_photo = RoomPhoto(room_type=inventory['room'])
    room_photo.photo.save('old_room.jpg', ContentFile(big_jpeg_bytes()), save=True)
    return hotel_photo, room_photo


def size_of(photo):
    photo.refresh_from_db()
    with photo.photo.open('rb') as handle:
        raw = handle.read()
    return Image.open(io.BytesIO(raw)).size, len(raw)


def run(*args):
    out = StringIO()
    call_command('shrink_photos', *args, stdout=out)
    return out.getvalue()


def test_report_only_by_default(stored):
    hotel_photo, _ = stored
    before = size_of(hotel_photo)
    text = run()
    assert size_of(hotel_photo) == before
    assert '2 photos can be shrunk' in text


def test_apply_shrinks_hotel_and_room_photos_in_place(stored):
    hotel_photo, room_photo = stored
    names = (hotel_photo.photo.name, room_photo.photo.name)
    text = run('--apply')
    for photo, name in zip(stored, names):
        (width, height), size = size_of(photo)
        assert max(width, height) == MAX_SIDE
        assert photo.photo.name == name
    assert '2 photos shrunk' in text


def test_a_second_run_finds_nothing_to_do(stored):
    run('--apply')
    text = run('--apply')
    assert '0 photos shrunk' in text


def test_a_missing_file_is_skipped_not_fatal(stored):
    hotel_photo, _ = stored
    hotel_photo.photo.storage.delete(hotel_photo.photo.name)
    text = run('--apply')
    assert '1 photos shrunk' in text
    assert '1 files missing' in text
