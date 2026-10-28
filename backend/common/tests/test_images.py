"""Owner photos are shrunk before they are stored: a phone photo of 6 MB becomes a few hundred KB, and the
camera's hidden data (place, time, device) is not kept."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from common.images import MAX_SIDE, shrink_upload


def picture(size=(4000, 3000), fmt='JPEG', mode='RGB', exif=None, name='photo.jpg'):
    buffer = io.BytesIO()
    image = Image.effect_noise(size, 80).convert(mode) if mode != 'P' else Image.new('P', size)
    options = {'exif': exif} if exif else {}
    image.save(buffer, format=fmt, **options)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')


def opened(upload):
    upload.seek(0)
    return Image.open(io.BytesIO(upload.read()))


def test_a_large_photo_is_scaled_down_to_the_longest_side_and_is_smaller():
    original = picture()
    shrunk = shrink_upload(original)
    image = opened(shrunk)
    assert max(image.size) == MAX_SIDE
    assert image.size == (MAX_SIDE, 1200)  # the shape stays 4:3
    assert shrunk.size < original.size / 3
    assert image.format == 'JPEG'


def test_a_small_picture_is_not_enlarged():
    assert opened(shrink_upload(picture(size=(800, 600)))).size == (800, 600)


def test_the_file_name_and_type_stay_the_same():
    shrunk = shrink_upload(picture(name='front.jpg'))
    assert shrunk.name == 'front.jpg'
    assert shrunk.content_type == 'image/jpeg'


def test_hidden_camera_data_is_dropped_and_the_turn_is_applied():
    exif = Image.Exif()
    exif[0x0112] = 6  # the camera was held sideways: rotate 90 degrees to show it upright
    exif[0x010F] = 'PrivateCameraMaker'
    shrunk = shrink_upload(picture(size=(2000, 1000), exif=exif.tobytes()))
    image = opened(shrunk)
    assert image.size == (800, 1600)  # turned upright (1000 x 2000), then scaled to the longest side
    assert not image.getexif()
    shrunk.seek(0)
    assert b'PrivateCameraMaker' not in shrunk.read()


def test_a_png_with_transparency_stays_a_png_with_transparency():
    shrunk = shrink_upload(picture(size=(2400, 1200), fmt='PNG', mode='RGBA', name='logo.png'))
    image = opened(shrunk)
    assert image.format == 'PNG' and image.mode == 'RGBA'
    assert max(image.size) == MAX_SIDE


def test_webp_and_gif_keep_their_format():
    assert opened(shrink_upload(picture(fmt='WEBP', name='a.webp'))).format == 'WEBP'
    assert opened(shrink_upload(picture(size=(10, 10), fmt='GIF', mode='P', name='a.gif'))).format == 'GIF'


def test_a_file_that_is_not_a_picture_is_handed_back_unchanged():
    junk = SimpleUploadedFile('x.jpg', b'not a picture', content_type='image/jpeg')
    assert shrink_upload(junk) is junk
