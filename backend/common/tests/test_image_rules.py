"""
Hár súwret júklewdiń ólshem qaǵıydaları (.ai/PLAN_IMAGE_RULES.md): júdá kishi yamasa qáte formadaǵı súwret biykar etiledi,
paydalanıw kerek ólshemler menen; haqıyqıy JPEG, PNG yamasa WebP bolmaǵan nárse atı yamasa header i ne dese de biykar
etiledi.
"""
import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import translation
from PIL import Image

from common.image_rules import AD_BANNER, HOTEL_PHOTO, PLACE_PICTURE, ROOM_PHOTO, image_upload_error
from common.testing import image_upload

SMALLEST = [HOTEL_PHOTO, ROOM_PHOTO, AD_BANNER, PLACE_PICTURE]


def test_the_rules_are_the_ones_the_owner_approved():
    assert (HOTEL_PHOTO.min_width, HOTEL_PHOTO.min_height, HOTEL_PHOTO.recommended) == (1200, 800, (1600, 1067))
    assert (ROOM_PHOTO.min_width, ROOM_PHOTO.min_height, ROOM_PHOTO.recommended) == (1200, 800, (1600, 1067))
    assert (AD_BANNER.min_width, AD_BANNER.min_height, AD_BANNER.recommended) == (1600, 600, (1920, 720))
    assert (PLACE_PICTURE.min_width, PLACE_PICTURE.min_height, PLACE_PICTURE.recommended) == (800, 600, (1200, 900))
    assert (HOTEL_PHOTO.shape_label, AD_BANNER.shape_label) == ('4:3 to 16:9', '16:9 to 16:5')


@pytest.mark.parametrize('rule', SMALLEST)
def test_the_smallest_and_the_recommended_size_are_accepted(rule):
    width, height = rule.recommended
    assert image_upload_error(image_upload(rule.min_width, max(rule.min_height, height * rule.min_width // width)), rule) is None
    assert image_upload_error(image_upload(width, height), rule) is None


@pytest.mark.parametrize('rule', SMALLEST)
def test_a_picture_one_pixel_short_is_refused_and_the_message_names_both_sizes(rule):
    width, height = rule.recommended
    error = image_upload_error(image_upload(rule.min_width - 1, height), rule)
    assert f'({rule.min_width - 1} x {height} px)' in error
    assert f'at least {rule.min_width} x {rule.min_height} px' in error
    assert f'{width} x {height} px' in error
    assert 'JPG, PNG or WebP, up to 10 MB' in error


@pytest.mark.parametrize('rule', SMALLEST)
def test_the_shape_limits_are_inclusive(rule):
    low, high = rule.shape
    height = 1800  # shekler denominatorlarınıń hámmesine bóliner, sol sebepli eki shegara da pútin piksel
    assert image_upload_error(image_upload(int(height * high), height), rule) is None
    assert image_upload_error(image_upload(int(height * low), height), rule) is None


@pytest.mark.parametrize('rule', SMALLEST)
def test_a_picture_wider_or_taller_than_the_shape_is_refused_with_the_shape(rule):
    low, high = rule.shape
    too_wide = image_upload_error(image_upload(int(1800 * high) + 400, 1800), rule)
    too_tall = image_upload_error(image_upload(int(1800 * low) - 300, 1800), rule)
    for error in (too_wide, too_tall):
        assert 'wrong shape' in error
        assert rule.shape_label in error


def test_a_portrait_picture_is_not_a_hotel_photo():
    assert 'wrong shape' in image_upload_error(image_upload(1200, 1800), HOTEL_PHOTO)


def test_a_phone_photo_stored_sideways_is_judged_by_how_it_is_shown():
    # 4000 x 3000 piksel "oń jaqqa burıw" menen portret retinde tik kórinedi: biykar etiledi. 3000 x 4000 oń jaqqa burılǵan
    # landshaft retinde kórinedi: qabıllanadı
    assert 'wrong shape' in image_upload_error(image_upload(4000, 3000, orientation=6), HOTEL_PHOTO)
    assert image_upload_error(image_upload(3000, 4000, orientation=6), HOTEL_PHOTO) is None


@pytest.mark.parametrize('fmt', ['JPEG', 'PNG', 'WEBP'])
def test_jpeg_png_and_webp_are_accepted(fmt):
    assert image_upload_error(image_upload(1600, 1067, fmt=fmt), HOTEL_PHOTO) is None


def test_a_gif_is_refused():
    assert 'not a JPG, PNG or WebP' in image_upload_error(image_upload(1600, 1067, fmt='GIF'), HOTEL_PHOTO)


def test_a_text_file_renamed_jpg_is_refused_even_with_an_image_header():
    fake = SimpleUploadedFile('photo.jpg', b'<script>alert(1)</script>', content_type='image/jpeg')
    assert 'not a JPG, PNG or WebP' in image_upload_error(fake, HOTEL_PHOTO)


def test_an_svg_is_refused():
    svg = SimpleUploadedFile('logo.svg', b'<svg xmlns="http://www.w3.org/2000/svg" width="2000" height="1400"/>', content_type='image/svg+xml')
    assert image_upload_error(svg, HOTEL_PHOTO)
    renamed = SimpleUploadedFile('logo.jpg', svg.read(), content_type='image/jpeg')
    assert 'not a JPG, PNG or WebP' in image_upload_error(renamed, HOTEL_PHOTO)


def test_the_header_is_not_trusted_a_real_picture_with_a_wrong_header_is_accepted():
    upload = image_upload(1600, 1067)
    upload.content_type = 'application/octet-stream'
    assert image_upload_error(upload, HOTEL_PHOTO) is None


def test_a_picture_with_too_many_pixels_is_refused():
    buffer = io.BytesIO()
    Image.new('1', (7000, 6000)).save(buffer, format='PNG')
    upload = SimpleUploadedFile('huge.png', buffer.getvalue(), content_type='image/png')
    assert image_upload_error(upload, HOTEL_PHOTO) == 'Image dimensions are too large.'


def test_a_file_over_ten_megabytes_is_refused():
    upload = SimpleUploadedFile('big.jpg', b'0' * (10 * 1024 * 1024 + 1), content_type='image/jpeg')
    assert 'exceeds' in image_upload_error(upload, HOTEL_PHOTO)


def test_the_upload_can_still_be_read_after_the_check():
    upload = image_upload(1600, 1067)
    assert image_upload_error(upload, HOTEL_PHOTO) is None
    assert upload.read(3) == b'\xff\xd8\xff'


@pytest.mark.parametrize('language', ['uz', 'ru'])
def test_the_refusals_are_said_in_the_page_language(language):
    with translation.override(language):
        small = image_upload_error(image_upload(800, 500), HOTEL_PHOTO)
        shape = image_upload_error(image_upload(1200, 1800), HOTEL_PHOTO)
        kind = image_upload_error(SimpleUploadedFile('a.jpg', b'text', content_type='image/jpeg'), HOTEL_PHOTO)
    for text in (small, shape, kind):
        assert 'The picture' not in text and 'not a JPG' not in text
    assert '800 x 500' in small and '1200 x 800' in small
    assert '4:3' in shape
