"""Shrinks the hotel and room photos stored before uploads were shrunk (longest side 1600 px, no camera data)."""
import mimetypes

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand

from common.images import shrink_upload
from properties.models import PropertyPhoto, RoomPhoto


class Command(BaseCommand):
    help = 'Shrink stored hotel and room photos. Reports only; add --apply to change the files (same names).'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true', help='Rewrite the files that get smaller')

    def handle(self, *args, apply=False, **options):
        shrinkable = shrunk = missing = saved = 0
        for model in (PropertyPhoto, RoomPhoto):
            for photo in model.objects.exclude(photo='').iterator():
                storage, name = photo.photo.storage, photo.photo.name
                if not storage.exists(name):
                    missing += 1
                    continue
                with storage.open(name, 'rb') as handle:
                    original = handle.read()
                upload = SimpleUploadedFile(name, original, content_type=mimetypes.guess_type(name)[0] or '')
                smaller = shrink_upload(upload).read()
                if len(smaller) >= len(original):
                    continue
                shrinkable += 1
                if apply:
                    with open(storage.path(name), 'wb') as handle:
                        handle.write(smaller)
                    shrunk += 1
                    saved += len(original) - len(smaller)
        self.stdout.write(self._report(apply, shrinkable, shrunk, missing, saved))

    @staticmethod
    def _report(apply, shrinkable, shrunk, missing, saved):
        if apply:
            lines = [f'{shrunk} photos shrunk, {saved / 1_000_000:.1f} MB saved']
        else:
            lines = [f'{shrinkable} photos can be shrunk (run again with --apply)']
        if missing:
            lines.append(f'{missing} files missing on disk (skipped)')
        return '\n'.join(lines)
