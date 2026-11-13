"""Test járdemshisi: tańlanǵan ólshemdegi súwret júklew retinde, hár júklewdiń testleri ushın (qarań common/image_rules.py)."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

EXTENSION = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp', 'GIF': 'gif'}


def image_upload(width=1600, height=1067, fmt='JPEG', name=None, orientation=None, color=(120, 90, 60)):
    """
    width x height piksel haqıyqıy súwret (bir reńli: kishkene fayl, qálegen ólshem). `orientation` kameranıń
    burıw belgisin (1-8) JPEG ge jazadı, telefon portret súwretti jantaytıp saqlaǵanda islegenindey.
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
