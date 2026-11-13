"""
TICKBRON mehmanxana model leri hám izlew nátiyjeleri ushın serializer ler.
"""
from datetime import timedelta

from common.dates import business_today
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from django.db.models import Prefetch
from rest_framework import serializers
from properties.models import (
    Property, PropertyType, PropertyTranslation, PropertyPolicy,
    Amenity, AmenityCategory, PropertyAmenity, PropertyPhoto,
    RoomType, RatePlan, DateInventory, RoomPhoto, RoomAmenity
)
from bookings.pricing import owner_prices_of, price_list, property_price_list, rate_lookup, night_price_in
from common.money import SUPPORTED_BASE_CURRENCIES
from currency.rates import current_rate, rate_for_request, uzs_amount
from django.utils.dateparse import parse_date
from django.utils.translation import gettext as _

MAX_AVAILABILITY_DAYS = 366


class ApproxUzsPriceMixin(serializers.Serializer):
    """
    R6 D sheshimi: base_price eń sońǵı kurs boyınsha somda, tek kórsetiw ushın (atı
    shama menen degenin aytadı; alınatuǵın summa bron snapshot ınan keledi). Kurs hár
    soraw ushın bir márte izlenedi (currency.rates.rate_for_request), hesh qashan hár qatar ushın emes.
    """
    base_price_uzs_approx = serializers.SerializerMethodField()
    uzs_rate = serializers.SerializerMethodField()

    def _approx_uzs(self, obj):
        # 'rate_request' tek hár soraw ushın kurs keshin alıp júredi; ol DRF tiń
        # 'request' konteksti emes, ol fayl maydanların da absolyut URL ǵa ótkizer edi
        request = self.context.get('rate_request') or self.context.get('request')
        if request is None:
            return {'value': None, 'exchange_rate': None}
        return uzs_amount(request, obj.base_price, obj.currency, 'value')

    @extend_schema_field(OpenApiTypes.STR)
    def get_base_price_uzs_approx(self, obj):
        return self._approx_uzs(obj)['value']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_uzs_rate(self, obj):
        return self._approx_uzs(obj)['exchange_rate']


class CardPricesMixin(serializers.Serializer):
    """
    R16: mehmanxana kartasınıń hár qollap-quwatlanatuǵın valyutadaǵı "dan" bahası (sol valyutadaǵı aktiv rate
    plan larınıń eń arzan bahası): {code: {amount, source}}; qarań bookings.pricing.property_price_list.
    """
    prices = serializers.SerializerMethodField()

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_prices(self, obj):
        request = self.context.get('rate_request') or self.context.get('request')
        if not hasattr(self, '_rate_of'):
            self._rate_of = rate_lookup(request)
        plans = [plan for room_type in getattr(obj, 'card_room_types', []) for plan in room_type.rate_plans.all()]
        return property_price_list(obj, plans, self._rate_of)


class PropertyTypeSerializer(serializers.ModelSerializer):
    """PropertyType modeli ushın serializer."""

    class Meta:
        model = PropertyType
        fields = ['id', 'name', 'slug', 'description', 'icon']
        read_only_fields = ['id']


class AmenityCategorySerializer(serializers.ModelSerializer):
    """AmenityCategory modeli ushın serializer."""

    class Meta:
        model = AmenityCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'sort_order']
        read_only_fields = ['id']


class AmenitySerializer(serializers.ModelSerializer):
    """Amenity modeli ushın serializer."""
    category = AmenityCategorySerializer(read_only=True)

    class Meta:
        model = Amenity
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_searchable', 'sort_order', 'category']
        read_only_fields = ['id']


class PropertyAmenitySerializer(serializers.ModelSerializer):
    """PropertyAmenity modeli ushın serializer."""
    amenity = AmenitySerializer(read_only=True)

    class Meta:
        model = PropertyAmenity
        fields = ['amenity', 'is_available', 'notes']
        read_only_fields = []


class PropertyPhotoSerializer(serializers.ModelSerializer):
    """PropertyPhoto modeli ushın serializer."""
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = PropertyPhoto
        fields = ['id', 'photo', 'photo_url', 'photo_type', 'caption', 'is_primary', 'display_order', 'alt_text']
        read_only_fields = ['id']

    def get_photo_url(self, obj):
        """Súwret ushın absolyut URL di alıw."""
        if obj.photo:
            return obj.photo.url
        return None


