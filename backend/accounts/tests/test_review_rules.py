"""
Review integrity rules (audit #20).

A review needs the reviewer's own completed booking and must be for that
booking's property. One review per booking. booking/property cannot be changed
after creation, and editing an approved review sends it back to moderation.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import Review
from bookings.models import Booking
from properties.models import Property, PropertyType
from users.models import User

REVIEWS_URL = '/api/v1/me/reviews/'


class ReviewRulesTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='guest@example.com', password='testpass123')
        self.other_user = User.objects.create_user(email='other@example.com', password='testpass123')
        self.client.force_authenticate(user=self.user)

        property_type = PropertyType.objects.create(name='Apartment', slug='apartment')
        self.property = self._make_property(property_type, 'City A')
        self.other_property = self._make_property(property_type, 'City B')

        self.booking = self._make_booking(self.user, self.property, '2024-01-01', '2024-01-05')

    def _make_property(self, property_type, city):
        return Property.objects.create(
            owner=self.other_user, property_type=property_type, status='active',
            max_guests=4, bedrooms=2, bathrooms=1, address_line1='1 Street',
            city=city, country='Country', base_price=100.00, currency='USD',
        )

    def _make_booking(self, guest, prop, check_in, check_out, booking_status='completed'):
        return Booking.objects.create(
            guest=guest, property=prop, check_in=check_in, check_out=check_out,
            number_of_nights=4, guest_count=2, total_price=400.00, currency='USD',
            status=booking_status,
        )

    def _payload(self, **overrides):
        data = {
            'property': self.property.id,
            'booking': self.booking.id,
            'overall_rating': 5,
            'title': 'Great stay',
            'comment': 'Nice place',
        }
        data.update(overrides)
        return data


class ReviewCreateRulesTest(ReviewRulesTestBase):
    def test_valid_review_is_created_pending(self):
        response = self.client.post(REVIEWS_URL, self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = Review.objects.get()
        self.assertEqual(review.booking, self.booking)
        self.assertEqual(review.status, 'pending')

    def test_review_without_booking_is_rejected(self):
        data = self._payload()
        del data['booking']
        response = self.client.post(REVIEWS_URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_review_with_null_booking_is_rejected(self):
        response = self.client.post(REVIEWS_URL, self._payload(booking=None), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_review_for_someone_elses_booking_is_rejected(self):
        foreign = self._make_booking(self.other_user, self.property, '2024-02-01', '2024-02-05')
        response = self.client.post(REVIEWS_URL, self._payload(booking=foreign.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_review_for_unfinished_booking_is_rejected(self):
        confirmed = self._make_booking(
            self.user, self.property, '2024-03-01', '2024-03-05', booking_status='confirmed'
        )
        response = self.client.post(REVIEWS_URL, self._payload(booking=confirmed.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_review_for_a_different_property_is_rejected(self):
        response = self.client.post(
            REVIEWS_URL, self._payload(property=self.other_property.id), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_second_review_for_same_booking_is_rejected(self):
        first = self.client.post(REVIEWS_URL, self._payload(), format='json')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)

        second = self.client.post(REVIEWS_URL, self._payload(title='Again'), format='json')
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)

    def test_soft_deleted_review_still_blocks_second_review(self):
        review = Review.objects.create(
            user=self.user, property=self.property, booking=self.booking, overall_rating=4
        )
        review.soft_delete()

        response = self.client.post(REVIEWS_URL, self._payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)


class ReviewUpdateRulesTest(ReviewRulesTestBase):
    def setUp(self):
        super().setUp()
        self.review = Review.objects.create(
            user=self.user, property=self.property, booking=self.booking,
            overall_rating=5, status='approved',
        )
        self.url = f'{REVIEWS_URL}{self.review.id}/'

    def test_patch_cannot_move_review_to_another_booking_or_property(self):
        other_booking = self._make_booking(self.user, self.other_property, '2024-04-01', '2024-04-05')
        response = self.client.patch(
            self.url,
            {'booking': other_booking.id, 'property': self.other_property.id},
            format='json',
        )
        self.assertIn(response.status_code, (status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST))
        self.review.refresh_from_db()
        self.assertEqual(self.review.booking_id, self.booking.id)
        self.assertEqual(self.review.property_id, self.property.id)

    def test_editing_approved_review_returns_it_to_pending(self):
        self.assertIsNotNone(self.review.reviewed_at)
        response = self.client.patch(self.url, {'comment': 'Edited'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.comment, 'Edited')
        self.assertEqual(self.review.status, 'pending')
        self.assertIsNone(self.review.reviewed_at)

    def test_edited_review_drops_out_of_property_scores(self):
        scores_url = f'{REVIEWS_URL}property_scores/?property_id={self.property.id}'
        self.assertEqual(self.client.get(scores_url).data['total_reviews'], 1)

        self.client.patch(self.url, {'overall_rating': 1}, format='json')

        self.assertEqual(self.client.get(scores_url).data['total_reviews'], 0)


class EligiblePropertiesTest(ReviewRulesTestBase):
    URL = f'{REVIEWS_URL}eligible_properties/'

    def test_each_unreviewed_completed_booking_is_listed(self):
        second = self._make_booking(self.user, self.property, '2024-06-01', '2024-06-05')

        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        booking_ids = {item['booking_id'] for item in response.data['eligible_properties']}
        self.assertEqual(booking_ids, {self.booking.id, second.id})

    def test_reviewing_one_booking_keeps_other_booking_of_same_property(self):
        second = self._make_booking(self.user, self.property, '2024-06-01', '2024-06-05')
        Review.objects.create(
            user=self.user, property=self.property, booking=self.booking, overall_rating=5
        )

        response = self.client.get(self.URL)
        booking_ids = [item['booking_id'] for item in response.data['eligible_properties']]
        self.assertEqual(booking_ids, [second.id])

    def test_soft_deleted_review_still_counts_as_reviewed(self):
        review = Review.objects.create(
            user=self.user, property=self.property, booking=self.booking, overall_rating=5
        )
        review.soft_delete()

        response = self.client.get(self.URL)
        self.assertEqual(response.data['eligible_properties'], [])

    def test_unfinished_and_foreign_bookings_are_not_listed(self):
        self._make_booking(self.user, self.property, '2024-07-01', '2024-07-05', booking_status='confirmed')
        self._make_booking(self.other_user, self.property, '2024-08-01', '2024-08-05')

        response = self.client.get(self.URL)
        booking_ids = [item['booking_id'] for item in response.data['eligible_properties']]
        self.assertEqual(booking_ids, [self.booking.id])
