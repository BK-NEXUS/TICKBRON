"""
The size rules of every picture upload (plan: .ai/PLAN_IMAGE_RULES.md).

A picture is stored only when it is a real JPEG, PNG or WebP of a size and shape that the site shows well; otherwise the
upload is refused with the sizes to use. The rules are data (one per kind of picture) and one function checks them, so the
hotel owner's, the admin's and the ad uploads cannot drift apart. The frontend repeats the numbers to show a hint and to
refuse early (frontend/src/utils/imageRules.ts); this module is the authority.
"""
from dataclasses import dataclass
from fractions import Fraction

from django.utils.translation import gettext as _
from PIL import Image

MAX_FILE_BYTES = 10 * 1024 * 1024
# A tiny file can expand to gigabytes of pixels when decoded
MAX_IMAGE_PIXELS = 40_000_000
# The pictures the site accepts, by what Pillow finds in the file (never by the name or the header the client sends)
ALLOWED_FORMATS = ('JPEG', 'PNG', 'WEBP')
# EXIF turn flags that show a picture on its side: the shape the visitor sees has width and height swapped
SIDEWAYS = {5, 6, 7, 8}
ORIENTATION_TAG = 0x0112


@dataclass(frozen=True)
class ImageRule:
    min_width: int
    min_height: int
    shape: tuple  # (narrowest, widest) as width / height
    shape_labels: tuple  # the same two limits as the people say them, e.g. ('4:3', '16:9')
    recommended: tuple  # (width, height)
    recommended_label: str  # the shape of the recommended size, e.g. '3:2'
    max_side: int  # the longest side a stored picture keeps (common/images.py shrinks to it)

    @property
    def shape_label(self):
        return f'{self.shape_labels[0]} to {self.shape_labels[1]}'


# Hotel and room photos: cards, gallery and room cards show them from 4:3 to 16:9
HOTEL_PHOTO = ImageRule(1200, 800, (Fraction(4, 3), Fraction(16, 9)), ('4:3', '16:9'), (1600, 1067), '3:2', 1600)
ROOM_PHOTO = ImageRule(1200, 800, (Fraction(4, 3), Fraction(16, 9)), ('4:3', '16:9'), (1600, 1067), '3:2', 1600)
# The ad carousel is 16:9 on a phone and 16:5 on a wide screen, and crops the middle in between
AD_BANNER = ImageRule(1600, 600, (Fraction(16, 9), Fraction(16, 5)), ('16:9', '16:5'), (1920, 720), '8:3', 2400)
# The "where to" cards of the home page are 4:3
PLACE_PICTURE = ImageRule(800, 600, (Fraction(6, 5), Fraction(9, 5)), ('6:5', '9:5'), (1200, 900), '4:3', 1600)


def _shown_size(image):
    """Width and height as a visitor sees the picture: a phone photo stored sideways is turned by its flag."""
    width, height = image.size
    if image.getexif().get(ORIENTATION_TAG) in SIDEWAYS:
        return height, width
    return width, height


def _the_picture(file):
    """(width, height) of a real JPEG, PNG or WebP as shown, 'dimensions' when it is far too big, None when it is not one."""
    try:
        file.seek(0)
        image = Image.open(file)
        if image.format not in ALLOWED_FORMATS:
            return None
        image.verify()
        file.seek(0)
        image = Image.open(file)
        width, height = image.size
        if width * height > MAX_IMAGE_PIXELS:
            return 'dimensions'
        return _shown_size(image)
    except Image.DecompressionBombError:
        return 'dimensions'
    except Exception:  # not a picture, or a damaged one: Pillow raises many kinds
        return None
    finally:
        file.seek(0)


def image_upload_error(file, rule):
    """The refusal text of an upload that does not fit `rule` (in the page language), or None when it can be stored."""
    if file.size > MAX_FILE_BYTES:
        return _('File size exceeds maximum allowed size of %(size)sMB') % {'size': MAX_FILE_BYTES / (1024 * 1024)}
    shown = _the_picture(file)
    if shown is None:
        return _('This is not a JPG, PNG or WebP picture. Send a JPG, PNG or WebP file, up to 10 MB.')
    if shown == 'dimensions':
        return _('Image dimensions are too large.')
    width, height = shown
    best = {'rec_width': rule.recommended[0], 'rec_height': rule.recommended[1], 'rec_shape': rule.recommended_label}
    if width < rule.min_width or height < rule.min_height:
        return _('The picture is too small (%(width)s x %(height)s px). Send at least %(min_width)s x %(min_height)s px; '
                 '%(rec_width)s x %(rec_height)s px (%(rec_shape)s) is best. JPG, PNG or WebP, up to 10 MB.') % {
            'width': width, 'height': height, 'min_width': rule.min_width, 'min_height': rule.min_height, **best}
    if not rule.shape[0] <= Fraction(width, height) <= rule.shape[1]:
        return _('The picture has the wrong shape (%(width)s x %(height)s px). Send a picture with a width to height ratio '
                 'from %(low)s to %(high)s; %(rec_width)s x %(rec_height)s px (%(rec_shape)s) is best. '
                 'JPG, PNG or WebP, up to 10 MB.') % {
            'width': width, 'height': height, 'low': rule.shape_labels[0], 'high': rule.shape_labels[1], **best}
    return None