class PropertyTranslationSerializer(serializers.ModelSerializer):
    """PropertyTranslation modeli ushın serializer."""

    class Meta:
        model = PropertyTranslation
        fields = ['language', 'name', 'description', 'address_line1', 'address_line2', 'city']
        read_only_fields = []


class PropertyPolicySerializer(serializers.ModelSerializer):
    """PropertyPolicy modeli ushın serializer."""

    class Meta:
        model = PropertyPolicy
        fields = ['policy_type', 'title', 'description', 'is_strict']
        read_only_fields = []


# Bir márte qurıladı: serializer óz maydanların anıqlaw ushın modeldi oqıydı, bul onı bir
# mehmanxananıń qatarı menen toltırıwdan qımbatlaw, hám izlew betinde 100 ge shekem mehmanxana boladı. Olar request almaydı, sol
# sebepli sorawlar arasında hesh nárse bólisilmeydi.
_PHOTO_ROW = PropertyPhotoSerializer()
_AMENITY_ROW = PropertyAmenitySerializer()


class PropertySearchResultSerializer(CardPricesMixin, ApproxUzsPriceMixin, serializers.ModelSerializer):
    """
    Izlew nátiyjeleri ushın serializer.

    Izlew nátiyjelerin kórsetiw ushın tiykarǵı mehmanxana maǵlıwmatın óz ishine aladı.
    """
    property_type = PropertyTypeSerializer(read_only=True)
    # Izlew queryset i bulardı aldınan júkleydi, sol sebepli hár nátiyje ushın query joq
    translations = PropertyTranslationSerializer(many=True, read_only=True)
    primary_photo = serializers.SerializerMethodField()
    amenities = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    # Izlew queryset i belgilegen (properties.search.with_review_scores)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'translations', 'property_type', 'status', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'base_price', 'currency', 'prices', 'base_price_uzs_approx', 'uzs_rate',
            'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating',
            'primary_photo', 'amenities', 'full_address', 'average_rating', 'review_count', 'created_at'
        ]
        read_only_fields = ['id']

    def get_primary_photo(self, obj):
        """Tiykarǵı súwret, bolmasa birinshisi; izlew aldınan júklegen qatarlardan oqıladı."""
        photos = list(obj.active_photos if hasattr(obj, 'active_photos') else obj.photos.filter(
            is_active=True, is_deleted=False))
        primary = next((photo for photo in photos if photo.is_primary), None) or (photos[0] if photos else None)
        return _PHOTO_ROW.to_representation(primary) if primary else None

    def get_amenities(self, obj):
        """Bar, izlenetuǵın amenity ler; izlew aldınan júklegen qatarlardan oqıladı."""
        links = obj.searchable_amenities if hasattr(obj, 'searchable_amenities') else obj.property_amenities.filter(
            is_available=True, amenity__is_searchable=True, is_deleted=False,
        ).select_related('amenity__category')
        return [_AMENITY_ROW.to_representation(link) for link in links]

    def get_full_address(self, obj):
        """Tolıq mánzildi qatar retinde alıw."""
        return obj.get_full_address()

    def get_average_rating(self, obj):
        value = getattr(obj, 'average_rating', None)
        return round(float(value), 1) if value is not None else None

    def get_review_count(self, obj):
        return getattr(obj, 'review_count', 0) or 0


