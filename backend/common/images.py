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
EXTENSION = {'JPEG': '.jpg', 'WEBP': '.webp', 'PNG': '.png', 'GIF': '.gif'}
SAVE_OPTIONS = {
    'JPEG': {'quality': QUALITY, 'optimize': True, 'progressive': True},
    'WEBP': {'quality': QUALITY},
    'PNG': {'optimize': True},
    'GIF': {},
}


def shrink_upload(upload, max_side=MAX_SIDE):
    """
    The same upload with a picture no bigger than `max_side`, in the same format; the name ends with what the file
    really is (a PNG sent as photo.jpg is stored as photo.png).

    Re-saving also drops the camera's hidden data (place, time, device); the turn it asked for is applied first.
    Something Pillow cannot read is handed back as it came (the callers have already checked it is a picture).
    """
    try:
        upload.seek(0)
        image = Image.open(upload)
        image_format = image.format
        if image_format not in SAVE_OPTIONS:
            return upload
        image = ImageOps.exif_transpose(image)
        image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        if image_format == 'JPEG' and image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        options = dict(SAVE_OPTIONS[image_format])
        if image.info.get('icc_profile'):
            options['icc_profile'] = image.info['icc_profile']
        buffer = io.BytesIO()
        image.save(buffer, format=image_format, **options)
    except Exception:
        logger.warning('Could not shrink the uploaded picture %s; stored as it came', upload.name, exc_info=True)
        upload.seek(0)
        return upload
    name = os.path.splitext(upload.name)[0] + EXTENSION[image_format]
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=upload.content_type)
