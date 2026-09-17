"""
Migration to add search optimization indexes.

This migration adds database indexes to improve search performance.
Using Django's AddIndex for cross-database compatibility.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('properties', '0004_roomtype_roomphoto_roomamenity_rateplan_and_more'),
    ]

    operations = [
        # Add composite index for property status and price filtering
        migrations.AddIndex(
            model_name='property',
            index=models.Index(
                fields=['status', 'base_price'],
                name='idx_property_status_price'
            )
        ),
        
        # Add composite index for location search
        migrations.AddIndex(
            model_name='property',
            index=models.Index(
                fields=['city', 'country'],
                name='idx_property_location'
            )
        ),
        
        # Add index for guest capacity filtering
        migrations.AddIndex(
            model_name='property',
            index=models.Index(
                fields=['max_guests'],
                name='idx_property_guests'
            )
        ),
        
        # Add index for property type filtering
        migrations.AddIndex(
            model_name='property',
            index=models.Index(
                fields=['property_type_id', 'status'],
                name='idx_property_type_status'
            )
        ),
        
        # Add index for amenity search optimization
        migrations.AddIndex(
            model_name='propertyamenity',
            index=models.Index(
                fields=['property', 'amenity', 'is_available'],
                name='idx_property_amenity_available'
            )
        ),
    ]