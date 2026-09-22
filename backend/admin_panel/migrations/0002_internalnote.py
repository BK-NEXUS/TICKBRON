# Generated migration for InternalNote model
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    dependencies = [
        ('admin_panel', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InternalNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False, db_index=True)),
                ('deleted_at', models.DateTimeField(null=True, blank=True)),
                ('note', models.TextField(help_text='Internal note content', validators=[django.core.validators.MinLengthValidator(1)])),
                ('author', models.ForeignKey(help_text='Staff member who wrote this note', null=True, on_delete=models.deletion.SET_NULL, related_name='authored_notes', to='users.user')),
                ('customer', models.ForeignKey(db_index=True, help_text='Customer this note is about', on_delete=models.deletion.CASCADE, related_name='internal_notes', to='users.user')),
            ],
            options={
                'verbose_name': 'Internal Note',
                'verbose_name_plural': 'Internal Notes',
                'db_table': 'internal_notes',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['customer', 'created_at'], name='admin_panel_customer_created_idx'),
                    models.Index(fields=['author', 'created_at'], name='admin_panel_author_created_idx'),
                ],
            },
        ),
    ]