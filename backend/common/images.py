"""Mehmanxana iyeleri júkleytuǵın súwretlerdi kishireytiw."""
import io
import logging
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Saqlanǵan súwret saqlaytuǵın eń uzın tárep: 1440 px ekranda anıq, telefon súwretiniń kishkene bólegi
MAX_SIDE = 1600
QUALITY = 82
# Súwretler hám logotip ler WebP retinde saqlanadı (JPEG ten shama menen úshten bir kishi); GIF animaciyalı bolıwı múmkin, sol
# sebepli GIF bolıp qaladı
STORED_AS = {'JPEG': 'WEBP', 'PNG': 'WEBP', 'WEBP': 'WEBP', 'GIF': 'GIF'}
EXTENSION = {'WEBP': '.webp', 'GIF': '.gif', 'JPEG': '.jpg', 'PNG': '.png'}
SAVE_OPTIONS = {
    'WEBP': {'quality': QUALITY, 'method': 4},
    'JPEG': {'quality': QUALITY, 'optimize': True, 'progressive': True},
    'PNG': {'optimize': True},
    'GIF': {},
}


def shrink_upload(upload, max_side=MAX_SIDE, keep_format=False):
    """
    `max_side` ten úlken bolmaǵan súwret penen sol júkleniw, WebP retinde saqlanadı (GIF GIF bolıp qaladı); at
    fayldıń haqıyqıy túri menen pitedi (photo.jpg dep jiberilgen PNG photo.webp retinde saqlanadı).

    Qayta saqlaw kameranıń jasırın maǵlıwmatın (orın, waqıt, qurılma) da taslaydı; ol soraǵan burıw aldın qollanıladı.
    `keep_format` JPEG di JPEG, PNG di PNG qaldıradı, atın saqlaw kerek fayllar ushın.
    Pillow oqıy almaǵan nárse qanday kelse sonday qaytarıladı (shaqırıwshılar onıń súwret ekenin aldınan tekserip bolǵan).
    """
    try:
        upload.seek(0)
        image = Image.open(upload)
        image_format = image.format
        if image_format not in STORED_AS:
            return upload
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        stored_format = image_format if keep_format else STORED_AS[image_format]
        if stored_format == 'JPEG' and image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        if stored_format == 'WEBP' and image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA' if 'transparency' in image.info or image.mode in ('LA', 'PA') else 'RGB')
        options = dict(SAVE_OPTIONS[stored_format])
        if image.info.get('icc_profile'):
            options['icc_profile'] = image.info['icc_profile']
        buffer = io.BytesIO()
        image.save(buffer, format=stored_format, **options)
    except Exception:
        logger.warning('Could not shrink the uploaded picture %s; stored as it came', upload.name, exc_info=True)
        upload.seek(0)
        return upload
    name = os.path.splitext(upload.name)[0] + EXTENSION[stored_format]
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{stored_format.lower()}')
