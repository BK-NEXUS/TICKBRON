from collections import defaultdict

from django.db import migrations, models
from django.db.models.functions import Lower


def lowercase_emails_after_duplicate_check(apps, schema_editor):
    """
    Refuse to continue when two users differ only by letter case, then lowercase all emails.

    Which account keeps the address is a manual call, so the migration stops
    and lists the user IDs. The reverse keeps the lowercased addresses.
    """
    User = apps.get_model('users', 'User')

    ids_by_email = defaultdict(list)
    for pk, email in User.objects.values_list('pk', 'email'):
        ids_by_email[email.strip().lower()].append(pk)

    duplicates = [sorted(ids) for ids in ids_by_email.values() if len(ids) > 1]
    if duplicates:
        groups = '; '.join(', '.join(str(pk) for pk in ids) for ids in duplicates)
        raise RuntimeError(
            'Cannot make users.email case-insensitive unique: '
            f'{len(duplicates)} address(es) differ only by letter case. '
            f'User ID groups sharing an address: {groups}. '
            'Resolve these duplicates manually, then re-run migrate.'
        )

    for email, ids in ids_by_email.items():
        User.objects.filter(pk=ids[0]).update(email=email)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_phone_number_unique'),
    ]

    operations = [
        migrations.RunPython(lowercase_emails_after_duplicate_check, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(Lower('email'), name='users_email_lower_unique'),
        ),
    ]
