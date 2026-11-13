from rest_framework import serializers

from .models import Booking


class OwnBookingField(serializers.PrimaryKeyRelatedField):
    """
    Shaqırıwshıǵa tiyisli bolıwı kerek bron id si.

    Basqa birewdiń broni hám joq bron birdey juwap aladı, sol sebepli
    izbe-iz id lerdi basqa mehmanlardıń bronların sanaw yamasa izlew ushın paydalanıp bolmaydı.
    """
    default_error_messages = {
        'does_not_exist': 'Booking not found.',
        'incorrect_type': 'Booking not found.',
    }

    def __init__(self, **kwargs):
        super().__init__(queryset=Booking.objects.all(), **kwargs)

    def get_queryset(self):
        return Booking.objects.filter(guest=self.context['request'].user)