class PropertyDetailSerializer(ApproxUzsPriceMixin, serializers.ModelSerializer):
    """
    Mehmanxana maǵlıwmatı ushın tolıq serializer.

    Mehmanxana beti ushın barlıq mehmanxana maǵlıwmatın óz ishine aladı.
    """
    property_type = PropertyTypeSerializer(read_only=True)
    translations = PropertyTranslationSerializer(many=True, read_only=True)
    policies = PropertyPolicySerializer(many=True, read_only=True)
    photos = PropertyPhotoSerializer(many=True, read_only=True)
    amenities = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    room_types = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'property_type', 'status', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'base_price', 'currency', 'base_price_uzs_approx', 'uzs_rate',
            'total_area', 'floor_number',
            'has_elevator', 'has_parking', 'has_wifi', 'has_ac', 'has_heating',
            'translations', 'policies', 'photos', 'amenities', 'full_address',
            'gallery', 'room_types',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_amenities(self, obj):
        """Mehmanxananıń barlıq amenity lerin alıw."""
        property_amenities = obj.property_amenities.filter(
            is_deleted=False
        ).select_related('amenity__category')

        return PropertyAmenitySerializer(property_amenities, many=True).data

    def get_full_address(self, obj):
        """Tolıq mánzildi qatar retinde alıw."""
        return obj.get_full_address()

    def get_gallery(self, obj):
        """Súwret túri boyınsha shólkemlestirilgen mehmanxana galereyasın alıw."""
        photos = obj.photos.filter(
            is_active=True,
            is_deleted=False
        ).order_by('display_order', 'created_at')

        gallery = {
            'exterior': [],
            'interior': [],
            'amenity': [],
            'room': [],
            'other': []
        }

        for photo in photos:
            photo_data = PropertyPhotoSerializer(photo).data
            # Joq súwret URL in durıs islew
            if not photo_data.get('photo_url'):
                photo_data['photo_url'] = None
            photo_type = photo.photo_type
            if photo_type in gallery:
                gallery[photo_type].append(photo_data)
            else:
                gallery['other'].append(photo_data)

        return gallery

    def get_room_types(self, obj):
        """Mehmanxana ushın rate plan lı xona túrlerin alıw."""
        # Prefetch ishinde SQL de filterlenedi, sol sebepli xona túrleri qansha bolsa da tórt query
        room_types = obj.room_types.filter(is_deleted=False).prefetch_related(
            Prefetch('rate_plans', queryset=RatePlan.objects.filter(
                is_active=True, is_deleted=False).prefetch_related('prices')),
            Prefetch('photos', queryset=RoomPhoto.objects.filter(is_active=True, is_deleted=False)),
            Prefetch('room_amenities', queryset=RoomAmenity.objects.filter(
                is_deleted=False).select_related('amenity__category')),
        )

        request = self.context.get('request')
        rates = {}

        def rate_of(code):
            """`code` diń bir birligine som; pútkil mehmanxana beti ushın hár valyuta ushın bir márte izlenedi."""
            if code not in rates:
                info = rate_for_request(request, code) if request else current_rate(code)
                rates[code] = getattr(info, 'rate', None)
            return rates[code]

        room_types_data = []
        for room_type in room_types:
            # Aktiv rate plan larǵı alıw
            active_rate_plans = room_type.rate_plans.all()

            rate_plans_data = []
            for rate_plan in active_rate_plans:
                rate_plan_data = {
                    'id': rate_plan.id,
                    'name': rate_plan.name,
                    'slug': rate_plan.slug,
                    'rate_type': rate_plan.rate_type,
                    'description': rate_plan.description,
                    'base_price': str(rate_plan.base_price),
                    'currency': rate_plan.currency,
                    'min_nights': rate_plan.min_nights,
                    'max_nights': rate_plan.max_nights,
                    'cancellation_policy': rate_plan.cancellation_policy,
                    'deposit_required': rate_plan.deposit_required,
                    'deposit_percentage': rate_plan.deposit_percentage,
                    'advance_booking_days': rate_plan.advance_booking_days,
                    'prices': price_list(rate_plan, rate_of),
                }
                rate_plans_data.append(rate_plan_data)

            # Xona súwretlerin alıw
            room_photos = room_type.photos.all()

            room_photos_data = []
            for photo in room_photos:
                photo_data = {
                    'id': photo.id,
                    'photo': photo.photo.url if photo.photo else None,
                    'photo_type': photo.photo_type,
                    'caption': photo.caption,
                    'is_primary': photo.is_primary,
                    'display_order': photo.display_order,
                    'alt_text': photo.alt_text,
                }
                room_photos_data.append(photo_data)

            # Xona amenity lerin alıw
            room_amenities = room_type.room_amenities.all()

            room_amenities_data = []
            for room_amenity in room_amenities:
                amenity_data = {
                    'amenity': {
                        'id': room_amenity.amenity.id,
                        'name': room_amenity.amenity.name,
                        'slug': room_amenity.amenity.slug,
                        'description': room_amenity.amenity.description,
                        'icon': room_amenity.amenity.icon,
                        'is_searchable': room_amenity.amenity.is_searchable,
                        'category': {
                            'id': room_amenity.amenity.category.id,
                            'name': room_amenity.amenity.category.name,
                            'slug': room_amenity.amenity.category.slug,
                            'description': room_amenity.amenity.category.description,
                            'icon': room_amenity.amenity.category.icon,
                        }
                    },
                    'is_available': room_amenity.is_available,
                    'notes': room_amenity.notes,
                }
                room_amenities_data.append(amenity_data)

            room_type_data = {
                'id': room_type.id,
                'name': room_type.name,
                'slug': room_type.slug,
                'description': room_type.description,
                'base_occupancy': room_type.base_occupancy,
                'max_occupancy': room_type.max_occupancy,
                'base_price': str(room_type.base_price),
                'currency': room_type.currency,
                'total_rooms': room_type.total_rooms,
                'bed_configuration': room_type.bed_configuration,
                'room_size': room_type.room_size,
                'is_vip': room_type.is_vip,
                'rate_plans': rate_plans_data,
                'photos': room_photos_data,
                'amenities': room_amenities_data,
            }
            room_types_data.append(room_type_data)

        # VIP xonalar birinshi; sorted() turaqlı, sol sebepli hár topar ádettegi tártipti saqlaydı
        return sorted(room_types_data, key=lambda room: not room['is_vip'])


