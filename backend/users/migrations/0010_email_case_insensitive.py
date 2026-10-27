from django.db import migrations, models
from django.db.models.functions import Lower


def lower_case_addresses(apps, schema_editor):
    """Store every address in lower case. Stops, changing nothing, when two accounts differ only by capitals."""
    User = apps.get_model('users', 'User')
    seen = {}
    for pk, email in User.objects.order_by('id').values_list('id', 'email'):
        seen.setdefault((email or '').strip().lower(), []).append(email)
    clashes = sorted(address for address, spellings in seen.items() if len(spellings) > 1)
    if clashes:
        raise RuntimeError(
            'Cannot make e-mail addresses case-insensitive: these addresses exist in more than one spelling: '
            + ', '.join(clashes) + '. Merge or delete the extra accounts, then run migrate again.')
    for user in User.objects.exclude(email=Lower('email')):
        User.objects.filter(pk=user.pk).update(email=user.email.strip().lower())


class Migration(migrations.Migration):
    """
    One account per mailbox, whatever the capitals (QA finding F2). Addresses are lower-cased and a unique
    constraint on lower(email) keeps them so. Reversible: the constraint goes; the original capitals of
    addresses that were lower-cased are not restored (they were the same address).
    """

    dependencies = [
        ('users', '0009_drop_sms_login_columns'),
    ]

    operations = [
        migrations.RunPython(lower_case_addresses, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(Lower('email'), name='users_email_lower_unique'),
        ),
    ]
