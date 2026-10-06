"""
Accounts app for TICKBRON - favorites, reviews, notifications, and account history.
"""


def notify(user, code, params, booking=None):
    """Create an in-app notification (see accounts.notifications.notify)."""
    from .notifications import notify as _notify
    return _notify(user, code, params, booking=booking)
