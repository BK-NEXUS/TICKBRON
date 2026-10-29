"""Notices about a guest review: the decision of the staff (guest, owner) and the owner's answer (guest)."""
import logging

from accounts import notify

logger = logging.getLogger(__name__)


def _params(review):
    return {'review_id': review.id, 'property_id': review.property_id}


def _tell(user, code, review):
    # A notice that cannot be stored must never undo the decision or the answer that caused it
    try:
        notify(user, code, _params(review))
    except Exception:
        logger.exception('Could not store the %s notice of review %s', code, review.pk)


def tell_decision(review, approved):
    """The guest learns the decision; the hotel owner learns about a new public review."""
    if approved:
        _tell(review.user, 'review_approved', review)
        _tell(review.property.owner, 'new_review', review)
    else:
        _tell(review.user, 'review_rejected', review)


def tell_reply(review):
    _tell(review.user, 'review_reply', review)
