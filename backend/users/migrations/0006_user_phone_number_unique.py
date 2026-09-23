from collections import defaultdict

from django.db import migrations, models


def normalize_and_check_phone_numbers(apps, schema_editor):
    """
    Store blank phone numbers as NULL and refuse to continue on duplicates.

    Duplicates are not resolved automatically: deciding which account keeps a
    number is a manual call, so the migration stops and lists the user IDs.
    """
    User = apps.get_model('users', 'User')

    users_by_phone = defaultdict(list)
    for user in User.objects.exclude(phone_number__isnull=True).only('id', 'phone_number'):
        normalized = user.phone_number.strip() or None
        if normalized != user.phone_number:
            User.objects.filter(pk=user.pk).update(phone_number=normalized)
        if normalized:
            users_by_phone[normalized].append(user.pk)

    duplicates = [sorted(ids) for ids in users_by_phone.values() if len(ids) > 1]
    if duplicates:
        groups = '; '.join(', '.join(str(pk) for pk in ids) for ids in duplicates)
        raise RuntimeError(
            'Cannot make users.phone_number unique: '
            f'{len(duplicates)} phone number(s) are shared by multiple users. '
            f'User ID groups sharing a number: {groups}. '
            'Resolve these duplicates manually, then re-run migrate.'
        )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_preferred_contact_method_user_telegram_and_more'),
    ]

    operations = [
        migrations.RunPython(normalize_and_check_phone_numbers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True, unique=True),
        ),
    ]
