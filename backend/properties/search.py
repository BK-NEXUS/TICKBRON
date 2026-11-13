"""
Database múmkinshiliklerin paydalanıp TICKBRON mehmanxana izlewi ushın izlew xızmeti.

Bul modul SQLite (development) hám PostgreSQL (production) de isleytuǵın database imkaniyatların
paydalanıp tekst izlew, geografiyalıq izlew hám tolıq filterlewdi usınadı.
"""
from django.db.models import Q, F, FloatField, Prefetch, Avg, Count, Exists, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import date, datetime
import math
import re


# `features` mánisin izlew -> Property belgisi. Tártip jan panel kórsetetuǵın tártip.
FEATURES = {
    'wifi': ('has_wifi', 'WiFi'),
    'parking': ('has_parking', 'Parking'),
    'ac': ('has_ac', 'Air Conditioning'),
    'heating': ('has_heating', 'Heating'),
    'elevator': ('has_elevator', 'Elevator'),
}

SORT_OPTIONS = [
    ('relevance', 'Relevance'),
    ('price_asc', 'Price: Low to High'),
    ('price_desc', 'Price: High to Low'),
    ('rating', 'Rating'),
    ('reviews', 'Number of Reviews'),
]


def searchable_properties():
    """Izlew qaytara alatuǵın mehmanxanalar: tastıyıqlanǵan, aktiv hám óshirilmegen."""
    from properties.models import Property
    return Property.objects.filter(is_active=True, is_deleted=False, status='active')


def card_prices_prefetch(prefix=''):
    """
    R16: mehmanxana kartasına hár valyutadaǵı "dan" bahası ushın kerek aktiv rate plan lar (iyeniń bahaları menen),
    mehmanxanada `card_room_types` retinde; `prefix` mehmanxanaǵa jol ("property__").
    """
    from properties.models import RatePlan, RoomType

    return Prefetch(f'{prefix}room_types', to_attr='card_room_types', queryset=RoomType.objects.filter(
        is_deleted=False).prefetch_related(Prefetch('rate_plans', queryset=RatePlan.objects.filter(
            is_active=True, is_deleted=False).prefetch_related('prices'))))


GEOGRAPHY_LEVELS = ('region_ref', 'country_ref')
GEOGRAPHY_LANGUAGES = ('uz', 'ru', 'en')
MAX_SEARCH_WORDS = 8


def geography_name_filter(term):
    """Mehmanxananıń regionı yamasa mámleketiniń uz/ru/en atında sózdi izleytuǵın Q (ref ler arqalı)."""
    query = Q()
    for level in GEOGRAPHY_LEVELS:
        for language in GEOGRAPHY_LANGUAGES:
            query |= Q(**{f'{level}__name_{language}__icontains': term})
    return query


def with_review_scores(queryset):
    """
    Tastıyıqlanǵan sharhlardan average_rating (sharh joq bolsa None) hám review_count di belgilew.
    Sub-query ler, sol sebepli basqa filter ler qosqan join lar sanlardı kóbeytip jibere almaydı.
    """
    from accounts.models import Review

    approved = Review.objects.filter(
        property=OuterRef('pk'), status='approved', is_deleted=False,
    ).order_by().values('property')
    return queryset.annotate(
        average_rating=Subquery(
            approved.annotate(value=Avg('overall_rating')).values('value'), output_field=FloatField(),
        ),
        review_count=Coalesce(
            Subquery(approved.annotate(value=Count('id')).values('value'), output_field=IntegerField()),
            0,
        ),
    )


