"""Hotel owners read the approved reviews of their own hotels and answer them in public."""
from django.utils import timezone
from django.utils.translation import gettext as _
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.models import Review
from accounts.review_notices import tell_reply
from accounts.serializers import RATING_FIELDS, reviewer_label, stay_month
from common.validators import validate_free_text
from partner.views import IsHotelOwner

REPLY_MAX_LENGTH = 1000


class OwnerReviewSerializer(serializers.ModelSerializer):
    """A public review as its hotel's owner sees it; the reviewer is "Aziz K.", never an address."""
    reviewer = serializers.SerializerMethodField()
    stay_month = serializers.SerializerMethodField()
    property_name = serializers.CharField(source='property.display_name', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'property', 'property_name', 'reviewer', 'stay_month', *RATING_FIELDS, 'title', 'comment',
                  'created_at', 'owner_reply', 'replied_at']

    def get_reviewer(self, review):
        return reviewer_label(review.user)

    def get_stay_month(self, review):
        return stay_month(review)


class ReplySerializer(serializers.Serializer):
    text = serializers.CharField(max_length=REPLY_MAX_LENGTH, trim_whitespace=True, validators=[validate_free_text])


def _own_public_reviews(user):
    return Review.objects.filter(property__owner=user, status='approved', is_deleted=False) \
        .select_related('user', 'property', 'booking')


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsHotelOwner])
def partner_reviews(request):
    """The approved reviews of the owner's hotels, newest first (`?property=<id>` for one hotel)."""
    reviews = _own_public_reviews(request.user)
    hotel = request.query_params.get('property')
    if hotel and hotel.isdigit():
        reviews = reviews.filter(property_id=int(hotel))
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(reviews.order_by('-created_at', '-id'), request)
    return paginator.get_paginated_response(OwnerReviewSerializer(page, many=True).data)


@extend_schema(request=ReplySerializer, responses=OpenApiTypes.OBJECT)
@api_view(['POST', 'DELETE'])
@permission_classes([IsHotelOwner])
def partner_review_reply(request, review_id):
    """POST {text}: write or replace the answer (the guest is told about the first one). DELETE: take it back."""
    review = _own_public_reviews(request.user).filter(pk=review_id).first()
    if review is None:
        return Response({'detail': _('Not found.')}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'DELETE':
        review.owner_reply, review.replied_at = '', None
        review.save(update_fields=['owner_reply', 'replied_at', 'updated_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)
    serializer = ReplySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    first_answer = not review.owner_reply
    review.owner_reply, review.replied_at = serializer.validated_data['text'], timezone.now()
    review.save(update_fields=['owner_reply', 'replied_at', 'updated_at'])
    if first_answer:
        tell_reply(review)
    return Response(OwnerReviewSerializer(review).data)
