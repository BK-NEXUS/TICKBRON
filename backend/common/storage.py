"""
TICKBRON media islewi ushın storage abstrakciyası.

Bul modul túrli ortalıqlarda isleytuǵın birden-bir storage interfeysin usınadı:
- Development ushın jergilikli fayl sisteması
- Staging/production ushın S3 menen sáykes storage
"""
import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext as _


@deconstructible
class TickBronStorage:
    """
    TICKBRON media fayllar ushın birden-bir storage abstrakciyası.

    Bul klas túrli ortalıqlarda (local, staging, production) media saqlawdıń birdey
    interfeysin beredi, sonıń menen birge ortalıqqa tiyisli
    ámelge asırıwlarǵa ruxsat beredi.
    """

    def __init__(self):
        self._storage_backend = self._get_storage_backend()

    def _get_storage_backend(self):
        """
        Ortalıqqa qarap tiyisli storage backend ti anıqlaw.

        Qaytaradı:
            Storage backend nusqası (FileSystemStorage, S3Storage hám t.b.)
        """
        storage_type = getattr(settings, 'STORAGE_TYPE', 'local')

        if storage_type == 'local':
            return LocalStorage()
        elif storage_type == 's3':
            return S3Storage()
        else:
            # Ádetde jergilikli storage
            return LocalStorage()

    def url(self, name):
        """Berilgen fayl atı ushın URL alıw."""
        return self._storage_backend.url(name)

    def path(self, name):
        """Berilgen fayl atı ushın jergilikli fayl sisteması jolın alıw."""
        return self._storage_backend.path(name)

    def exists(self, name):
        """Fayldıń bar-joqlıǵın tekseriw."""
        return self._storage_backend.exists(name)

    def save(self, name, content, max_length=None):
        """Fayldı saqlaw."""
        return self._storage_backend.save(name, content, max_length=max_length)

    def delete(self, name):
        """Fayldı óshiriw."""
        return self._storage_backend.delete(name)

    def listdir(self, path):
        """Papka mazmunın dizimlew."""
        return self._storage_backend.listdir(path)

    def size(self, name):
        """Fayl ólshemin baytlarda alıw."""
        return self._storage_backend.size(name)

    def get_available_name(self, name, max_length=None):
        """Berilgen at ushın bos fayl atın alıw."""
        return self._storage_backend.get_available_name(name, max_length)

    def generate_filename(self, filename):
        """Berilgen fayl atı ushın unikal at jaratıw."""
        return self._storage_backend.generate_filename(filename)


class LocalStorage(FileSystemStorage):
    """
    Development ushın jergilikli fayl sisteması storage ı.

    Bul storage backend fayllardı jergilikli fayl sistemasında saqlaydı hám development
    hám test ortalıqları ushın jaraydı.
    """

    def __init__(self):
        location = getattr(settings, 'MEDIA_ROOT', os.path.join(settings.BASE_DIR, 'media'))
        base_url = getattr(settings, 'MEDIA_URL', '/media/')

        super().__init__(
            location=location,
            base_url=base_url
        )

    def get_available_name(self, name, max_length=None):
        """
        Fayldıń dáslepki keńeytpesin saqlap, bos fayl atın alıw.

        Bul metod júklengen fayllar dáslepki keńeytpesin saqlawın hám
        at tuwra kelmewin támiyinleydi.
        """
        # Atın tiykar hám keńeytpege bóliw
        base, ext = os.path.splitext(name)

        # At aldınan bos bolsa, qaytarıw
        if not self.exists(name):
            return name

        # Bolmasa, unikal etiw ushın sanaǵısh qosıw
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            if not self.exists(new_name):
                return new_name
            counter += 1


