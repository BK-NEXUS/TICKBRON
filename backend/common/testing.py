"""Test helper: a picture of a chosen size as an upload, for the tests of every upload (see common/image_rules.py)."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

EXTENSION = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp', 'GIF': 'gif'}


def image_upload(width=1600, height=1067, fmt='JPEG', name=None, orientation=None, color=(120, 90, 60)):
    """
    A real picture of width x height pixels (a plain colour: small file, any size). `orientation` writes the camera's
    turn flag (1-8) into a JPEG, as a phone does when it stores a portrait photo sideways.
    """
    options = {}
    if orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = orientation
        options['exif'] = exif.tobytes()
    buffer = io.BytesIO()
    Image.new('RGB', (width, height), color).save(buffer, format=fmt, **options)
    name = name or f'photo.{EXTENSION[fmt]}'
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=f'image/{fmt.lower()}')
