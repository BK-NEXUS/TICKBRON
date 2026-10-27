from decimal import Decimal

from properties.models import PropertyPhoto, RatePlan, RoomType


def add_room(hotel):
    return RoomType.objects.create(
        property=hotel, name='Std', slug='std', base_occupancy=1, max_occupancy=2,
        base_price=Decimal('50'), currency='USD', total_rooms=1,
    )


def add_rate(room):
    return RatePlan.objects.create(
        room_type=room, name='Flex', slug='flex', rate_type='standard', base_price=Decimal('50'),
        currency='USD', min_nights=1, is_active=True,
    )


def add_photo(hotel):
    return PropertyPhoto.objects.create(property=hotel, photo='properties/p.jpg')


def make_listable(hotel):
    add_rate(add_room(hotel))
    add_photo(hotel)
