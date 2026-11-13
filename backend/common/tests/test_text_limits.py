"""QA: mehmanlar hám mehmanxana iyeleri jazatuǵın erkin tekst maydanlarında uzınlıq shegi bar.

200 KB favorit jazbası qabıllandı (201), sebebi model baǵanası shekleusiz TextField.
"""
import pytest
from rest_framework.exceptions import ValidationError

from accounts.serializers import FavoriteCreateSerializer, FavoriteSerializer, ReviewCreateSerializer, ReviewSerializer
from partner.serializers import (
    PartnerDateInventorySerializer, PartnerRatePlanSerializer, PartnerRoomTypeSerializer,
)

CASES = [
    (FavoriteCreateSerializer, 'notes', 500),
    (FavoriteSerializer, 'notes', 500),
    (ReviewCreateSerializer, 'comment', 2000),
    (ReviewSerializer, 'comment', 2000),
    (PartnerRoomTypeSerializer, 'description', 2000),
    (PartnerRatePlanSerializer, 'description', 2000),
    (PartnerRatePlanSerializer, 'cancellation_policy', 2000),
    (PartnerDateInventorySerializer, 'notes', 500),
]


def accepts(serializer_class, field, length):
    """Maydannıń ózi usı uzınlıqtaǵı qatardı qabıllasa True (basqa maydanlar qatnaspaydı)."""
    try:
        serializer_class().fields[field].run_validation('x' * length)
    except ValidationError:
        return False
    return True


@pytest.mark.parametrize('serializer_class, field, limit', CASES, ids=[f'{c[0].__name__}.{c[1]}' for c in CASES])
def test_text_over_the_limit_is_refused(serializer_class, field, limit):
    assert not accepts(serializer_class, field, limit + 1)


@pytest.mark.parametrize('serializer_class, field, limit', CASES, ids=[f'{c[0].__name__}.{c[1]}' for c in CASES])
def test_text_at_the_limit_is_accepted(serializer_class, field, limit):
    assert accepts(serializer_class, field, limit)
