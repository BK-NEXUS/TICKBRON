"""Iye súwretleri saqlanbastan aldın kishireytiledi: 6 MB telefon súwreti bir neshe júz KB boladı, hám
kameranıń jasırın maǵlıwmatı (orın, waqıt, qurılma) saqlanbaydı."""
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
    assert image.size == (MAX_SIDE, 1200)  # forma 4:3 qaladı
    assert shrunk.size < original.size / 3
    assert image.format == 'WEBP'


def test_a_small_picture_is_not_enlarged():
    assert opened(shrink_upload(picture(size=(800, 600)))).size == (800, 600)


def test_a_jpeg_is_stored_as_webp_with_a_matching_name_and_type():
    shrunk = shrink_upload(picture(name='front.jpg'))
    assert shrunk.name == 'front.webp'
    assert shrunk.content_type == 'image/webp'


def test_hidden_camera_data_is_dropped_and_the_turn_is_applied():
    exif = Image.Exif()
    exif[0x0112] = 6  # kamera jantaytıp tutıldı: tik kórsetiw ushın 90 gradusqa burıw
    exif[0x010F] = 'PrivateCameraMaker'
    shrunk = shrink_upload(picture(size=(2000, 1000), exif=exif.tobytes()))
    image = opened(shrunk)
    assert image.size == (800, 1600)  # tik burıldı (1000 x 2000), keyin eń uzın tárepke shekem kishireytildi
    assert not image.getexif()
    shrunk.seek(0)
    assert b'PrivateCameraMaker' not in shrunk.read()


def test_a_png_with_transparency_becomes_webp_and_keeps_its_transparency():
    buffer = io.BytesIO()
    Image.new('RGBA', (2400, 1200), (200, 30, 30, 0)).save(buffer, format='PNG')  # pútkilley tiniq
    logo = SimpleUploadedFile('logo.png', buffer.getvalue(), content_type='image/png')
    image = opened(shrink_upload(logo))
    assert image.format == 'WEBP' and image.mode == 'RGBA'
    assert image.getpixel((0, 0))[3] == 0
    assert max(image.size) == MAX_SIDE


def test_webp_and_gif_keep_their_format():  # GIF animaciyalı bolıwı múmkin, sol sebepli tiymeydi
    assert opened(shrink_upload(picture(fmt='WEBP', name='a.webp'))).format == 'WEBP'
    assert opened(shrink_upload(picture(size=(10, 10), fmt='GIF', mode='P', name='a.gif'))).format == 'GIF'


def test_a_file_that_is_not_a_picture_is_handed_back_unchanged():
    junk = SimpleUploadedFile('x.jpg', b'not a picture', content_type='image/jpeg')
    assert shrink_upload(junk) is junk


def test_the_longest_side_can_be_chosen_per_kind_of_picture():
    shrunk = shrink_upload(picture(size=(3200, 1200)), max_side=2400)
    assert opened(shrunk).size == (2400, 900)


def test_the_stored_name_ends_with_what_the_file_really_is():
    assert shrink_upload(picture(fmt='PNG', name='holiday.jpg')).name == 'holiday.webp'
    assert shrink_upload(picture(fmt='WEBP', name='front.png')).name == 'front.webp'
    assert shrink_upload(picture(fmt='JPEG', name='scan.JPEG')).name == 'scan.webp'
    assert shrink_upload(picture(size=(10, 10), fmt='GIF', mode='P', name='a.png')).name == 'a.gif'
