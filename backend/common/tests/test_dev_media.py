"""Local development (DEBUG) serves the uploaded photos at /media/; production does not (the web server does)."""
import importlib

import pytest
from django.test import override_settings
from django.urls import clear_url_caches

import config.urls


def served(client, media_root):
    (media_root / 'hotel.txt').write_text('photo')
    importlib.reload(config.urls)
    clear_url_caches()
    return client.get('/media/hotel.txt')


@pytest.fixture(autouse=True)
def restore_urls():
    yield
    importlib.reload(config.urls)
    clear_url_caches()


def test_debug_serves_the_media_folder(client, tmp_path):
    with override_settings(DEBUG=True, MEDIA_ROOT=tmp_path):
        response = served(client, tmp_path)
        assert response.status_code == 200
        assert b''.join(response.streaming_content) == b'photo'


def test_production_does_not_serve_it_from_django(client, tmp_path):
    with override_settings(DEBUG=False, MEDIA_ROOT=tmp_path):
        assert served(client, tmp_path).status_code == 404
