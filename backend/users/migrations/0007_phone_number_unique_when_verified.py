from django.db import migrations, models
from django.db.models import Q


def clear_unverified_duplicates(apps, schema_editor):
    """
    Reverse step: the global unique constraint cannot return while several accounts
    still claim the same number, so claims without proof are cleared; verified
    holders keep their number.
    """
    User = apps.get_model('users', 'User')
    duplicated = (
        User.objects.exclude(phone_number__isnull=True)
        .values('phone_number')
        .annotate(holders=models.Count('id'))
        .filter(holders__gt=1)
        .values_list('phone_number', flat=True)
    )
    for number in list(duplicated):
        holders = list(User.objects.filter(phone_number=number).order_by('-phone_verified', 'id'))
        # Keep one holder: the verified one, otherwise the oldest account
        for user in holders[1:]:
            User.objects.filter(pk=user.pk).update(phone_number=None)


class Migration(migrations.Migration):
    """
    N-1: an unverified phone number is only a claim. Uniqueness now applies to VERIFIED
    numbers only, so someone who registers with another person's number cannot block
    its real owner. Reversible: the reverse step clears unproven duplicates first.
    """

    dependencies = [
        ('users', '0006_user_phone_number_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        # When reversing: runs after the new constraint is dropped, before the global unique returns
        migrations.RunPython(migrations.RunPython.noop, clear_unverified_duplicates),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(
                condition=Q(('phone_verified', True)),
                fields=('phone_number',),
                name='users_phone_unique_when_verified',
            ),
        ),
    ]