class SearchParamsSerializer(serializers.Serializer):
    """
    Izlew sorawı parametrleri ushın serializer.

    Izlew endpoint i ushın izlew parametrlerin standartlastırılǵan tekseriw menen tekseredi hám oqıydı.
    """
    q = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Text search query (max 500 characters)"
    )
    location = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        help_text="Location search (city, country, max 200 characters)"
    )
    lat = serializers.DecimalField(
        required=False,
        max_digits=9,
        decimal_places=6,
        min_value=-90,
        max_value=90,
        help_text="Latitude for geographic search (-90 to 90)"
    )
    lng = serializers.DecimalField(
        required=False,
        max_digits=9,
        decimal_places=6,
        min_value=-180,
        max_value=180,
        help_text="Longitude for geographic search (-180 to 180)"
    )
    radius = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=100,
        help_text="Search radius in kilometers (1-100)"
    )
    min_price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        help_text="Minimum price (non-negative)"
    )
    max_price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        help_text="Maximum price (non-negative)"
    )
    min_guests = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        help_text="Minimum number of guests (min 1)"
    )
    max_guests = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=50,
        help_text="Maximum number of guests (min 1)"
    )
    amenities = serializers.ListField(
        required=False,
        child=serializers.IntegerField(),
        max_length=20,
        help_text="List of amenity IDs to filter by (max 20)"
    )
    property_type = serializers.IntegerField(
        required=False,
        min_value=1,
        help_text="Property type ID to filter by"
    )
    features = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Comma-separated features the property must all have: wifi, parking, ac, heating, elevator"
    )
    min_rating = serializers.DecimalField(
        required=False,
        max_digits=3,
        decimal_places=1,
        min_value=1,
        max_value=5,
        help_text="Minimum average guest rating (1-5)"
    )
    check_in = serializers.DateField(
        required=False,
        help_text="Check-in date (YYYY-MM-DD format)"
    )
    check_out = serializers.DateField(
        required=False,
        help_text="Check-out date (YYYY-MM-DD format)"
    )
    sort = serializers.ChoiceField(
        required=False,
        default='relevance',
        choices=['relevance', 'price_asc', 'price_desc', 'rating', 'reviews', 'distance'],
        help_text="Sorting method"
    )
    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
        help_text="Page number (min 1)"
    )
    page_size = serializers.IntegerField(
        required=False,
        default=20,
        min_value=1,
        max_value=100,
        help_text="Results per page (1-100)"
    )

    def validate_features(self, value):
        from properties.search import FEATURES
        features = [f.strip() for f in value.split(',') if f.strip()]
        unknown = [f for f in features if f not in FEATURES]
        if unknown:
            raise serializers.ValidationError(
                f"Unknown feature(s): {', '.join(unknown)}. Allowed: {', '.join(FEATURES)}."
            )
        return features

    def validate(self, data):
        """Izlew parametrlerin tolıq tekseriwler menen tekseriw."""
        # Geografiyalıq izlew parametrlerin tekseriw
        if (data.get('lat') and not data.get('lng')) or (data.get('lng') and not data.get('lat')):
            raise serializers.ValidationError(_("Both lat and lng are required for geographic search"))

        # Sana aralıǵın tekseriw
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError("check_out must be after check_in")

        # Baha aralıǵın tekseriw
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        if min_price and max_price and max_price < min_price:
            raise serializers.ValidationError("max_price must be greater than or equal to min_price")

        # Mehmanlar aralıǵın tekseriw
        min_guests = data.get('min_guests')
        max_guests = data.get('max_guests')
        if min_guests and max_guests and max_guests < min_guests:
            raise serializers.ValidationError("max_guests must be greater than or equal to min_guests")

        return data


