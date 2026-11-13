"""
Admin API endpoint leri ushın view ler.

Bul modul mehmanxana moderation ı, paydalanıwshılardı basqarıw,
amenity di basqarıw hám tólemdi baqlaw view lerin óz ishine aladı.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import routers, serializers, viewsets, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import (
    Count, Exists, Max, Q, F, OuterRef, Subquery, Value, Case, When, CharField
)
from django.db.models.functions import TruncMonth, ExtractYear, Coalesce, Concat, Lower, NullIf, Trim
from datetime import timedelta
from properties.listing import missing_for_listing
from properties.models import Property, PropertyTranslation, Amenity, AmenityCategory
from partner import commission
from users import two_factor
from users.models import User
from users.throttles import TwoFactorResetThrottle
from bookings.models import Booking
from admin_panel.audit import AuditedModelViewSetMixin
from accounts.notifications import notify
from admin_panel.models import AdminAccessLog, InternalNote
from common.alphabet import DISPLAY_NAME, hotels_with_letter, letter_from, letter_q, people_with_letter
from common.dates import business_today
from common.request import object_body
from common.security_log import log_security_event
from admin_panel.serializers import (
    AdminPropertySerializer, AdminPropertyApproveSerializer, AdminPropertyRegionSerializer,
    AdminUserSerializer, AdminUserCreateSerializer, AdminStaffCreateSerializer, AdminContactSerializer,
    AdminAmenityCategorySerializer, AdminAmenitySerializer,
    AdminAmenityReadSerializer,
    AdminCustomerSerializer,
    AdminCustomerDetailSerializer,
    AdminBookingSummarySerializer,
    AdminInternalNoteSerializer,
    AdminInternalNoteCreateSerializer
)
from django.utils.translation import gettext as _


class IsSuperAdminOrStaff(IsAuthenticated):
    """
    Paydalanıwshınıń super-admin yamasa staff ekenin támiyinleytuǵın ruxsat.

    Super-admin lerde tolıq kirisiw bar, staff ta shekli.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        # Paydalanıwshınıń staff ekenin tekseriw
        if request.user.is_staff:
            return True

        return False


