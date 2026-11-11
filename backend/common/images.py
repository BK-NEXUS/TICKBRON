"""Shrinking of the pictures hotel owners upload."""
import io
import logging
import os

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# The longest side a stored photo keeps: sharp on a 1440 px screen, a fraction of a phone photo's size
MAX_SIDE = 1600
QUALITY = 82
# Photos and logos are stored as WebP (about a third smaller than JPEG); a GIF may be animated, so it stays a GIF
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
    The same upload with a picture no bigger than `max_side`, stored as WebP (a GIF stays a GIF); the name ends with
    what the file really is (a PNG sent as photo.jpg is stored as photo.webp).

    Re-saving also drops the camera's hidden data (place, time, device); the turn it asked for is applied first.
    `keep_format` leaves a JPEG a JPEG and a PNG a PNG, for files that must keep their name.
    Something Pillow cannot read is handed back as it came (the callers have already checked it is a picture).
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