class S3Storage:
    """
    Staging/production ushın S3 menen sáykes storage.

    Bul storage backend production ortalıqları ushın S3 menen sáykes obyekt storage ın (AWS S3, MinIO hám t.b.)
    paydalanadı. Waqtınsha ámelge asırıw (placeholder) - boto3 kerek.

    Eskertiw: Bul placeholder. Production ta durıs S3 sazlaması menen
    django-storages paydalanıń.
    """

    def __init__(self):
        # S3 sazlaması ushın placeholder
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'tickbron-media')
        self.access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', '')
        self.secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', '')
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        self.custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)

    def url(self, name):
        """Berilgen fayl atı ushın URL alıw."""
        if self.custom_domain:
            return f"https://{self.custom_domain}/{name}"
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{name}"

    def path(self, name):
        """S3 storage ında jergilikli jollar joq."""
        raise NotImplementedError("S3 storage doesn't support local paths")

    def exists(self, name):
        """Fayldıń S3 te bar-joqlıǵın tekseriw."""
        # Placeholder ámelge asırıw
        # Production ta bul S3 ti tekseriw ushın boto3 paydalanar edi
        return False

    def save(self, name, content, max_length=None):
        """Fayldı S3 ke saqlaw."""
        # Placeholder ámelge asırıw
        # Production ta bul S3 ke júklew ushın boto3 paydalanar edi
        raise NotImplementedError("S3 storage not yet implemented")

    def delete(self, name):
        """Fayldı S3 ten óshiriw."""
        # Placeholder ámelge asırıw
        # Production ta bul S3 ten óshiriw ushın boto3 paydalanar edi
        raise NotImplementedError("S3 storage not yet implemented")

    def listdir(self, path):
        """S3 papkasınıń mazmunın dizimlew."""
        # Placeholder ámelge asırıw
        # Production ta bul S3 obyektlerin dizimlew ushın boto3 paydalanar edi
        raise NotImplementedError("S3 storage not yet implemented")

    def size(self, name):
        """S3 ten fayl ólshemin alıw."""
        # Placeholder ámelge asırıw
        # Production ta bul S3 obyekt ólshemin alıw ushın boto3 paydalanar edi
        raise NotImplementedError("S3 storage not yet implemented")

    def get_available_name(self, name, max_length=None):
        """S3 ushın bos fayl atın alıw."""
        # S3 atawdı basqasha isleydi, biraq biz uqsas logikanı paydalanamız
        base, ext = os.path.splitext(name)
        counter = 1
        while True:
            new_name = f"{base}_{counter}{ext}"
            if not self.exists(new_name):
                return new_name
            counter += 1

    def generate_filename(self, filename):
        """S3 ushın unikal fayl atın jaratıw."""
        return self.get_available_name(filename)


def get_media_upload_path(instance, filename):
    """
    Mehmanxana media fayllarınıń júklew jolın jaratıw.

    Argumentler:
        instance: Model nusqası (PropertyPhoto)
        filename: Dáslepki fayl atı

    Qaytaradı:
        Fayldı saqlaw ushın jol qatarı
    """
    if hasattr(instance, 'property'):
        property_id = instance.property.id
    elif hasattr(instance, 'room_type'):
        property_id = instance.room_type.property_id
    else:
        # Mehmanxana ele belgilenbegen bolsa zapas jol
        property_id = 'temp'

    # Jol jaratıw: properties/{property_id}/photos/{filename}
    return f'properties/{property_id}/photos/{filename}'


def validate_image_file(file):
    """
    Júklengen súwret fayllardı tekseriw.

    Argumentler:
        file: UploadedFile nusqası

    Qaytaradı:
        tuple (is_valid, error_message)
    """

    # Fayl ólshemin tekseriw (eń kóbi 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size > max_size:
        return False, _('File size exceeds maximum allowed size of %(size)sMB') % {'size': max_size / (1024*1024)}

    # Fayl keńeytpesin tekseriw
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in allowed_extensions:
        return False, _('File type %(ext)s is not allowed. Allowed types: %(types)s') % {
            'ext': file_ext, 'types': ', '.join(allowed_extensions)}

    # Fayldıń haqıyqatında súwret ekenin tekseriw (ápiwayı tekseriw)
    if not file.content_type.startswith('image/'):
        return False, _('File content type %(type)s is not a valid image') % {'type': file.content_type}

    return True, None
