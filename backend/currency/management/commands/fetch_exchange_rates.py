from django.core.management.base import BaseCommand

from currency import cbu


class Command(BaseCommand):
    help = 'Fetch today\'s CBU exchange rates now (same code as the scheduled task). Run once on first deploy.'

    def handle(self, *args, **options):
        for currency, row in cbu.fetch_and_store().items():
            if row is None:
                self.stdout.write(self.style.ERROR(f'{currency}: fetch failed, see exchange-rates status'))
            elif row.status == 'rejected':
                self.stdout.write(self.style.WARNING(f'{currency}: {row.rate} for {row.rate_date} {row.note}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'{currency}: {row.rate} UZS for {row.rate_date}'))