class DateInventorySerializer(serializers.ModelSerializer):
    """
    DateInventory modeli ushın serializer.

    Kúnlik bos orın hám baha maǵlıwmatın kórsetedi.
    """
    remaining_rooms = serializers.IntegerField(help_text="Calculated remaining available rooms")
    # R16: túnniń hár valyutadaǵı bahası; contextte rate plan kerek (qarań RatePlanAvailabilitySerializer)
    prices = serializers.SerializerMethodField()

    class Meta:
        model = DateInventory
        fields = [
            'id', 'date', 'available_rooms', 'booked_rooms', 'remaining_rooms',
            'price', 'currency', 'prices', 'is_available', 'minimum_stay', 'maximum_stay'
        ]
        read_only_fields = ['id']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_prices(self, row):
        from common.money import SUPPORTED_BASE_CURRENCIES, quantize

        plan = self.context.get('rate_plan')
        if plan is None:
            return None
        price = row.price if row.price is not None else plan.base_price
        owner = self.context['owner_prices']
        result = {}
        for code in SUPPORTED_BASE_CURRENCIES:
            amount, _ = night_price_in(plan.currency, owner, price, code, self.context['rate_of'])
            result[code] = None if amount is None else f'{quantize(amount, code):.2f}'
        return result


class RatePlanAvailabilitySerializer(serializers.ModelSerializer):
    """
    Bos orın maǵlıwmatı bar RatePlan ushın serializer.

    Rate plan maǵlıwmatın hám berilgen sana aralıǵındaǵı date inventory di óz ishine aladı.
    """
    date_inventory = serializers.SerializerMethodField()
    # R16: plannıń hár valyutadaǵı bahası (iye / tiykarǵı / konvertaciyalanǵan), qarań bookings.pricing.price_list
    prices = serializers.SerializerMethodField()

    class Meta:
        model = RatePlan
        fields = [
            'id', 'name', 'slug', 'rate_type', 'description', 'base_price', 'currency', 'prices',
            'min_nights', 'max_nights', 'is_active', 'cancellation_policy',
            'deposit_required', 'deposit_percentage', 'advance_booking_days', 'date_inventory',
        ]
        read_only_fields = ['id']

    def get_date_inventory(self, obj):
        """
        Usı rate plan ushın soralǵan sana aralıǵındaǵı date inventory di alıw.

        Baha hám qaǵıydalar (ashıq/jabıq, eń kem/eń kóp turıw) ele DateInventory den keledi, biraq
        available_rooms/booked_rooms/remaining_rooms jaddıda (saqlanbaydı) RoomInventory den
        -- xona túriniń ortaq fizikalıq xona sanınan -- qayta jazıladı, sebebi
        bron sisteması 3.3 te DateInventory diń óz sanaǵıshların jazıwdı toqtattı (audit #31).
        Ele RoomInventory qatarı joq tún basqarılmaydı: xona túriniń tolıq
        total_rooms ı menen ashıq, quote_stay penen birdey ádetdegi mánis.
        """
        from properties.models import RoomInventory

        request = self.context.get('request')
        check_in = request.query_params.get('check_in') if request else None
        check_out = request.query_params.get('check_out') if request else None

        # Ushı ashıq soraw hár waqıt saqlanǵan hár qatardı qaytarar edi: onı baslanıwınan bir jılǵa shekem shekemlew
        start = parse_date(check_in) if check_in else business_today()
        queryset = obj.date_inventory.filter(
            is_deleted=False, date__gte=start, date__lte=start + timedelta(days=MAX_AVAILABILITY_DAYS),
        ).order_by('date')

        if check_out:
            queryset = queryset.filter(date__lte=check_out)

        rows = list(queryset)
        if rows:
            room_rows = {
                room_row.date: room_row for room_row in RoomInventory.objects.filter(
                    room_type=obj.room_type, date__in=[row.date for row in rows],
                )
            }
            for row in rows:
                room_row = room_rows.get(row.date)
                if room_row is not None:
                    row.available_rooms = room_row.available_rooms
                    row.booked_rooms = room_row.booked_rooms
                else:
                    row.available_rooms = obj.room_type.total_rooms
                    row.booked_rooms = 0

        return DateInventorySerializer(rows, many=True, context={
            'rate_plan': obj, 'owner_prices': owner_prices_of(obj), 'rate_of': self._rate_of(),
        }).data

    def _rate_of(self):
        if 'rate_of' not in self.context:
            self.context['rate_of'] = rate_lookup(self.context.get('request'))
        return self.context['rate_of']

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_prices(self, obj):
        return price_list(obj, self._rate_of())