class PropertySearchService:
    """
    PostgreSQL imkaniyatların paydalanıp mehmanxana izlewi ushın xızmet klası.

    Tolıq tekst izlew, geografiyalıq izlew, anıq emes sáykeslew hám tolıq filterlewdi usınadı.
    """

    def __init__(self):
        self.base_queryset = self._get_base_queryset()

    def _get_base_queryset(self):
        """Mehmanxana izlewi ushın tiykarǵı queryset ti alıw."""
        from properties.models import PropertyAmenity, PropertyPhoto, PropertyTranslation

        return with_review_scores(searchable_properties()).select_related(
            'owner',
            'property_type'
        ).prefetch_related(
            # Hár nátiyjeniń awdarmaları ushın bir query (`translations` retinde serializer den ótedi)
            Prefetch('translations', queryset=PropertyTranslation.objects.filter(is_deleted=False)),
            # Serializer de emes, usı jerde filterlenedi, sol sebepli nátiyje beti qálegen ólshemde birdey query ge túsedi
            Prefetch('property_amenities', to_attr='searchable_amenities', queryset=PropertyAmenity.objects.filter(
                is_available=True, amenity__is_searchable=True, is_deleted=False).select_related('amenity__category')),
            Prefetch('photos', to_attr='active_photos', queryset=PropertyPhoto.objects.filter(
                is_active=True, is_deleted=False)),
            card_prices_prefetch(),
        )

    def _validate_search_params(self, search_params):
        """
        Izlew parametrlerin tekseriw hám tazalaw.

        Tazalanǵan parametrler dict in qaytaradı (tártiplew hám betlew ushın ádetdegi mánisler toltırılǵan).
        Birinshi jaramsız parametr ushın xabarı bar ValueError kóteredi.
        """
        validated_params = {}
        for check in (
            self._check_text, self._check_location, self._check_coordinates, self._check_radius,
            self._check_price_range, self._check_guest_range, self._check_amenities, self._check_property_type,
            self._check_dates, self._check_features, self._check_min_rating, self._check_sort, self._check_paging,
        ):
            check(search_params, validated_params)
        return validated_params

    @staticmethod
    def _check_text(params, out):
        if 'q' not in params:
            return
        q = str(params['q']).strip()
        if len(q) > 500:
            raise ValueError("Search query too long (max 500 characters)")
        # Potencial qáwipli belgilerdi alıp taslaw
        q = re.sub(r'[<>"\']', '', q)
        out['q'] = q if q else None

    @staticmethod
    def _check_location(params, out):
        if 'location' not in params:
            return
        location = str(params['location']).strip()
        if len(location) > 200:
            raise ValueError("Location too long (max 200 characters)")
        out['location'] = location if location else None

    @staticmethod
    def _optional_pair(params, low_key, high_key, convert):
        """Aralıqtıń eki ushı san retinde; jiberilmegen ushı None."""
        low = convert(params[low_key]) if low_key in params else None
        high = convert(params[high_key]) if high_key in params else None
        return low, high

    def _check_coordinates(self, params, out):
        if 'lat' not in params and 'lng' not in params:
            return
        try:
            lat, lng = self._optional_pair(params, 'lat', 'lng', float)
            if lat is not None and not -90 <= lat <= 90:
                raise ValueError("Invalid latitude (must be between -90 and 90)")
            if lng is not None and not -180 <= lng <= 180:
                raise ValueError("Invalid longitude (must be between -180 and 180)")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid geographic coordinates: {str(e)}")
        out['lat'], out['lng'] = lat, lng

    @staticmethod
    def _check_radius(params, out):
        if 'radius' not in params:
            return
        try:
            radius = float(params['radius'])
            if not 1 <= radius <= 100:
                raise ValueError("Radius must be between 1 and 100 km")
        except (ValueError, TypeError):
            raise ValueError("Invalid radius value")
        out['radius'] = radius

    def _check_price_range(self, params, out):
        if 'min_price' not in params and 'max_price' not in params:
            return
        try:
            min_price, max_price = self._optional_pair(params, 'min_price', 'max_price', float)
            if min_price is not None and min_price < 0:
                raise ValueError("Minimum price cannot be negative")
            if max_price is not None and max_price < 0:
                raise ValueError("Maximum price cannot be negative")
            if min_price is not None and max_price is not None and min_price > max_price:
                raise ValueError("Minimum price cannot be greater than maximum price")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid price values: {str(e)}")
        out['min_price'], out['max_price'] = min_price, max_price

    def _check_guest_range(self, params, out):
        if 'min_guests' not in params and 'max_guests' not in params:
            return
        try:
            min_guests, max_guests = self._optional_pair(params, 'min_guests', 'max_guests', int)
            if min_guests is not None and min_guests < 1:
                raise ValueError("Minimum guests must be at least 1")
            if max_guests is not None and max_guests < 1:
                raise ValueError("Maximum guests must be at least 1")
            if min_guests is not None and max_guests is not None and min_guests > max_guests:
                raise ValueError("Minimum guests cannot be greater than maximum guests")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid guest values: {str(e)}")
        out['min_guests'], out['max_guests'] = min_guests, max_guests

    @staticmethod
    def _check_amenities(params, out):
        if 'amenities' not in params:
            return
        amenities = params['amenities']
        if not isinstance(amenities, list):
            raise ValueError("Amenities must be a list")
        if len(amenities) > 20:
            raise ValueError("Too many amenities (max 20)")
        out['amenities'] = amenities

    @staticmethod
    def _check_property_type(params, out):
        if 'property_type' not in params:
            return
        try:
            property_type = int(params['property_type'])
            if property_type < 1:
                raise ValueError("Invalid property type ID")
        except (ValueError, TypeError):
            raise ValueError("Invalid property type value")
        out['property_type'] = property_type

    def _check_dates(self, params, out):
        if 'check_in' not in params and 'check_out' not in params:
            return
        try:
            check_in = self._parse_date(params.get('check_in')) if 'check_in' in params else None
            check_out = self._parse_date(params.get('check_out')) if 'check_out' in params else None
            if check_in and check_out and check_out <= check_in:
                raise ValueError("Check-out date must be after check-in date")
        except ValueError as e:
            raise ValueError(f"Invalid date values: {str(e)}")
        out['check_in'], out['check_out'] = check_in, check_out

    @staticmethod
    def _check_features(params, out):
        if not params.get('features'):
            return
        features = list(params['features'])
        unknown = [f for f in features if f not in FEATURES]
        if unknown:
            raise ValueError(f"Unknown features: {', '.join(unknown)}")
        out['features'] = features

    @staticmethod
    def _check_min_rating(params, out):
        if params.get('min_rating') is None:
            return
        try:
            min_rating = float(params['min_rating'])
        except (ValueError, TypeError):
            raise ValueError("Invalid minimum rating")
        if not 1 <= min_rating <= 5:
            raise ValueError("Minimum rating must be between 1 and 5")
        out['min_rating'] = min_rating

    @staticmethod
    def _check_sort(params, out):
        valid_sort_methods = [sort_id for sort_id, _ in SORT_OPTIONS] + ['distance']
        sort = params.get('sort', 'relevance')
        if sort not in valid_sort_methods:
            raise ValueError(f"Invalid sort method. Must be one of: {', '.join(valid_sort_methods)}")
        out['sort'] = sort

    @staticmethod
    def _positive_int(params, key, default, message, maximum=None):
        """Eń keminde 1 (hám eń kóbi `maximum`) bolǵan integer parametr, yamasa jiberilmegen bolsa ádetdegi mánis."""
        if key not in params:
            return default
        try:
            value = int(params[key])
            if value < 1 or (maximum is not None and value > maximum):
                raise ValueError(message)
        except (ValueError, TypeError):
            raise ValueError(message)
        return value

    def _check_paging(self, params, out):
        out['page'] = self._positive_int(params, 'page', 1, "Invalid page number")
        out['page_size'] = self._positive_int(params, 'page_size', 20, "Invalid page size", maximum=100)

    def _parse_date(self, date_str):
        """
        Túrli formatlardaǵı sana qatarın oqıw.

        Argumentler:
            date_str: sana qatarı (YYYY-MM-DD formatı jaqsı)

        Qaytaradı:
            datetime.date obyekti

        Kóteredi:
            ValueError: sana formatı jaramsız bolsa
        """
        if not date_str:
            return None
        # SearchParamsSerializer query mánisin aldınan sanaǵa ótkizgen
        if isinstance(date_str, date):
            return date_str

        try:
            # Aldın YYYY-MM-DD formatın sınap kóriw
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                # Basqa ulıwma formatlardı sınap kóriw
                return datetime.strptime(date_str, '%Y/%m/%d').date()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD format.")

    def filtered_queryset(self, search_params):
        """Tártiplew hám betlewden aldın hár filterge sáykes keletuǵın izlenetuǵın mehmanxanalar."""
        return self._apply_filters(self.base_queryset, self._validate_search_params(search_params))

    def _apply_filters(self, queryset, search_params):

        # Tekst izlewdi qollanıw
        if search_params.get('q'):
            queryset = self._apply_text_search(queryset, search_params['q'])

        # Jaylasıw izlewin qollanıw
        if search_params.get('location'):
            queryset = self._apply_location_search(queryset, search_params['location'])

        # Geografiyalıq izlewdi qollanıw
        if all(k in search_params for k in ['lat', 'lng']):
            radius = search_params.get('radius', 10)  # ádetde 10km
            queryset = self._apply_geographic_search(
                queryset,
                search_params['lat'],
                search_params['lng'],
                radius
            )

        # Baha filterin qollanıw
        if search_params.get('min_price') is not None or search_params.get('max_price') is not None:
            queryset = self._apply_price_filter(
                queryset,
                search_params.get('min_price'),
                search_params.get('max_price')
            )

        # Mehmanlar sıyımlılıǵı filterin qollanıw
        if search_params.get('min_guests') is not None or search_params.get('max_guests') is not None:
            queryset = self._apply_guest_filter(
                queryset,
                search_params.get('min_guests'),
                search_params.get('max_guests')
            )

        # Amenity filterin qollanıw
        if search_params.get('amenities'):
            queryset = self._apply_amenity_filter(queryset, search_params['amenities'])

        # Feature filterin qollanıw (hár soralǵan belgi qoyılǵan bolıwı kerek)
        if search_params.get('features'):
            queryset = queryset.filter(**{FEATURES[f][0]: True for f in search_params['features']})

        # Eń kem reyting filterin qollanıw (bahalanbaǵan mehmanxanalarda reyting joq, sol sebepli olar túsip qaladı)
        if search_params.get('min_rating') is not None:
            queryset = queryset.filter(average_rating__gte=search_params['min_rating'])

        # Mehmanxana túri filterin qollanıw
        if search_params.get('property_type'):
            queryset = self._apply_property_type_filter(queryset, search_params['property_type'])

        # Sana boyınsha bos orın filterin qollanıw
        if search_params.get('check_in') and search_params.get('check_out'):
            queryset = self._apply_date_filter(
                queryset,
                search_params['check_in'],
                search_params['check_out']
            )

        return queryset

    def search(self, search_params):
        """
        Berilgen parametrler boyınsha mehmanxana izlewin orınlaw.

        Argumentler:
            search_params: izlew parametrleri bar dict
                - q: tekst izlew sorawı
                - location: jaylasıw izlewi (city, country)
                - lat, lng, radius: geografiyalıq izlew
                - min_price, max_price: baha aralıǵı
                - min_guests, max_guests: mehmanlar sıyımlılıǵı
                - amenities: amenity ID lar dizimi
                - property_type: mehmanxana túri ID si
                - check_in, check_out: bos orın ushın sana aralıǵı
                - sort: tártiplew usılı (relevance, price_asc, price_desc, rating, distance)
                - page: bet nomeri
                - page_size: bettegi nátiyjeler

        Qaytaradı:
            Izlew nátiyjeleri hám metadata menen dict

        Kóteredi:
            ValueError: izlew parametrleri jaramsız bolsa
        """
        # Izlew parametrlerin tekseriw hám tazalaw
        search_params = self._validate_search_params(search_params)

        queryset = self._apply_filters(self.base_queryset, search_params)

        # Tártiplewdi qollanıw
        sort_method = search_params.get('sort', 'relevance')
        queryset = self._apply_sorting(queryset, sort_method, search_params)

        # Standartlastırılǵan qátelik islew menen betlewdi qollanıw
        page = search_params.get('page', 1)
        page_size = search_params.get('page_size', 20)

        try:
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
        except (EmptyPage, PageNotAnInteger):
            # Betlew qátelikların durıs islew
            page = 1
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

        return {
            'count': paginator.count,
            'next': page_obj.has_next() and page + 1 or None,
            'previous': page_obj.has_previous() and page - 1 or None,
            'results': list(page_obj.object_list),
            'page': page,
            'page_size': page_size,
            'total_pages': paginator.num_pages
        }

    def _apply_text_search(self, queryset, query):
        """
        Django ORM icontains di paydalanıp tekst izlewdi qollanıw (SQLite hám PostgreSQL de isleydi).

        Argumentler:
            queryset: tiykarǵı queryset
            query: tazalanǵan izlew sorawı qatarı

        Qaytaradı:
            filterlengen queryset
        """
        if not query or len(query) < 2:
            return queryset

        from properties.models import PropertyTranslation

        # Hár sóz óz aldına sáykeslenedi, hám hár sóz qayda bolsa da sáykes keliwi kerek (sóz basqa
        # maydanǵa sáykes keliwi múmkin). OR menen "Pricey Street" qálegen "Street" bar hár mehmanxananı tabar edi.
        # Sóz sanı shegaralanǵan hám awdarmalar EXISTS penen sáykeslenedi, sol sebepli SQL uzın
        # sorawda ósip ketpeydi (hár sózge bir join bir anonim sorawǵa database di ustap qalıwǵa múmkinshilik berdi).
        for word in self._search_words(query):
            queryset = queryset.filter(
                Q(address_line1__icontains=word) |
                Q(city__icontains=word) |
                Q(country__icontains=word) |
                geography_name_filter(word) |
                Exists(PropertyTranslation.objects.filter(property=OuterRef('pk')).filter(
                    Q(name__icontains=word) | Q(description__icontains=word)))
            )
        return queryset

    @staticmethod
    def _search_words(query):
        """2+ belgili birinshi MAX_SEARCH_WORDS ayrıqsha sóz (register ti esapqa almay)."""
        words = []
        for word in query.split():
            if len(word) >= 2 and word.lower() not in (seen.lower() for seen in words):
                words.append(word)
        return words[:MAX_SEARCH_WORDS]

    def _apply_location_search(self, queryset, location):
        """
        Jaylasıw tiykarındaǵı izlewdi qollanıw: Geography ref leri arqalı úsh tildegi atlar,
        hám tekst maydanlar (sáykeslenbegen mehmanxanalardaǵı jalǵız jaylasıw).
        """
        return queryset.filter(
            geography_name_filter(location) |
            Q(city__icontains=location) |
            Q(country__icontains=location) |
            Q(address_line1__icontains=location)
        )

    def _apply_geographic_search(self, queryset, lat, lng, radius_km):
        """
        Ápiwayılastırılǵan bounding box usılı menen geografiyalıq izlewdi qollanıw.

        Argumentler:
            queryset: tiykarǵı queryset
            lat: izlew orayınıń latitude ı
            lng: izlew orayınıń longitude ı
            radius_km: kilometrlerde izlew radiusı
        """
        # Database ler arası sáykeslik ushın ápiwayı bounding box usılı
        # Radiusti shama menen gradusqa ótkiziw (1 gradus ≈ 111 km)
        lat_range = radius_km / 111.0
        lng_range = radius_km / (111.0 * math.cos(math.radians(float(lat))))

        return queryset.filter(
            latitude__gte=float(lat) - lat_range,
            latitude__lte=float(lat) + lat_range,
            longitude__gte=float(lng) - lng_range,
            longitude__lte=float(lng) + lng_range
        )

    def _apply_price_filter(self, queryset, min_price=None, max_price=None):
        """
        Standartlastırılǵan minez benen baha aralıǵı filterin qollanıw.

        Argumentler:
            queryset: tiykarǵı queryset
            min_price: eń kem baha (tekserilgen)
            max_price: eń kóp baha (tekserilgen)

        Qaytaradı:
            filterlengen queryset
        """
        if min_price is not None:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(base_price__lte=max_price)

        return queryset

    def _apply_guest_filter(self, queryset, min_guests=None, max_guests=None):
        """
        Standartlastırılǵan minez benen mehmanlar sıyımlılıǵı filterin qollanıw.

        Argumentler:
            queryset: tiykarǵı queryset
            min_guests: mehmanlardıń eń kem sanı (tekserilgen)
            max_guests: mehmanlardıń eń kóp sanı (tekserilgen)

        Qaytaradı:
            filterlengen queryset
        """
        if min_guests is not None:
            queryset = queryset.filter(max_guests__gte=min_guests)
        if max_guests is not None:
            queryset = queryset.filter(max_guests__lte=max_guests)

        return queryset

    def _apply_amenity_filter(self, queryset, amenity_ids):
        """
        Standartlastırılǵan minez benen amenity filterin qollanıw.

        Argumentler:
            queryset: tiykarǵı queryset
            amenity_ids: amenity ID lar dizimi (tekserilgen)

        Qaytaradı:
            filterlengen queryset
        """

        # Barlıq kórsetilgen amenity i bar mehmanxanalardı filterlew
        for amenity_id in amenity_ids:
            queryset = queryset.filter(
                property_amenities__amenity_id=amenity_id,
                property_amenities__is_available=True
            )

        return queryset.distinct()

    def _apply_property_type_filter(self, queryset, property_type_id):
        """Mehmanxana túri filterin qollanıw."""
        return queryset.filter(property_type_id=property_type_id)

    def _apply_date_filter(self, queryset, check_in, check_out):
        """
        Pútkil turıw ushın bronlanıwı múmkin mehmanxanalardı qaldırıw: rate plan nıń eń kem/eń kóp túnleri turıwǵa
        ruxsat beretuǵın bir aktiv rate plan (aktiv xona túrinde), check_in nen check_out qa shekem (kirmeydi)
        hár tún ushın ashıq DateInventory qatarı (baha/qaǵıydalar) bar, hám xona túrinde sol túnlerdiń hárqaysısında
        RoomInventory de fizikalıq xona qalǵan -- 3.3 ten beri ortaq san (audit #31); RoomInventory
        qatarı joq tún basqarılmaydı hám xona túriniń tolıq total_rooms ı menen ashıq.
        quote_stay penen birdey qaǵıydalar.
        """
        from properties.models import DateInventory, RatePlan, RoomInventory

        check_in = self._parse_date(check_in)
        check_out = self._parse_date(check_out)
        if not check_in or not check_out or check_out <= check_in:
            return queryset
        nights = (check_out - check_in).days

        open_nights = DateInventory.objects.filter(
            rate_plan=OuterRef('pk'),
            date__gte=check_in,
            date__lt=check_out,
            is_deleted=False,
            is_available=True,
        ).filter(
            Q(minimum_stay__isnull=True) | Q(minimum_stay__lte=nights),
            Q(maximum_stay__isnull=True) | Q(maximum_stay__gte=nights),
        ).order_by().values('rate_plan').annotate(n=Count('id')).values('n')

        # Xona túriniń ortaq RoomInventory qatarı bar hám satılıp bolǵan yamasa jabıq túnler.
        # Joq qatar basqarılmaydı (ashıq), sol sebepli bul jerde hesh qashan esaplanbaydı.
        room_short_nights = RoomInventory.objects.filter(
            room_type=OuterRef('room_type'),
            date__gte=check_in,
            date__lt=check_out,
        ).filter(
            Q(is_available=False) | Q(available_rooms__lte=F('booked_rooms'))
        ).order_by().values('room_type').annotate(n=Count('id')).values('n')

        bookable_rate_plans = RatePlan.objects.filter(
            is_active=True,
            is_deleted=False,
            room_type__is_active=True,
            room_type__is_deleted=False,
            room_type__total_rooms__gt=0,
            min_nights__lte=nights,
        ).filter(
            Q(max_nights__isnull=True) | Q(max_nights__gte=nights)
        ).annotate(
            open_nights=Subquery(open_nights, output_field=IntegerField()),
            room_short_nights=Subquery(room_short_nights, output_field=IntegerField()),
        ).filter(open_nights=nights).filter(
            Q(room_short_nights__isnull=True) | Q(room_short_nights=0)
        )

        return queryset.filter(
            id__in=bookable_rate_plans.values('room_type__property_id')
        )

    def _apply_sorting(self, queryset, sort_method, search_params):
        """
        Izlew nátiyjelerine standartlastırılǵan minez benen tártiplewdi qollanıw.

        Argumentler:
            queryset: tiykarǵı queryset
            sort_method: tekserilgen tártiplew usılı
            search_params: kontekst ushın izlew parametrleri

        Qaytaradı:
            tártiplengen queryset
        """
        if sort_method == 'relevance':
            # Bar bolsa izlew rankı boyınsha, bolmasa created_at boyınsha tártiplew
            if hasattr(queryset.model, 'rank'):
                return queryset.order_by('-rank', '-created_at')
            return queryset.order_by('-created_at')

        elif sort_method == 'price_asc':
            return queryset.order_by('base_price', '-created_at')

        elif sort_method == 'price_desc':
            return queryset.order_by('-base_price', '-created_at')

        elif sort_method == 'rating':
            # Eń joqarı ortasha birinshi, bahalanbaǵanı aqırǵı; kóp sharh teń jaǵdayda jeńedi
            return queryset.order_by(
                F('average_rating').desc(nulls_last=True), '-review_count', '-created_at'
            )

        elif sort_method == 'reviews':
            return queryset.order_by(
                '-review_count', F('average_rating').desc(nulls_last=True), '-created_at'
            )

        elif sort_method == 'distance':
            # Izlew orayınan qashıqlıq boyınsha tártiplew (ápiwayılastırılǵan usıl)
            # Házirshe created_at boyınsha tártiplew, sebebi haqıyqıy qashıqlıq tártiplewi quramalı esaplawdı talap etedi
            return queryset.order_by('-created_at')

        # Ádetdegi tártiplew
        return queryset.order_by('-created_at')

    def get_search_suggestions(self, query, limit=5):
        """
        Avtotolıqtırıw ushın izlew usınısların alıw.

        Argumentler:
            query: bólekleyin izlew sorawı
            limit: usınıslardıń eń kóp sanı

        Qaytaradı:
            usınıs qatarları dizimi
        """
        from properties.models import Property

        if not query or len(query) < 2:
            return []

        # Ashıq mehmanxanaları bar orınlar (region, mámleket), terilgenge sáykes kelgen tilde atalǵan;
        # sol sebepli usınıs izlengende birdey mehmanxanalardı tabadı.
        # Sózlikke hesh qashan sáykeslenbegen mehmanxanalar óz tekst qala / mámleketine qaytadı.
        public = Property.objects.filter(is_active=True, is_deleted=False, status='active')
        suggestions = []

        def add(values):
            for value in values:
                if value and value not in suggestions:
                    suggestions.append(value)

        for level in GEOGRAPHY_LEVELS:
            for language in GEOGRAPHY_LANGUAGES:
                field = f'{level}__name_{language}'
                add(public.filter(**{f'{field}__icontains': query}).order_by(field)
                    .values_list(field, flat=True).distinct()[:limit])
        add(public.filter(city__icontains=query)
            .order_by('city').values_list('city', flat=True).distinct()[:limit])
        add(public.filter(country_ref__isnull=True, country__icontains=query)
            .order_by('country').values_list('country', flat=True).distinct()[:limit])
        return suggestions[:limit]
