"""What a hotel needs before guests can see it: a room, an active rate and a photo."""
from properties.models import PropertyPhoto, RatePlan, RoomType


def missing_for_listing(property):
    """Return the parts still missing, in the order the owner sets them up."""
    rooms = RoomType.objects.filter(property=property, is_deleted=False)
    rates = RatePlan.objects.filter(room_type__in=rooms, is_active=True, is_deleted=False)
    parts = (
        ('room', rooms),
        ('rate', rates),
        ('photo', PropertyPhoto.objects.filter(property=property, is_deleted=False)),
    )
    return [name for name, rows in parts if not rows.exists()]