class RoomTypeAvailabilitySerializer(serializers.ModelSerializer):
    """
    Bos orın maǵlıwmatı bar RoomType ushın serializer.

    Xona túri maǵlıwmatın hám olardıń bos orınları menen rate plan larǵı óz ishine aladı.
    """
    rate_plans = serializers.SerializerMethodField()

    class Meta:
        model = RoomType
        fields = [
            'id', 'name', 'slug', 'description', 'base_occupancy', 'max_occupancy',
            'base_price', 'currency', 'total_rooms', 'bed_configuration', 'room_size', 'is_vip', 'rate_plans'
        ]
        read_only_fields = ['id']

    def get_rate_plans(self, obj):
        """Usı xona túri ushın bos orın maǵlıwmatı bar aktiv rate plan larǵı alıw."""
        request = self.context.get('request')
        rate_plans = obj.rate_plans.filter(
            is_active=True,
            is_deleted=False
        ).prefetch_related('prices').order_by('name')

        return RatePlanAvailabilitySerializer(
            rate_plans,
            many=True,
            context={'request': request, 'rate_of': rate_lookup(request)}
        ).data


class PropertyAvailabilitySerializer(ApproxUzsPriceMixin, serializers.ModelSerializer):
    """
    Mehmanxananıń bos orın maǵlıwmatı ushın serializer.

    Mehmanxana maǵlıwmatın hám rate plan lar menen date inventory bar xona túrlerin óz ishine aladı.
    """
    room_types = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'property_type', 'status', 'max_guests', 'bedrooms', 'bathrooms',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country',
            'latitude', 'longitude', 'base_price', 'currency', 'base_price_uzs_approx', 'uzs_rate', 'room_types'
        ]
        read_only_fields = ['id']

    def get_room_types(self, obj):
        """Usı mehmanxana ushın bos orın maǵlıwmatı bar xona túrlerin alıw."""
        request = self.context.get('request')
        # Aldın VIP xonalar, keyin at boyınsha
        room_types = obj.room_types.filter(
            is_deleted=False
        ).order_by('-is_vip', 'name')

        return RoomTypeAvailabilitySerializer(
            room_types,
            many=True,
            context={'request': request}
        ).data


class AvailabilityParamsSerializer(serializers.Serializer):
    """
    Availability endpoint sorawı parametrleri ushın serializer.

    Bos orın sorawları ushın sana aralıǵı parametrlerin tekseredi.
    """
    check_in = serializers.DateField(
        required=False,
        help_text="Check-in date (YYYY-MM-DD format)"
    )
    check_out = serializers.DateField(
        required=False,
        help_text="Check-out date (YYYY-MM-DD format)"
    )

    def validate(self, data):
        """Sana aralıǵı parametrlerin tekseriw."""
        check_in = data.get('check_in')
        check_out = data.get('check_out')

        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError("check_out must be after check_in")

        if check_in and check_in < business_today():
            raise serializers.ValidationError("check_in cannot be in the past")

        return data


class QuoteParamsSerializer(serializers.Serializer):
    """GET /properties/{id}/quote/ tiń query parametrleri."""
    room_type_id = serializers.IntegerField(min_value=1)
    rate_plan_id = serializers.IntegerField(min_value=1)
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    rooms = serializers.IntegerField(min_value=1, max_value=20, default=1)
    # R16: turıwdı usı valyutada kórsetiw (ádetde: rate plan nıń óz valyutası)
    currency = serializers.ChoiceField(choices=SUPPORTED_BASE_CURRENCIES, required=False)

    def validate(self, data):
        if data['check_out'] <= data['check_in']:
            raise serializers.ValidationError({'check_out': _('Check-out date must be after check-in date')})
        if data['check_in'] < business_today():
            raise serializers.ValidationError({'check_in': _('Check-in date cannot be in the past')})
        return data
