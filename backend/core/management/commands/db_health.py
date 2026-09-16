"""
Django management command for database health checks.

Usage: python manage.py db_health
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Check database connection health and status'

    def handle(self, *args, **options):
        """Execute the database health check."""
        self.stdout.write('Checking database health...')
        
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                
                if result and result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Database connection failed'))
                    return
            
            # Display database information
            db_name = connection.settings_dict['NAME']
            db_engine = connection.settings_dict['ENGINE']
            
            self.stdout.write(f'Database Engine: {db_engine}')
            self.stdout.write(f'Database Name: {db_name}')
            
            # Check if PostgreSQL
            if 'postgresql' in db_engine:
                with connection.cursor() as cursor:
                    cursor.execute('SELECT version()')
                    version = cursor.fetchone()[0]
                    self.stdout.write(f'PostgreSQL Version: {version}')
            
            self.stdout.write(self.style.SUCCESS('Database health check completed'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database health check failed: {str(e)}'))
            raise
