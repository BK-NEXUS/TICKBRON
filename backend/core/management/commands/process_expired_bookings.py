"""
Django management command to process expired bookings.

This command should be run periodically (e.g., via cron or Celery beat)
to clean up expired pending bookings and restore their inventory.
"""
import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from bookings.models import Booking


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process expired pending bookings and restore inventory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            help='Run without actually expiring bookings (for testing)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            dest='verbose',
            help='Show detailed output about processed bookings',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)

        # Find expired pending bookings
        expired_bookings = Booking.objects.filter(
            status='pending',
            expires_at__lt=timezone.now(),
            is_deleted=False
        )

        count = expired_bookings.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No expired bookings to process.'))
            return

        self.stdout.write(f'Found {count} expired booking(s) to process.')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run mode - no bookings will be expired.'))
            for booking in expired_bookings:
                self.stdout.write(
                    f'  - Booking {booking.confirmation_code} (ID: {booking.id}) '
                    f'expired at {booking.expires_at}'
                )
            return

        # Process expired bookings
        processed_count = 0
        failed_count = 0
        for booking in expired_bookings:
            try:
                booking.expire_booking()
                processed_count += 1
                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Expired booking {booking.confirmation_code} (ID: {booking.id})'
                        )
                    )
            except Exception as e:
                failed_count += 1
                logger.exception(f"Failed to expire booking {booking.pk}")
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to expire booking {booking.confirmation_code} (ID: {booking.id}): {str(e)}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {processed_count}/{count} expired booking(s).'
            )
        )

        # Non-zero exit status so cron/monitoring notices failures
        if failed_count:
            raise CommandError(f'{failed_count} expired booking(s) could not be processed.')
