"""Owner photos of a room type: list, upload, change, delete, cover rules, limits, what the room list and the guest page show."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from partner.serializers import MAX_PHOTOS_PER_ROOM_TYPE
from permissions.models import Role
from properties.models import Property, PropertyType, RoomPhoto, RoomType

User = get_user_model()

GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)
MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class RoomPhotoTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        self.client = APIClient()
        owner_role, _ = Role.objects.get_or_create(name='hotel-owner', defaults={'is_system_role': True})
        guest_role, _ = Role.objects.get_or_create(name='customer', defaults={'is_system_role': True})
        self.owner = User.objects.create_user(email='o1@example.com', password='testpassword123', role=owner_role)
        self.other = User.objects.create_user(email='o2@example.com', password='testpassword123', role=owner_role)
        self.guest = User.objects.create_user(email='g@example.com', password='testpassword123', role=guest_role)
        ptype = PropertyType.objects.create(name='Hotel', slug='hotel')
        self.room = self._room(self._property(self.owner, ptype), 'Standard')
        self.foreign = self._room(self._property(self.other, ptype), 'Foreign')
        self.url = f'/api/v1/partner/rooms/{self.room.id}/photos/'

    def _property(self, owner, ptype):
        return Property.objects.create(
            owner=owner, property_type=ptype, status='active', max_guests=2, bedrooms=1, bathrooms=1,
            address_line1='1 Main St', city='Tashkent', country='Uzbekistan', base_price=100, currency='USD',
        )

    def _room(self, prop, name):
        return RoomType.objects.create(
            property=prop, name=name, slug=name.lower(), base_occupancy=2, max_occupancy=2, base_price=50,
            currency='USD', total_rooms=3)

    def _upload(self, url=None, name='bed.gif', content=GIF, **extra):
        image = SimpleUploadedFile(name, content, content_type='image/gif')
        return self.client.post(url or self.url, {'photo': image, 'photo_type': 'bedroom', **extra}, format='multipart')

    def _photo(self, room=None, **fields):
        return RoomPhoto.objects.create(room_type=room or self.room, photo='rooms/x/photos/a.gif', **fields)

    def detail(self, photo, room=None):
        return f'/api/v1/partner/rooms/{(room or self.room).id}/photos/{photo.id}/'

    # list
    def test_owner_lists_own_room_photos_in_order(self):
        second = self._photo(display_order=2)
        first = self._photo(display_order=1)
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([p['id'] for p in response.data], [first.id, second.id])

    def test_list_of_another_owners_room_is_404(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(f'/api/v1/partner/rooms/{self.foreign.id}/photos/').status_code, 404)

    def test_guest_and_anonymous_cannot_list(self):
        self.assertIn(self.client.get(self.url).status_code, (401, 403))
        self.client.force_authenticate(self.guest)
        self.assertEqual(self.client.get(self.url).status_code, status.HTTP_403_FORBIDDEN)

    def test_list_excludes_deleted_photos(self):
        self._photo().soft_delete()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get(self.url).data, [])

    # upload
    def test_first_photo_becomes_cover_and_next_one_does_not(self):
        self.client.force_authenticate(self.owner)
        first = self._upload()
        second = self._upload(is_primary='false')
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertTrue(first.data['is_primary'])
        self.assertFalse(second.data['is_primary'])

    def test_new_photos_go_to_the_end(self):
        self.client.force_authenticate(self.owner)
        orders = [self._upload().data['display_order'] for _ in range(3)]
        self.assertEqual(orders, sorted(set(orders)))
        self.assertEqual(len(set(orders)), 3)

    def test_uploaded_file_name_is_random_not_the_clients(self):
        self.client.force_authenticate(self.owner)
        response = self._upload(name='my private name.gif')
        stored = RoomPhoto.objects.get(pk=response.data['id']).photo.name
        self.assertRegex(stored, r'/[0-9a-f]{32}\.gif$')
        self.assertNotIn('private', stored)

    def test_upload_to_another_owners_room_is_404(self):
        self.client.force_authenticate(self.owner)
        self.assertEqual(self._upload(url=f'/api/v1/partner/rooms/{self.foreign.id}/photos/').status_code, 404)

    def test_a_file_that_is_not_a_picture_is_refused(self):
        self.client.force_authenticate(self.owner)
        response = self._upload(name='evil.gif', content=b'<script>alert(1)</script>')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo', response.data)
        self.assertEqual(RoomPhoto.objects.count(), 0)

    def test_a_room_type_holds_a_limited_number_of_photos(self):
        for _ in range(MAX_PHOTOS_PER_ROOM_TYPE):
            self._photo()
        self.client.force_authenticate(self.owner)
        response = self._upload()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('photo', response.data)
        self.assertEqual(RoomPhoto.objects.filter(room_type=self.room).count(), MAX_PHOTOS_PER_ROOM_TYPE)

    # change
    def test_owner_changes_caption_and_type(self):
        photo = self._photo()
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.detail(photo), {'caption': 'Bed', 'photo_type': 'view'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        photo.refresh_from_db()
        self.assertEqual((photo.caption, photo.photo_type), ('Bed', 'view'))

    def test_making_a_photo_cover_demotes_the_old_one(self):
        old = self._photo(is_primary=True)
        new = self._photo()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(self.detail(new), {'is_primary': True}, format='json').status_code, 200)
        old.refresh_from_db(), new.refresh_from_db()
        self.assertEqual((old.is_primary, new.is_primary), (False, True))

    def test_cover_cannot_be_unset_directly(self):
        cover = self._photo(is_primary=True)
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.detail(cover), {'is_primary': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('is_primary', response.data)

    def test_the_image_file_cannot_be_replaced_by_patch(self):
        photo = self._photo()
        before = photo.photo.name
        self.client.force_authenticate(self.owner)
        image = SimpleUploadedFile('new.gif', GIF, content_type='image/gif')
        self.client.patch(self.detail(photo), {'photo': image}, format='multipart')
        photo.refresh_from_db()
        self.assertEqual(photo.photo.name, before)

    def test_other_owner_cannot_change_or_delete(self):
        photo = self._photo()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.patch(self.detail(photo), {'caption': 'x'}, format='json').status_code, 404)
        self.assertEqual(self.client.delete(self.detail(photo)).status_code, 404)
        self.assertFalse(RoomPhoto.objects.get(pk=photo.pk).is_deleted)

    def test_photo_of_another_room_under_my_room_is_404(self):
        foreign_photo = self._photo(room=self.foreign)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.patch(self.detail(foreign_photo), {'caption': 'x'}, format='json').status_code, 404)

    # delete
    def test_delete_soft_deletes(self):
        photo = self._photo()
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(self.detail(photo)).status_code, status.HTTP_204_NO_CONTENT)
        self.assertTrue(RoomPhoto.objects.get(pk=photo.pk).is_deleted)

    def test_deleting_the_cover_promotes_the_first_remaining(self):
        cover = self._photo(is_primary=True, display_order=0)
        next_up = self._photo(display_order=1)
        self._photo(display_order=2)
        self.client.force_authenticate(self.owner)
        self.client.delete(self.detail(cover))
        next_up.refresh_from_db()
        self.assertTrue(next_up.is_primary)

    def test_deleting_the_last_photo_leaves_no_cover_and_no_error(self):
        only = self._photo(is_primary=True)
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.delete(self.detail(only)).status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(self.url).data, [])

    def test_guest_cannot_delete(self):
        photo = self._photo()
        self.client.force_authenticate(self.guest)
        self.assertEqual(self.client.delete(self.detail(photo)).status_code, status.HTTP_403_FORBIDDEN)

    # what the room list shows
    def test_room_list_says_how_many_photos_a_room_has_and_which_one_is_the_cover(self):
        self._photo(is_primary=True, display_order=0)
        self._photo(display_order=1)
        self._photo().soft_delete()
        self.client.force_authenticate(self.owner)
        rooms = self.client.get('/api/v1/partner/rooms/')
        row = next(r for r in rooms.data['results'] if r['id'] == self.room.id) if 'results' in rooms.data \
            else next(r for r in rooms.data if r['id'] == self.room.id)
        self.assertEqual(row['photos_count'], 2)
        self.assertTrue(row['cover_url'].endswith('.gif'))

    def test_a_room_without_photos_has_count_zero_and_no_cover(self):
        self.client.force_authenticate(self.owner)
        data = self.client.get(f'/api/v1/partner/rooms/{self.room.id}/').data
        self.assertEqual((data['photos_count'], data['cover_url']), (0, None))
