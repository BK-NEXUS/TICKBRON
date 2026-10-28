"""Shrinking of the pictures hotel owners upload."""
import io
import logging

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# The longest side a stored photo keeps: sharp on a 1440 px screen, a fraction of a phone photo's size
MAX_SIDE = 1600
QUALITY = 82
SAVE_OPTIONS = {
    'JPEG': {'quality': QUALITY, 'optimize': True, 'progressive': True},
    'WEBP': {'quality': QUALITY},
    'PNG': {'optimize': True},
    'GIF': {},
}


def shrink_upload(upload):
    """
    The same upload with a picture no bigger than MAX_SIDE, in the same format and under the same name.

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
        image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
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
    return SimpleUploadedFile(upload.name, buffer.getvalue(), content_type=upload.content_type)
