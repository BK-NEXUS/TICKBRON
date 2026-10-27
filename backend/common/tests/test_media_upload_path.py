"""A room photo is stored under its hotel's folder, not in a shared "temp" folder."""
from types import SimpleNamespace

from common.storage import get_media_upload_path


def test_hotel_photo_goes_to_the_hotel_folder():
    photo = SimpleNamespace(property=SimpleNamespace(id=7))
    assert get_media_upload_path(photo, 'a.jpg') == 'properties/7/photos/a.jpg'


def test_room_photo_goes_to_the_folder_of_its_hotel():
    photo = SimpleNamespace(room_type=SimpleNamespace(property_id=7))
    assert get_media_upload_path(photo, 'a.jpg') == 'properties/7/photos/a.jpg'


def test_unknown_owner_still_gets_a_path():
    assert get_media_upload_path(SimpleNamespace(), 'a.jpg') == 'properties/temp/photos/a.jpg'
