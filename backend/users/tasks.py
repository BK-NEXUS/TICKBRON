"""Celery tasks of the users app."""
from celery import shared_task

from users.models import User
from users.password_reset import can_reset_password, send_reset_email


@shared_task
def send_password_reset_email(user_id):
    """Mail the reset link. A request is answered before this runs, so a slow mail server shows nothing."""
    user = User.objects.filter(pk=user_id).first()
    if user is not None and can_reset_password(user):
        send_reset_email(user)
