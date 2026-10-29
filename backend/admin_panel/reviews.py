"""Staff moderation of guest reviews: a review is public only after the staff approves it."""
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.models import Review
from accounts.review_notices import tell_decision
from accounts.serializers import RATING_FIELDS, reviewer_label, stay_month
from admin_panel.models import AdminAccessLog
from admin_panel.views import IsSuperAdminOrStaff
from django.utils.translation import gettext as _

STATUSES = ('pending', 'approved', 'rejected')


class AdminReviewSerializer(serializers.ModelSerializer):
    """A review as the staff sees it: the reviewer's address is shown here, never on the public list."""
    reviewer = serializers.SerializerMethodField()
    reviewer_email = serializers.EmailField(source='user.email', read_only=True)
    property_name = serializers.CharField(source='property.display_name', read_only=True)
    stay_month = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ['id', 'property', 'property_name', 'reviewer', 'reviewer_email', 'stay_month', *RATING_FIELDS,
                  'title', 'comment', 'status', 'created_at', 'reviewed_at']

    def get_reviewer(self, review):
        return reviewer_label(review.user)

    def get_stay_month(self, review):
        return stay_month(review)


def _queryset():
    return Review.objects.filter(is_deleted=False).select_related('user', 'property__owner', 'booking')


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_reviews(request):
    """Reviews by status (`?status=pending|approved|rejected`, default pending), oldest waiting first."""
    wanted = request.query_params.get('status', 'pending')
    if wanted not in STATUSES:
        return Response({'status': [_('Choose one of: pending, approved, rejected.')]},
                        status=status.HTTP_400_BAD_REQUEST)
    ordering = ('created_at', 'id') if wanted == 'pending' else ('-created_at', '-id')
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(_queryset().filter(status=wanted).order_by(*ordering), request)
    return paginator.get_paginated_response(AdminReviewSerializer(page, many=True).data)


def _decide(request, review_id, decision):
    review = _queryset().filter(pk=review_id).first()
    if review is None:
        return Response({'detail': _('Not found.')}, status=status.HTTP_404_NOT_FOUND)
    changed = review.status != decision
    review.status = decision
    review.reviewed_at = timezone.now()
    review.save(update_fields=['status', 'reviewed_at', 'updated_at'])
    if changed:
        tell_decision(review, approved=decision == 'approved')
    AdminAccessLog.record(request.user, f'review_{"approve" if decision == "approved" else "reject"}',
                          target_user_id=review.user_id, details={'object_id': review.id, 'property_id': review.property_id})
    return Response(AdminReviewSerializer(review).data)


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_review_approve(request, review_id):
    """Show the review on the hotel page and count it in the hotel's scores."""
    return _decide(request, review_id, 'approved')


@extend_schema(request=None, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_review_reject(request, review_id):
    """Keep the review off the hotel page and out of its scores."""
    return _decide(request, review_id, 'rejected')