class IsSuperAdmin(IsAuthenticated):
    """
    Paydalanıwshınıń super-admin ekenin támiyinleytuǵın ruxsat.

    Bul endpoint lerge tek super-admin ler (is_superuser=True) kire aladı.
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        # Paydalanıwshınıń superuser ekenin tekseriw
        if request.user.is_superuser:
            return True

        return False


HOTEL_OWNER_ROLE = 'hotel-owner'


class AdminAPIRootView(routers.APIRootView):
    """Router diń endpoint dizimi; ádetdegisi kirgen qálegen paydalanıwshıǵa ashıq."""
    permission_classes = [IsSuperAdminOrStaff]


class AdminPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ler mehmanxana moderation ı ushın ViewSet.

    Moderation maqsetinde barlıq mehmanxanalarǵa tek oqıw kirisiwi.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminPropertySerializer

    def get_queryset(self):
        """
        Moderation ushın barlıq mehmanxanalar. Query: ?letter= (qálegen tildegi mehmanxana atınıń birinshi háripi, yamasa #),
        ?status= (pending, active, suspended, ...), ?search= (qálegen tildegi at yamasa city).
        """
        params = self.request.query_params
        properties = hotels_with_letter(
            Property.objects.filter(is_deleted=False).select_related('owner', 'property_type', 'approved_by'),
            letter_from(self.request))
        hotel_status = (params.get('status') or '').strip()
        if hotel_status:
            properties = properties.filter(status=hotel_status)
        term = (params.get('search') or '').strip()[:SEARCH_LENGTH]
        if term:
            named = PropertyTranslation.objects.filter(property=OuterRef('pk'), name__icontains=term)
            properties = properties.filter(Exists(named) | Q(city__icontains=term))
        return properties


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_property_approve(request, property_id):
    """
    Mehmanxananı dizimge tastıyıqlaw.

    Path parametrleri:
        property_id: mehmanxana ID si

    Request body:
        rejection_reason: biykar etiw sebebi (ıqtıyarıy, tek biykar etkende)

    Qaytaradı:
        Tastıyıqlaw statusı menen jańalanǵan mehmanxana
    """
    property = get_object_or_404(Property, id=property_id, is_deleted=False)

    serializer = AdminPropertyApproveSerializer(data=request.data)

    if serializer.is_valid():
        rejection_reason = serializer.validated_data.get('rejection_reason', '')

        if rejection_reason:
            # Mehmanxananı biykar etiw
            property.status = 'rejected'
            property.rejection_reason = rejection_reason
            property.approved_by = None
            property.approved_at = None
        else:
            missing = missing_for_listing(property)
            if missing:
                return Response(
                    {'error': _('Property is not ready to be listed'), 'missing': missing},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            property.status = 'active'
            property.rejection_reason = ''
            property.approved_by = request.user
            property.approved_at = timezone.now()

        property.save()
        AdminAccessLog.record(
            request.user, 'property_reject' if rejection_reason else 'property_approve',
            details={'property_id': property.id},
        )

        return Response(
            AdminPropertySerializer(property).data,
            status=status.HTTP_200_OK
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH'])
@permission_classes([IsSuperAdminOrStaff])
def admin_property_region(request, property_id):
    """
    Mehmanxananıń jaylasıwın belgilew (Status bólimi: mámleket > region > mehmanxana).

    Request body (eki forma da bolıwı múmkin):
        country_ref, region_ref: Geography id leri (ekewi null bolsa tazalanadı)
        state: region atı; bos yamasa null bolsa tazalanadı ("Unspecified"); tek eski klientler ushın

    Tek jaylasıw ózgeredi; body degi basqa hár maydan itibarǵa alınbaydı.
    """
    property = get_object_or_404(Property, id=property_id, is_deleted=False)
    serializer = AdminPropertyRegionSerializer(data=request.data, context={'property': property})
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    refs = [name for name in ('country_ref', 'region_ref') if name in data]
    if refs:
        for name in refs:
            setattr(property, name, data[name])
        if all(data.get(name) is None for name in refs) and len(refs) == 2:
            property.state = None
        # Property.save() ref lerdiń inglizsha atların country / state ge kóshiredi
        property.save()
    else:
        property.state = data['state']
        property.save(update_fields=['state', 'updated_at'])
    AdminAccessLog.record(request.user, 'property_region_update', details={'property_id': property.id})
    return Response(AdminPropertySerializer(property).data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_property_suspend(request, property_id):
    """
    Mehmanxananı toqtatıw.

    Path parametrleri:
        property_id: mehmanxana ID si

    Qaytaradı:
        Toqtatılǵan statusı menen jańalanǵan mehmanxana
    """
    property = get_object_or_404(Property, id=property_id, is_deleted=False)

    property.status = 'suspended'
    property.save()
    AdminAccessLog.record(request.user, 'property_suspend', details={'property_id': property.id})

    return Response(
        AdminPropertySerializer(property).data,
        status=status.HTTP_200_OK
    )


class AdminListPagination(PageNumberPagination):
    """Panellerdiń dizimleri: bir betke 50, soralsa 100 ge shekem."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


USER_ROLES = ('guest', 'owner', 'staff', 'super_admin')
SEARCH_LENGTH = 100


def users_of_role(queryset, role):
    """Paydalanıwshılardı akkaunttıń bir túrine shekemlew; túrler bir-birine tuspeydi."""
    if role == 'super_admin':
        return queryset.filter(is_superuser=True)
    if role == 'staff':
        return queryset.filter(is_staff=True, is_superuser=False)
    if role == 'owner':
        return queryset.filter(is_staff=False, is_superuser=False, role__name=HOTEL_OWNER_ROLE)
    return queryset.filter(is_staff=False, is_superuser=False).exclude(role__name=HOTEL_OWNER_ROLE)


class AdminUserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin ler paydalanıwshılardı basqarıw ushın ViewSet.

    Tek oqıw, bir waqıtta bir bet, kórsetilgen at tıń alfavit tártibinde. Query: ?letter= (kórsetilgen
    attıń birinshi háripi, yamasa háripsiz ushın #), ?search= (at, e-mail yamasa telefon), ?role=
    guest|owner|staff|super_admin,
    ?page=, ?page_size= (100 ge shekem).
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminUserSerializer
    pagination_class = AdminListPagination

    def get_queryset(self):
        """Basqarıw ushın paydalanıwshılar, query menen shekemlengen."""
        params = self.request.query_params
        users = people_with_letter(User.objects.filter(is_deleted=False).select_related('role'), letter_from(self.request))
        role = (params.get('role') or '').strip()
        if role:
            if role not in USER_ROLES:
                raise ValidationError({'role': [_('Choose one of: guest, owner, staff, super_admin.')]})
            users = users_of_role(users, role)
        term = (params.get('search') or '').strip()[:SEARCH_LENGTH]
        if term:
            users = users.filter(
                Q(full_name__icontains=term) | Q(first_name__icontains=term) | Q(last_name__icontains=term)
                | Q(email__icontains=term) | Q(phone_number__icontains=term))
        return users.annotate(sort_name=Lower(DISPLAY_NAME)).order_by('sort_name', 'id')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        AdminAccessLog.record(request.user, 'user_list')
        return response


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def admin_create_hotel_owner(request):
    """
    Mehmanxana iyesi akkaunt ın jaratıw (tek super-admin).

    Bul endpoint super-admin lerge mehmanxana iyesi akkaunt ların óz-ózinen dizimnen ótiwsiz
    tikkeley jaratıwǵa múmkinshilik beredi. Akkaunt mehmanxana iyesi roli menen jaratıladı
    hám berilgen kirisiw maǵlıwmatları menen birden paydalanıwǵa tayar boladı.

    Request body:
        email: mehmanxana iyesiniń e-mail ı (májbúriy)
        first_name: Atı (májbúriy)
        last_name: Familiyası (májbúriy)
        phone_number: Telefon nomeri (májbúriy)
        country_ref, region_ref: iyeniń mehmanxanaları jaylasatuǵın orın (májbúriy, bir-birine sáykes bolıwı kerek)
        commission_percent: sayt hár bronnan ne aladı, 0 den 100 ge shekem (májbúriy)
        password: Dáslepki parol (májbúriy, eń kemi 8 belgi)
        password_confirm: Parol tastıyıqlawı (májbúriy)

    Qaytaradı:
        Mehmanxana iyesi rolindegi jaratılǵan paydalanıwshı obyekti
    """
    serializer = AdminUserCreateSerializer(data=request.data)

    if serializer.is_valid():
        with transaction.atomic():
            user = serializer.save()
            commission.set_percent(user, serializer.validated_data['commission_percent'], request.user)
        AdminAccessLog.record(request.user, 'hotel_owner_create', target_user_id=user.id)
        return Response(
            AdminUserSerializer(user).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def admin_create_admin(request):
    """
    Basqa administrator qosıw (tek super-admin). Jańa akkaunt staff boladı, hesh qashan super-admin emes;
    soraw bunı ózgerte almaydı. Body: email, first_name, last_name, phone_number, password,
    password_confirm. Admin kirisiw logına jazıladı.
    """
    serializer = AdminStaffCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    user = serializer.save()
    AdminAccessLog.record(request.user, 'admin_create', target_user_id=user.id,
                          details={'role': serializer.validated_data['role']})
    return Response(AdminUserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PATCH'])
@permission_classes([IsSuperAdminOrStaff])
def admin_change_contact(request, user_id):
    """
    Akkauttıń telefon nomerin hám/yamasa e-mail ın ózgertiw (super admin yamasa staff). Body: phone_number, email.
    Staff admin mehmanlardı hám mehmanxana iyelerin ózgerte aladı; super admin staff adminlerdi de ózgerte aladı. Super
    admin niń baylanıs maǵlıwmatın bul jerde ózgertip bolmaydı. Jańa e-mail akkauntti tastıyıqlanbaǵan etip belgileydi hám
    onı
    hámme jerden shıǵaradı. Admin kirisiw logına jazıladı (qaysı maydanlar, mánisler hesh qashan).
    """
    target = get_object_or_404(User.objects.filter(is_deleted=False), pk=user_id)
    allowed_over_staff = request.user.is_superuser
    if target.is_superuser or (target.is_staff and not allowed_over_staff):
        return Response({'detail': _('You cannot change the contact details of this account.')},
                        status=status.HTTP_403_FORBIDDEN)
    serializer = AdminContactSerializer(data=object_body(request), account=target)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    changed = serializer.validated_data
    for field, value in changed.items():
        setattr(target, field, value)
    if 'email' in changed:
        target.email_verified = False
    target.save(update_fields=list(changed) + (['email_verified'] if 'email' in changed else []))
    if 'email' in changed:
        two_factor.end_sessions(target)
    AdminAccessLog.record(request.user, 'user_contact_update', target_user_id=target.id,
                          details={'fields': ','.join(sorted(changed))})
    return Response(AdminUserSerializer(target).data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdmin])
@throttle_classes([TwoFactorResetThrottle])
def admin_reset_two_factor(request, user_id):
    """
    Telefon joǵalǵannan keyin basqa akkauttıń eki basqıshlı kirisiwin qayta ornatıw (tek super-admin). Body: code,
    super admin niń ÓZ házirgi ilova kodı, sol sebepli tek urlanǵan session menen bunı islep bolmaydı. Akkaunt
    hámme jerden shıǵarıladı hám keyingi kirisiwinde qayta sazlaydı. Super admin niń óz eki basqıshlı kirisiwin bul jerde
    qayta ornatıp bolmaydı: ol serverde isleniledi (`manage.py reset_2fa`). Admin kirisiw logına jazıladı.
    """
    code = object_body(request).get('code')
    if not (request.user.two_factor_enabled and isinstance(code, str) and two_factor.accept_code(request.user, code)):
        return Response({'detail': _('Enter your own current two-step code.')}, status=status.HTTP_400_BAD_REQUEST)
    target = get_object_or_404(User.objects.filter(is_deleted=False), pk=user_id)
    if target.is_superuser:
        return Response(
            {'detail': _("A super admin's two-step sign-in can only be reset on the server.")},
            status=status.HTTP_403_FORBIDDEN)
    if not target.two_factor_enabled:
        return Response({'detail': _('Two-step sign-in is not on for this account.')}, status=status.HTTP_400_BAD_REQUEST)
    two_factor.reset(target)
    AdminAccessLog.record(request.user, 'two_factor_reset', target_user_id=target.id)
    notify(target, 'two_factor_reset', {})
    log_security_event('two_factor_reset', request, target=target.pk)
    return Response(AdminUserSerializer(target).data)


class AdminAmenityCategoryViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    """
    Admin ler amenity kategoriyaların basqarıw ushın ViewSet.

    Amenity kategoriyaları ushın tolıq CRUD kirisiwi.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminAmenityCategorySerializer
    audit_name = 'amenity_category'

    def get_queryset(self):
        """Barlıq amenity kategoriyaların qaytaradı."""
        return AmenityCategory.objects.filter(is_deleted=False)


class AdminAmenityViewSet(AuditedModelViewSetMixin, viewsets.ModelViewSet):
    """
    Admin ler amenity lerdi basqarıw ushın ViewSet.

    Amenity ler ushın tolıq CRUD kirisiwi.
    """
    permission_classes = [IsSuperAdminOrStaff]
    serializer_class = AdminAmenitySerializer
    audit_name = 'amenity'

    def get_serializer_class(self):
        """Háreketke qarap tiyisli serializer di qaytaradı."""
        if self.action in ['list', 'retrieve']:
            # Oqıw ámelleri ushın ishki kategoriyası bar serializer di paydalanıw
            return AdminAmenityReadSerializer
        return AdminAmenitySerializer

    def get_queryset(self):
        """Barlıq amenity lerdi qaytaradı."""
        return Amenity.objects.filter(is_deleted=False).select_related('category')


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_booking_lookup_by_reference(request):
    """
    Mijozdıń tolıq maǵlıwmatın hám bronın reference code boyınsha izlew.

    Bul endpoint staff/qollap-quwatlaw ushın: mehmann mehmanxanada mashqala haqqında
    xabarlasqanda hám bron reference code in aytıp qollap-quwatlawǵa qońıraw etkende.

    Query parametrleri:
        reference_code: 6 belgili bron reference code (májbúriy)

    Qaytaradı:
        Tolıq bron maǵlıwmatı, olardıń ishinde:
        - Mijoz maǵlıwmatı (at, baylanıs)
        - Mehmanxana hám xona maǵlıwmatı
        - Bron sanaları hám status
        - Tólem statusı
    """
    reference_code = request.query_params.get('reference_code')

    if not reference_code:
        return Response(
            {'error': 'reference_code parameter is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Bron di reference code boyınsha izlew
    try:
        booking = Booking.objects.select_related(
            'guest', 'property', 'property__property_type', 'property__owner'
        ).prefetch_related(
            'booking_items__room_type', 'booking_items__rate_plan'
        ).get(
            confirmation_code=reference_code.upper(),
            is_deleted=False
        )
    except Booking.DoesNotExist:
        return Response(
            {'error': _('Booking not found with this reference code')},
            status=status.HTTP_404_NOT_FOUND
        )

    # Tolıq juwap qurıw
    booking_items_data = []
    for item in booking.booking_items.all():
        booking_items_data.append({
            'room_type': {
                'id': item.room_type.id,
                'name': item.room_type.name,
                'description': item.room_type.description,
                'base_occupancy': item.room_type.base_occupancy,
                'max_occupancy': item.room_type.max_occupancy,
            },
            'rate_plan': {
                'id': item.rate_plan.id,
                'name': item.rate_plan.name,
                'rate_type': item.rate_plan.rate_type,
                'description': item.rate_plan.description,
            },
            'number_of_rooms': item.number_of_rooms,
            'price_per_night': str(item.price_per_night),
            'currency': item.currency,
        })

    response_data = {
        'booking': {
            'id': booking.id,
            'reference_code': booking.confirmation_code,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'check_in': booking.check_in,
            'check_out': booking.check_out,
            'number_of_nights': booking.number_of_nights,
            'guest_count': booking.guest_count,
            'total_price': str(booking.total_price),
            'currency': booking.currency,
            'special_requests': booking.special_requests,
            'cancelled_at': booking.cancelled_at,
            'cancellation_reason': booking.cancellation_reason,
            'expires_at': booking.expires_at,
            'created_at': booking.created_at,
            'updated_at': booking.updated_at,
            'guest_full_name': booking.guest_full_name,
            'guest_phone': booking.guest_phone,
            'guest_email': booking.guest_email,
            'number_of_rooms': booking.number_of_rooms,
            'children': booking.children,
            'booking_items': booking_items_data,
        },
        'customer': {
            'id': booking.guest.id,
            'full_name': booking.guest.get_full_name(),
            'email': booking.guest.email,
            'phone_number': booking.guest.phone_number,
            'whatsapp': booking.guest.whatsapp,
            'telegram': booking.guest.telegram,
            'preferred_contact_method': booking.guest.preferred_contact_method,
        },
        'property': {
            'id': booking.property.id,
            'name': booking.property.display_name(),
            'property_type': booking.property.property_type.name if booking.property.property_type else None,
            'status': booking.property.status,
            'address_line1': booking.property.address_line1,
            'city': booking.property.city,
            'state': booking.property.state,
            'country': booking.property.country,
            'base_price': str(booking.property.base_price),
            'currency': booking.property.currency,
            'owner': {
                'id': booking.property.owner.id,
                'full_name': booking.property.owner.get_full_name(),
                'email': booking.property.owner.email,
            } if booking.property.owner else None,
        },
    }

    AdminAccessLog.record(
        request.user, 'booking_lookup', target_user_id=booking.guest_id, target_booking_id=booking.id,
    )
    return Response(response_data, status=status.HTTP_200_OK)


class AdminCustomerPagination(PageNumberPagination):
    """
    Admin mijozlar dizimi ushın óz pagination ı.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT, operation_id='v1_admin_panel_customers_list')
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_customers_directory(request):
    """
    Bron jıynaqları menen mijozlar dizimi ushın admin API.

    Hár mijoz ushın qaytaradı:
    - mijoz ID si, dizimnen ótken sana, tolıq at, telefon, e-mail, whatsapp, telegram, qálegen baylanıs usılı
    - bronlardıń jámi sanı, sońǵı bron sanası, tólengen jámi summa, mijoz statusı

    Query parametrleri:
        search: at, telefon, e-mail yamasa mijoz ID si boyınsha izlew (ıqtıyarıy)
        page: Bet nomeri (ádetde: 1)
        page_size: Bettegi elementler sanı (ádetde: 20, eń kóbi: 100)
        sort_by: Tártiplew maydanı (ádetde: registration_date)
        sort_order: Tártiplew baǵıtı (asc yamasa desc, ádetde: desc)

    Qaytaradı:
        Bron jıynaqları menen mijozlardıń betlerge bólingen dizimi
    """
    # Query parametrlerin alıw
    search = request.query_params.get('search', '').strip()
    page = request.query_params.get('page', 1)
    sort_by = request.query_params.get('sort_by', 'registration_date')
    sort_order = request.query_params.get('sort_order', 'desc')

    # sort_order di tekseriw
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'

    # sort_by maydanın tekseriw
    valid_sort_fields = [
        'registration_date', 'full_name', 'email', 'total_booking_count',
        'last_booking_date', 'customer_status'
    ]
    if sort_by not in valid_sort_fields:
        sort_by = 'registration_date'

    # Jıynaqlar baylanıslı sub-query ler arqalı keledi, sol sebepli bir mijoz eki ret esaplanbaydı
    customer_bookings = Booking.objects.filter(
        guest=OuterRef('pk'), is_deleted=False
    ).order_by().values('guest')

    # Aktiv: is_active=True hám (sońǵı 90 kúnde broni bar YAMASA ele bronları joq)
    # Aktiv emes: is_active=False YAMASA (is_active=True hám sońǵı bron 90 kúnnen aldın)
    threshold_date = timezone.now() - timedelta(days=90)

    # Staff, super-admin ler hám mehmanxana iyeleri mijoz emes
    users = User.objects.filter(
        is_deleted=False, is_staff=False, is_superuser=False
    ).exclude(role__name=HOTEL_OWNER_ROLE).annotate(
        total_booking_count=Coalesce(
            Subquery(customer_bookings.annotate(c=Count('id')).values('c')), 0
        ),
        last_booking_date=Subquery(customer_bookings.annotate(m=Max('created_at')).values('m')),
        # User.get_full_name() penen birdey zapas jol: full_name, bolmasa first + last, bolmasa email
        display_name=Coalesce(
            NullIf('full_name', Value('')),
            NullIf(Trim(Concat('first_name', Value(' '), 'last_name')), Value('')),
            'email',
            output_field=CharField(),
        ),
    ).annotate(
        customer_status=Case(
            When(is_active=False, then=Value('inactive')),
            When(last_booking_date__lt=threshold_date, then=Value('inactive')),
            default=Value('active'),
            output_field=CharField(),
        ),
    )

    letter = letter_from(request)
    if letter is not None:
        users = users.filter(letter_q('display_name', letter))

    # Izlew filter in qollanıw
    if search:
        users = users.filter(
            Q(full_name__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(email__icontains=search) |
            Q(id__icontains=search)
        )

    # Database de tártiplew; id teń jaǵdaylardı ajıratadı, sol sebepli betler turaqlı boladı
    sort_expressions = {
        'registration_date': F('date_joined'),
        'full_name': Lower('display_name'),
        'email': F('email'),
        'total_booking_count': F('total_booking_count'),
        'last_booking_date': F('last_booking_date'),
        'customer_status': F('customer_status'),
    }
    sort_expression = sort_expressions[sort_by]
    if sort_order == 'asc':
        users = users.order_by(sort_expression.asc(nulls_last=True), 'id')
    else:
        users = users.order_by(sort_expression.desc(nulls_last=True), '-id')

    # Queryset ti betlerge bóliw, sonda paydalanıwshılardıń tek bir beti júklenedi
    paginator = AdminCustomerPagination()
    page = paginator.paginate_queryset(users, request)

    paginated_data = [
        {
            'id': user.id,
            'registration_date': user.date_joined,
            'full_name': user.get_full_name(),
            'phone': user.phone_number,
            'email': user.email,
            'whatsapp': user.whatsapp,
            'telegram': user.telegram,
            'preferred_contact_method': user.preferred_contact_method,
            'total_booking_count': user.total_booking_count,
            'last_booking_date': user.last_booking_date,
            'customer_status': user.customer_status,
        }
        for user in page
    ]

    # Betlerge bólingen maǵlıwmattı serializer den ótkiziw
    serializer = AdminCustomerSerializer(paginated_data, many=True)

    AdminAccessLog.record(request.user, 'customer_list')
    return paginator.get_paginated_response(serializer.data)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_customer_detail(request, customer_id):
    """
    Bir mijozdıń tolıq profili ushın admin API.

    Qaytaradı:
    - Baylanıs maǵlıwmatı (tolıq profil)
    - all/upcoming/completed/cancelled boyınsha filterlenetuǵın barlıq bronlar
    - Sońǵı aktivlik waqıt belgisi
    - Ishki jazbalar (tek staff)

    Query parametrleri:
        booking_filter: Bronlardı status boyınsha filterlew (all, upcoming, completed, cancelled)

    Path parametrleri:
        customer_id: Mijoz ID si
    """
    # Mijozdı alıw
    customer = get_object_or_404(User, id=customer_id, is_deleted=False)

    # Bron filter in alıw
    booking_filter = request.query_params.get('booking_filter', 'all')

    # Bronlar query sin qurıw
    bookings = Booking.objects.filter(
        guest=customer,
        is_deleted=False
    ).select_related('property').order_by('-created_at')

    # Bron filter in qollanıw
    if booking_filter == 'upcoming':
        bookings = bookings.filter(
            status='confirmed',
            check_in__gte=business_today()
        )
    elif booking_filter == 'completed':
        bookings = bookings.filter(status='completed')
    elif booking_filter == 'cancelled':
        bookings = bookings.filter(status='cancelled')
    # 'all' barlıq bronlardı qaytaradı

    # Bronlardı serializer den ótkiziw
    bookings_data = []
    for booking in bookings:
        bookings_data.append({
            'id': booking.id,
            'reference_code': booking.confirmation_code,
            'status': booking.status,
            'payment_status': booking.payment_status,
            'check_in': booking.check_in,
            'check_out': booking.check_out,
            'number_of_nights': booking.number_of_nights,
            'total_price': str(booking.total_price),
            'currency': booking.currency,
            'property_name': booking.property.display_name(),
            'property_city': booking.property.city,
            'created_at': booking.created_at
        })

    bookings_serializer = AdminBookingSummarySerializer(bookings_data, many=True)

    # Ishki jazbalardı alıw
    internal_notes = InternalNote.objects.filter(
        customer=customer,
        is_deleted=False
    ).select_related('author').order_by('-created_at')

    internal_notes_serializer = AdminInternalNoteSerializer(internal_notes, many=True)

    # Sońǵı aktivlik waqıt belgisin esaplaw
    # Sońǵı aktivlik mınalardıń eń jańası: last_login, sońǵı bronnıń created_at
    last_activities = []
    if customer.last_login:
        last_activities.append(customer.last_login)
    if bookings.exists():
        last_activities.append(bookings.first().created_at)

    last_activity = max(last_activities) if last_activities else None

    # Juwaptı qurıw
    response_data = {
        'customer': AdminCustomerDetailSerializer(customer).data,
        'bookings': bookings_serializer.data,
        'internal_notes': internal_notes_serializer.data,
        'last_activity': last_activity
    }

    AdminAccessLog.record(request.user, 'customer_view', target_user_id=customer.id)
    return Response(response_data, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrStaff])
def admin_internal_note_create(request, customer_id):
    """
    Mijoz ushın ishki jazba jaratıw.

    Path parametrleri:
        customer_id: Mijoz ID si

    Request body:
        note: Jazba mazmunı (májbúriy)

    Qaytaradı:
        Jaratılǵan ishki jazba
    """
    customer = get_object_or_404(User, id=customer_id, is_deleted=False)

    serializer = AdminInternalNoteCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if serializer.is_valid():
        note = serializer.save(customer=customer)
        AdminAccessLog.record(request.user, 'internal_note_create', target_user_id=customer.id,
                              details={'object_id': note.id})
        return Response(
            AdminInternalNoteSerializer(note).data,
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['PUT', 'DELETE'])
@permission_classes([IsSuperAdminOrStaff])
def admin_internal_note_detail(request, customer_id, note_id):
    """
    Ishki jazbanı jańalaw yamasa óshiriw.

    Path parametrleri:
        customer_id: Mijoz ID si
        note_id: Jazba ID si

    Request body (PUT ushın):
        note: Jańalanǵan jazba mazmunı (májbúriy)

    Qaytaradı:
        Jańalanǵan jazba (PUT ushın) yamasa 204 No Content (DELETE ushın)
    """
    customer = get_object_or_404(User, id=customer_id, is_deleted=False)
    note = get_object_or_404(
        InternalNote,
        id=note_id,
        customer=customer,
        is_deleted=False
    )

    if request.method == 'PUT':
        serializer = AdminInternalNoteSerializer(note, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            AdminAccessLog.record(request.user, 'internal_note_update', target_user_id=customer.id,
                                  details={'object_id': note.id})
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        note.soft_delete()
        AdminAccessLog.record(request.user, 'internal_note_delete', target_user_id=customer.id,
                              details={'object_id': note.id})
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_registration_statistics(request):
    """
    Dizimnen ótiw statistikası ushın admin API.

    Jańa dizimnen ótiw sanların mınaǵan bólip qaytaradı:
    - Júrip turatuǵın 12 ay aynası (aymaǵa)
    - Kalendar jıl (jılma-jıl)

    Query parametrleri:
        type: Bóliw túri (rolling_12_months yamasa calendar_year, ádetde: rolling_12_months)

    Qaytaradı:
        Sanlar hám dáwir belgileri menen dizimnen ótiw statistikası
    """
    stats_type = request.query_params.get('type', 'rolling_12_months')

    if stats_type == 'calendar_year':
        # Kalendar jıl boyınsha dizimnen ótiw sanın alıw
        yearly_stats = User.objects.filter(
            is_deleted=False
        ).annotate(
            year=ExtractYear('date_joined')
        ).values('year').annotate(
            count=Count('id')
        ).order_by('year')

        # Juwaptı formatlaw
        stats_data = [
            {
                'period': str(item['year']),
                'count': item['count']
            }
            for item in yearly_stats
        ]

        return Response({
            'type': 'calendar_year',
            'statistics': stats_data
        }, status=status.HTTP_200_OK)

    else:  # rolling_12_months (ádetde)
        # Júrip turatuǵın 12 ay aynasın alıw
        end_date = timezone.now()
        start_date = end_date - timedelta(days=365)

        # Júrip turatuǵın aynada ay boyınsha dizimnen ótiw sanın alıw
        monthly_stats = User.objects.filter(
            is_deleted=False,
            date_joined__gte=start_date,
            date_joined__lte=end_date
        ).annotate(
            month=TruncMonth('date_joined')
        ).values('month').annotate(
            count=Count('id')
        ).order_by('month')

        # Juwaptı ay belgileri menen formatlaw
        stats_data = []
        for item in monthly_stats:
            month_date = item['month']
            stats_data.append({
                'period': month_date.strftime('%Y-%m'),
                'count': item['count']
            })

        return Response({
            'type': 'rolling_12_months',
            'start_date': start_date,
            'end_date': end_date,
            'statistics': stats_data
        }, status=status.HTTP_200_OK)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_top_bookers_leaderboard(request):
    """
    Eń kóp bronlaǵan mijozlar reytingi ushın admin API.

    Mijozlardı tańlanatuǵın dáwir ishinde juwmaqlanǵan bronlar sanı boyınsha ráteleydi.
    Mijozdı sıylıqlaw/loyallıq baǵdarlamaların qollap-quwatlaw ushın arnalǵan.

    Query parametrleri:
        period: Reyting ushın waqıt dáwiri (this_month, this_year, all_time, ádetde: all_time)
        limit: Qaytarılatuǵın eń jaqsı mijozlardıń eń kóp sanı (ádetde: 10, eń kóbi: 100)

    Qaytaradı:
        Mijoz atı, bron sanı hám rat penen reyting
    """
    period = request.query_params.get('period', 'all_time')
    limit = request.query_params.get('limit', 10)

    # limit ti tekseriw hám tazalaw
    try:
        limit = int(limit)
        if limit < 1:
            limit = 10
        elif limit > 100:
            limit = 100
    except (ValueError, TypeError):
        limit = 10

    # Dáwirge qarap sana filter in qurıw
    now = timezone.now()

    if period == 'this_month':
        # Házirgi aydıń birinshi kúni
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        booking_filter = Q(
            bookings__is_deleted=False,
            bookings__status='completed',
            bookings__created_at__gte=start_date
        )
    elif period == 'this_year':
        # Házirgi jıldıń birinshi kúni
        start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        booking_filter = Q(
            bookings__is_deleted=False,
            bookings__status='completed',
            bookings__created_at__gte=start_date
        )
    else:  # 'all_time' sana filter ine iye emes
        booking_filter = Q(
            bookings__is_deleted=False,
            bookings__status='completed'
        )

    # Juwmaqlanǵan bronlar sanı menen eń jaqsı mijozlardı alıw
    top_bookers = User.objects.filter(
        is_deleted=False
    ).annotate(
        completed_booking_count=Count('bookings', filter=booking_filter)
    ).filter(
        completed_booking_count__gt=0
    ).order_by('-completed_booking_count')[:limit]

    # Reyting juwabın qurıw
    leaderboard_data = []
    for rank, user in enumerate(top_bookers, start=1):
        leaderboard_data.append({
            'rank': rank,
            'customer_id': user.id,
            'customer_name': user.get_full_name(),
            'completed_booking_count': user.completed_booking_count
        })

    return Response({
        'period': period,
        'limit': limit,
        'leaderboard': leaderboard_data
    }, status=status.HTTP_200_OK)


class AdminAccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminAccessLog
        fields = ['id', 'actor_id', 'action', 'target_user_id', 'target_booking_id', 'details', 'created_at']
        read_only_fields = fields


class AdminAccessLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrStaff])
def admin_access_log(request):
    """
    AdminAccessLog tiń tek staff ushın, tek oqıw view si, eń jańası birinshi.

    Filter ler: actor_id, target_user_id, target_booking_id (integer ler), action.
    Bul logtı oqıw ózi jazılmaydı (onda tek id ler bar, mijoz maǵlıwmatı joq).
    """
    entries = AdminAccessLog.objects.all()
    for name in ('actor_id', 'target_user_id', 'target_booking_id'):
        value = request.query_params.get(name)
        if value:
            if not value.isdigit():
                return Response({'error': f'{name} must be an integer'}, status=status.HTTP_400_BAD_REQUEST)
            entries = entries.filter(**{name: int(value)})
    action = request.query_params.get('action')
    if action:
        entries = entries.filter(action=action)

    paginator = AdminAccessLogPagination()
    page = paginator.paginate_queryset(entries, request)
    return paginator.get_paginated_response(AdminAccessLogSerializer(page, many=True).data)
