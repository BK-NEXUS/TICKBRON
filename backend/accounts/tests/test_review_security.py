"""
Sharhlar qawipsizligi (SECURITY_FINDINGS F1): staff /me/reviews/ arqalı basqa adamnıń sharhın ózgertiw
almaydı, sharh óshirilgende tek soft-delete boladı, biykarlanǵan sharh qayta moderation ǵa túspeydi,
mehmanxana iyesi óz mehmanxanasına sharh jaza almaydı, title/comment ta markup joq.
"""
from rest_framework import status

from accounts.models import Review
from accounts.tests.test_review_rules import REVIEWS_URL, ReviewRulesTestBase
from users.models import User


class StaffCannotTouchGuestReviewsTest(ReviewRulesTestBase):
    def setUp(self):
        super().setUp()
        self.review = Review.objects.create(
            user=self.user, property=self.property, booking=self.booking,
            overall_rating=4, title='Fine', comment='Ok', status='approved',
        )
        self.staff = User.objects.create_user(email='staff@example.com', password='x', is_staff=True)
        self.client.force_authenticate(user=self.staff)

    def test_staff_cannot_patch_a_guest_review(self):
        response = self.client.patch(f'{REVIEWS_URL}{self.review.id}/', {'comment': 'hacked'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.review.refresh_from_db()
        self.assertEqual(self.review.comment, 'Ok')

    def test_staff_cannot_delete_a_guest_review(self):
        response = self.client.delete(f'{REVIEWS_URL}{self.review.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(Review.objects.get(pk=self.review.pk).is_deleted)

    def test_staff_list_shows_only_own_reviews(self):
        response = self.client.get(REVIEWS_URL)
        self.assertEqual(response.data['count'], 0)


class OwnReviewLifecycleTest(ReviewRulesTestBase):
    def setUp(self):
        super().setUp()
        self.review = Review.objects.create(
            user=self.user, property=self.property, booking=self.booking,
            overall_rating=4, title='Fine', comment='Ok', status='approved',
        )

    def test_delete_keeps_the_row_so_the_booking_cannot_be_reviewed_again(self):
        response = self.client.delete(f'{REVIEWS_URL}{self.review.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(Review.objects.get(pk=self.review.pk).is_deleted)
        again = self.client.post(REVIEWS_URL, self._payload(), format='json')
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Review.objects.count(), 1)

    def test_rejected_review_cannot_be_requeued_by_patch(self):
        Review.objects.filter(pk=self.review.pk).update(status='rejected')
        response = self.client.patch(f'{REVIEWS_URL}{self.review.id}/', {'comment': 'again'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, 'rejected')
        self.assertEqual(self.review.comment, 'Ok')

    def test_approved_review_can_still_be_edited_and_requeued(self):
        response = self.client.patch(f'{REVIEWS_URL}{self.review.id}/', {'comment': 'Better'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, 'pending')


class ReviewInputRulesTest(ReviewRulesTestBase):
    def test_owner_cannot_review_their_own_hotel(self):
        owner_booking = self._make_booking(self.other_user, self.property, '2024-03-01', '2024-03-05')
        self.client.force_authenticate(user=self.other_user)
        response = self.client.post(
            REVIEWS_URL, self._payload(booking=owner_booking.id), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Review.objects.exists())

    def test_markup_in_title_or_comment_is_rejected_on_create(self):
        for field in ('title', 'comment'):
            response = self.client.post(
                REVIEWS_URL, self._payload(**{field: '<script>x</script>'}), format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, field)
            self.assertIn(field, response.data['error']['details'])
        self.assertFalse(Review.objects.exists())

    def test_markup_is_rejected_on_update(self):
        review = Review.objects.create(
            user=self.user, property=self.property, booking=self.booking,
            overall_rating=4, title='Fine', comment='Ok', status='pending',
        )
        response = self.client.patch(f'{REVIEWS_URL}{review.id}/', {'comment': 'a<b'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
