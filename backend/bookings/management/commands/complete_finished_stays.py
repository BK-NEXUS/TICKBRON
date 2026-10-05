"""
python manage.py complete_finished_stays [--dry-run]

One-off (and manual) run of the nightly auto-completion (R12): confirmed bookings
whose check-out date is before the business date become completed. The counts are
printed before anything changes; --dry-run only prints them.
"""
from django.core.management.base import BaseCommand

from bookings.completion import complete_finished_stays, finished_stays
from common.dates import business_today


class Command(BaseCommand):
    help = 'Complete confirmed bookings whose check-out date has passed (business date, Asia/Tashkent).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Print the counts and change nothing.')

    def handle(self, *args, **options):
        today = business_today()
        self.stdout.write(f'business date: {today.isoformat()}')
        self.stdout.write(f'eligible: {finished_stays(today).count()}')
        if options['dry_run']:
            self.stdout.write('Dry run: nothing changed.')
            return
        result = complete_finished_stays(trigger='command')
        self.stdout.write(f"changed: {result['changed']}")
        self.stdout.write(f"failed: {result['failed']}")
        if result['failed']:
            self.stderr.write('Some bookings could not be completed; see the log (booking ids only).')
