"""Mehmann sharhı haqqındaǵı xabarlandırıwlar: staff tıń qararı (mehmannan hám iyege) hám iyeniń juwabı (mehmanǵa)."""
import logging

from accounts import notify

logger = logging.getLogger(__name__)


def _params(review):
    return {'review_id': review.id, 'property_id': review.property_id}


def _tell(user, code, review):
    # Saqlanbaǵan xabarlandırıw ózin keltirip shıǵarǵan qarar yamasa juwaptı hesh qashan biykar etpewi kerek
    try:
        notify(user, code, _params(review))
    except Exception:
        logger.exception('Could not store the %s notice of review %s', code, review.pk)


def tell_decision(review, approved):
    """Mehmann qarardı biledi; mehmanxana iyesi jańa ashıq sharh haqqında biledi."""
    if approved:
        _tell(review.user, 'review_approved', review)
        _tell(review.property.owner, 'new_review', review)
    else:
        _tell(review.user, 'review_rejected', review)


def tell_reply(review):
    _tell(review.user, 'review_reply', review)
