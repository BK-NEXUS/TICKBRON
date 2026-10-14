from rest_framework import serializers

from .models import Booking


class OwnBookingField(serializers.PrimaryKeyRelatedField):
    """
    A booking id that must belong to the caller.

    Someone else's booking and a booking that does not exist get the same answer, so the
    sequential ids cannot be used to count or probe other guests' bookings.
    """
    default_error_messages = {
        'does_not_exist': 'Booking not found.',
        'incorrect_type': 'Booking not found.',
    }

    def __init__(self, **kwargs):
        super().__init__(queryset=Booking.objects.all(), **kwargs)

    def get_queryset(self):
        return Booking.objects.filter(guest=self.context['request'].user)
