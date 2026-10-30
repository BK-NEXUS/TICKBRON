"""Switches off the two-step sign-in of one account (a lost phone and lost backup codes). Run on the server only."""
from django.core.management.base import BaseCommand, CommandError

from common.security_log import log_security_event
from users import two_factor
from users.models import User


class Command(BaseCommand):
    help = "Reset one account's two-step sign-in; it sets it up again at its next sign-in. Works for a super admin too."

    def add_arguments(self, parser):
        parser.add_argument('email', help='E-mail of the account')

    def handle(self, *args, email, **options):
        user = User.objects.filter(email__iexact=email.strip(), is_deleted=False).first()
        if user is None:
            raise CommandError(f'No account with the e-mail {email}.')
        if not user.two_factor_enabled:
            self.stdout.write('Two-step sign-in is not on for this account; nothing to reset.')
            return
        two_factor.reset(user)
        log_security_event('two_factor_reset', user=user, by='server_command')
        self.stdout.write(f'Two-step sign-in reset for {user.email}. The account is signed out everywhere.')
