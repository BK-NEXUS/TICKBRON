"""users app ınıń Celery task ları."""
from celery import shared_task

from users.models import User
from users.password_reset import can_reset_password, send_reset_email


@shared_task
def send_password_reset_email(user_id):
    """Tiklew siltemesin e-mail ge jiberiw. Soraw bul isleniwden aldın juwap aladı, sol sebepli sekin e-mail server hesh
    nárse kórsetpeydi."""
    user = User.objects.filter(pk=user_id).first()
    if user is not None and can_reset_password(user):
        send_reset_email(user)
