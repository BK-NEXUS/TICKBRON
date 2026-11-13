"""
Hár súwret júklewdiń ólshem qaǵıydaları (reje: .ai/PLAN_IMAGE_RULES.md).

Súwret tek haqıyqıy JPEG, PNG yamasa WebP bolsa hám saytta jaqsı kórinetuǵın ólshemde hám formada bolsa saqlanadı;
bolmasa júkleniw paydalanıw kerek ólshemler menen biykar etiledi. Qaǵıydalar maǵlıwmat (hár súwret túri ushın bir) hám bir
funkciya
olardı tekseredi, sol sebepli mehmanxana iyesiniń, adminniń hám reklama júklewleri bir-birinen ayrılıp ketpeydi.
Frontend sanlardı kórsetpe ushın hám erte biykar etiw ushın qaytaladı (frontend/src/utils/imageRules.ts);
bul modul tiykarǵı hújjet.
"""
from dataclasses import dataclass
from fractions import Fraction

from django.utils.translation import gettext as _
from PIL import Image

MAX_FILE_BYTES = 10 * 1024 * 1024
# Kishkene fayl ashılǵanda gigabaytlap piksel bolıp keńeyiwi múmkin
MAX_IMAGE_PIXELS = 40_000_000
# Sayt qabıllaytuǵın súwretler, Pillow fayldan tapqanı boyınsha (hesh qashan klient jiberetuǵın at yamasa header boyınsha emes)
ALLOWED_FORMATS = ('JPEG', 'PNG', 'WEBP')
# Súwretti jantayıp kórsetetuǵın EXIF burıw belgileri: paydalanıwshı kóretuǵın formada eni menen boyı almasadı
SIDEWAYS = {5, 6, 7, 8}
ORIENTATION_TAG = 0x0112


@dataclass(frozen=True)
class ImageRule:
    min_width: int
    min_height: int
    shape: tuple  # (eń tar, eń keń) eni / boyı retinde
    shape_labels: tuple  # sol eki shek adamlar aytatuǵınday, mısalı ('4:3', '16:9')
    recommended: tuple  # (eni, boyı)
    recommended_label: str  # usınılatuǵın ólshemniń forması, mısalı '3:2'
    max_side: int  # saqlanǵan súwret saqlaytuǵın eń uzın tárep (common/images.py sonıǵa shekem kishireytedi)

    @property
    def shape_label(self):
        return f'{self.shape_labels[0]} to {self.shape_labels[1]}'


# Mehmanxana hám xona súwretleri: kartalar, galereya hám xona kartaları olardı 4:3 ten 16:9 ǵa shekem kórsetedi
HOTEL_PHOTO = ImageRule(1200, 800, (Fraction(4, 3), Fraction(16, 9)), ('4:3', '16:9'), (1600, 1067), '3:2', 1600)
ROOM_PHOTO = ImageRule(1200, 800, (Fraction(4, 3), Fraction(16, 9)), ('4:3', '16:9'), (1600, 1067), '3:2', 1600)
# Reklama karuseli telefonda 16:9 hám keń ekranda 16:5, ortasın kesedi
AD_BANNER = ImageRule(1600, 600, (Fraction(16, 9), Fraction(16, 5)), ('16:9', '16:5'), (1920, 720), '8:3', 2400)
# Bas bettiń "qayaqqa" kartaları 4:3
PLACE_PICTURE = ImageRule(800, 600, (Fraction(6, 5), Fraction(9, 5)), ('6:5', '9:5'), (1200, 900), '4:3', 1600)


def _shown_size(image):
    """Súwrettiń paydalanıwshı kóretuǵın eni hám boyı: jantayıp saqlanǵan telefon súwreti óz belgisi boyınsha burıladı."""
    width, height = image.size
    if image.getexif().get(ORIENTATION_TAG) in SIDEWAYS:
        return height, width
    return width, height


def _the_picture(file):
    """Haqıyqıy JPEG, PNG yamasa WebP tıń kórsetilgenindey (eni, boyı), júdá úlken bolsa 'dimensions', ol emes bolsa None."""
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
    except Exception:  # súwret emes, yamasa buzılǵan: Pillow kóp túrli qátelik kóteredi
        return None
    finally:
        file.seek(0)


def image_upload_error(file, rule):
    """`rule` ge sáykes kelmeytuǵın júklewdiń biykar etiw teksti (bet tilinde), yamasa saqlanatuǵın bolsa None."""
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
