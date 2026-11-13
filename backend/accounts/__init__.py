"""
TICKBRON ushın accounts app ı: favorit ler, sharhlar, bildiriwler (notifications) hám akkaunt tariyxı.
"""


def notify(user, code, params, booking=None):
    """Ilova ishindegi bildiriw (in-app notification) jasaw (qarań: accounts.notifications.notify)."""
    from .notifications import notify as _notify
    return _notify(user, code, params, booking=booking)
