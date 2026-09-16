"""
Django management command for initializing TICKBRON database.

Usage: python manage.py init_db
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Initialize TICKBRON database with migrations and initial data'

    def handle(self, *args, **options):
        """Execute database initialization."""
        self.stdout.write('Initializing TICKBRON database...')
        
        try:
            # Run migrations
            self.stdout.write('Running migrations...')
            call_command('migrate', '--run-syncdb', verbosity=2)
            self.stdout.write(self.style.SUCCESS('✓ Migrations completed'))
            
            # Create initial data if needed (for future checkpoints)
            # This will be populated when we have initial data requirements
            
            self.stdout.write(self.style.SUCCESS('Database initialization completed'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database initialization failed: {str(e)}'))
            raise
