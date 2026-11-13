"""
Database jaǵdayın tekseriw ushın Django management command ı.

Paydalanıw: python manage.py db_health
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Check database connection health and status'

    def handle(self, *args, **options):
        """Database jaǵdayın tekseriwdi orınlaw."""
        self.stdout.write('Checking database health...')

        try:
            # Database ulanıwın tekseriw
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()

                if result and result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Database connection failed'))
                    return

            # Database maǵlıwmatın kórsetiw
            db_name = connection.settings_dict['NAME']
            db_engine = connection.settings_dict['ENGINE']

            self.stdout.write(f'Database Engine: {db_engine}')
            self.stdout.write(f'Database Name: {db_name}')

            # PostgreSQL ekenin tekseriw
            if 'postgresql' in db_engine:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT version()')
                    version = cursor.fetchone()[0]
                    self.stdout.write(f'PostgreSQL Version: {version}')

            self.stdout.write(self.style.SUCCESS('Database health check completed'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database health check failed: {str(e)}'))
            raise
