"""
TICKBRON database in tayarlaw ushın Django management command ı.

Paydalanıw: python manage.py init_db
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Initialize TICKBRON database with migrations and initial data'

    def handle(self, *args, **options):
        """Database di tayarlawdı orınlaw."""
        self.stdout.write('Initializing TICKBRON database...')

        try:
            # Migration lardı isletiw
            self.stdout.write('Running migrations...')
            call_command('migrate', '--run-syncdb', verbosity=2)
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed'))

            # Kerek bolsa dáslepki maǵlıwmat jaratıw (keyingi checkpoint lar ushın)
            # Dáslepki maǵlıwmat talapları payda bolǵanda bul toltırıladı

            self.stdout.write(self.style.SUCCESS('Database initialization completed'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database initialization failed: {str(e)}'))
            raise
