"""
TICKBRON bron endpoint leri ushın serializer ler.
"""
import logging
from common.validators import validate_person_name
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.db import DatabaseError
from common.dates import business_today
from bookings.arrival import arrival_deadline, arrival_time_error
from bookings.notices import tell_booked, tell_cancelled_by_guest
from bookings.pricing import refusal_reason
from users.serializers import validate_phone_number_format
from currency.rates import ExchangeRateUnavailable
from .models import Booking, BookingItem
from django.utils.translation import gettext as _

logger = logging.getLogger('tickbron')


class BookingItemSerializer(serializers.ModelSerializer):
    """Bron elementleri ushın serializer."""

    room_type_name = serializers.CharField(source='room_type.name', read_only=True)
    rate_plan_name = serializers.CharField(source='rate_plan.name', read_only=True)

    class Meta:
        model = BookingItem
        fields = [
            'id', 'room_type', 'room_type_name', 'rate_plan', 'rate_plan_name',
            'number_of_rooms', 'price_per_night', 'currency'
        ]
        read_only_fields = ['id']


class BookingSerializer(serializers.ModelSerializer):
    """Bronlar ushın serializer."""

    booking_items = BookingItemSerializer(many=True, read_only=True)
    guest_name = serializers.CharField(source='guest.get_full_name', read_only=True)
    property_name = serializers.CharField(source='property.display_name', read_only=True)
    exchange_rate = serializers.SerializerMethodField()
    arrival_deadline = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id', 'guest', 'guest_name', 'property', 'property_name',
            'status', 'payment_status', 'check_in', 'check_out',
            'number_of_nights', 'guest_count', 'total_price', 'currency',
            'special_requests', 'confirmation_code', 'cancelled_at',
            'cancellation_reason', 'expires_at', 'booking_items', 'created_at', 'updated_at',
            'guest_full_name', 'guest_phone', 'guest_email', 'number_of_rooms', 'children',
            'charge_amount', 'charge_currency', 'exchange_rate',
            'expected_arrival_time', 'arrived_at', 'arrival_deadline',
        ]
        # Tek shıǵıw serializer i: bronlar BookingCreateSerializer arqalı jaratıladı
        # hám tek model metodları arqalı ózgeredi, soraw maǵlıwmatınan hesh qashan jazılmaydı.
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.DATETIME)
    def get_arrival_deadline(self, obj):
        """Mehmann qashan kelmedi dep esaplanadı (ISO, is waqtı), yamasa eski bron ushın null."""
        deadline = arrival_deadline(obj)
        return deadline.isoformat() if deadline else None

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_exchange_rate(self, obj):
        """Alınatuǵın summa esaplanǵan kurs (R6 snapshot), quote formatında."""
        return {
            'rate': f'{obj.exchange_rate:.6f}',
            'date': obj.exchange_rate_date.isoformat() if obj.exchange_rate_date else None,
            'source': obj.exchange_rate_source,
            'stale': obj.exchange_rate_stale,
        }


class BookingCreateSerializer(serializers.Serializer):
    """Transaction qáwipsiz inventory qulıplaw menen bron jaratıw ushın serializer."""

    property_id = serializers.IntegerField()
    room_type_id = serializers.IntegerField()
    rate_plan_id = serializers.IntegerField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    guest_count = serializers.IntegerField(min_value=1)
    special_requests = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    # Mehmannıń baylanıs maǵlıwmatı (ıqtıyarıy - paydalanıwshı profilinen aldınan toltırıladı)
    guest_full_name = serializers.CharField(
        required=False, allow_blank=True, max_length=300, validators=[validate_person_name],
    )  # baǵanıń ólshemi
    guest_phone = serializers.CharField(required=False, allow_blank=True)
    # Mehmanxanada naqd: mehmann kiriw kúni qaysı waqıtta keledi (HH:MM)
    expected_arrival_time = serializers.TimeField(input_formats=['%H:%M', '%H:%M:%S'])
    guest_email = serializers.EmailField(required=False, allow_blank=True)

    # Xona hám balalar maǵlıwmatı
    number_of_rooms = serializers.IntegerField(min_value=1, max_value=10, default=1)
    children = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=17),
        required=False,
        allow_empty=True
    )

    def validate_guest_phone(self, value):
        """Bos bolsa profil nomeri paydalanıladı (bron ekewiniń birewin talap etedi); E.164 formatında saqlanadı."""
        if not value.strip():
            return ''
        return validate_phone_number_format(value)

    def validate(self, data):
        """Bron jaratıw parametrlerin tekseriw."""
        from properties.models import Property, RoomType, RatePlan

        arrival_error = arrival_time_error(data['check_in'], data['expected_arrival_time'])
        if arrival_error:
            raise serializers.ValidationError({'expected_arrival_time': arrival_error})

        if not (data.get('guest_phone') or self.context['request'].user.phone_number):
            raise serializers.ValidationError({'guest_phone': _('A phone number is required.')})

        # Sana aralıǵın tekseriw
        if data['check_out'] <= data['check_in']:
            raise ValidationError({
                'check_out': _('Check-out date must be after check-in date')
            })

        if data['check_in'] < business_today():
            raise ValidationError({
                'check_in': _('Check-in date cannot be in the past')
            })

        # Mehmanxananıń bar hám aktiv ekenin tekseriw
        try:
            # Tek tastıyıqlanǵan (status='active') mehmanxanalardı bronlaw múmkin
            property_obj = Property.objects.get(
                id=data['property_id'],
                status='active',
                is_active=True,
                is_deleted=False
            )
        except Property.DoesNotExist:
            raise ValidationError({
                'property_id': _('Property not found or not available')
            })

        # Xona túriniń bar hám mehmanxanaǵa tiyisli ekenin tekseriw
        try:
            room_type = RoomType.objects.get(
                id=data['room_type_id'],
                property=property_obj,
                is_deleted=False
            )
        except RoomType.DoesNotExist:
            raise ValidationError({
                'room_type_id': _('Room type not found or does not belong to this property')
            })

        # Rate plan nıń bar hám xona túrine tiyisli ekenin tekseriw
        try:
            rate_plan = RatePlan.objects.get(
                id=data['rate_plan_id'],
                room_type=room_type,
                is_active=True,
                is_deleted=False
            )
        except RatePlan.DoesNotExist:
            raise ValidationError({
                'rate_plan_id': _('Rate plan not found or does not belong to this room type')
            })

        # Mehmanlar sanın barlıq bronlanǵan xonalardıń sıyımlılıǵı menen tekseriw
        capacity = room_type.max_occupancy * data.get('number_of_rooms', 1)
        if data['guest_count'] > capacity:
            raise ValidationError({
                'guest_count': _('Guest count exceeds maximum occupancy of %(capacity)s for the booked rooms') % {'capacity': capacity}
            })

        # Rate plan shekleulerin tekseriw
        number_of_nights = (data['check_out'] - data['check_in']).days

        if rate_plan.min_nights and number_of_nights < rate_plan.min_nights:
            raise ValidationError({
                'check_in': _('Booking duration is less than minimum nights requirement (%(nights)s)') % {'nights': rate_plan.min_nights}
            })

        if rate_plan.max_nights and number_of_nights > rate_plan.max_nights:
            raise ValidationError({
                'check_in': _('Booking duration exceeds maximum nights requirement (%(nights)s)') % {'nights': rate_plan.max_nights}
            })

        # Tekserilgen obyektlerdi keyingi paydalanıw ushın saqlaw
        self.validated_objects = {
            'property': property_obj,
            'room_type': room_type,
            'rate_plan': rate_plan
        }

        return data

    def create(self, validated_data):
        """Transaction qáwipsiz inventory qulıplaw menen bron jaratıw."""
        guest = self.context['request'].user
        property_obj = self.validated_objects['property']
        room_type = self.validated_objects['room_type']
        rate_plan = self.validated_objects['rate_plan']

        # Berilmegen bolsa, mehmann maǵlıwmatın paydalanıwshı profilinen aldınan toltırıw
        guest_full_name = validated_data.get('guest_full_name') or guest.get_full_name()
        guest_phone = validated_data.get('guest_phone') or guest.phone_number
        guest_email = validated_data.get('guest_email') or guest.email

        try:
            booking = Booking.create_booking(
                guest=guest,
                property_obj=property_obj,
                room_type=room_type,
                rate_plan=rate_plan,
                check_in=validated_data['check_in'],
                check_out=validated_data['check_out'],
                guest_count=validated_data['guest_count'],
                special_requests=validated_data.get('special_requests'),
                guest_full_name=guest_full_name,
                guest_phone=guest_phone,
                guest_email=guest_email,
                number_of_rooms=validated_data.get('number_of_rooms', 1),
                children=validated_data.get('children', []),
                expected_arrival_time=validated_data['expected_arrival_time'],
                confirmed=True,
            )
            tell_booked(booking)
            return booking
        except ExchangeRateUnavailable:
            raise
        except ValidationError as e:
            # Django ValidationError di DRF ValidationError ge ózgertiw
            if hasattr(e, 'message_dict'):
                refused = serializers.ValidationError(e.message_dict)
                refused.reason = refusal_reason(e)  # view onı alıp ótedi, sonda sayt biykar etiwdi awdara aladı
                raise refused
            else:
                raise serializers.ValidationError({'non_field_errors': str(e)})
        except DatabaseError:
            # Toqtap qalıw server qátesi (5xx), mehmann formanı qayta jiberip túzete almaytuǵın nárse
            raise
        except Exception:
            # Kútilmegen/ishki qátelik: str(e) di klientke hesh qashan qaytarmań, tek serverde log qa jazıń.
            logger.exception('Unexpected error creating booking')
            raise serializers.ValidationError({
                'non_field_errors': _('Failed to create booking. Please try again.')
            })


class BookingCancelSerializer(serializers.Serializer):
    """Bronlardı biykar etiw ushın serializer."""

    cancellation_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, data):
        """Biykar etiw parametrlerin tekseriw."""
        booking = self.context['booking']

        if booking.status in ['cancelled', 'completed', 'no_show']:
            raise ValidationError({
                'status': _('Booking cannot be cancelled in current status')
            })

        # Turıw baslanǵannan keyin biykar etiw mehmann paydalanǵan xonalardı bosatıp, alınǵan
        # pulǵa tiymey qaldırar edi; bul jaǵdaydı mehmanxana hám qollap-quwatlaw qolda sheshedi
        if booking.status == 'confirmed' and booking.check_in <= business_today():
            raise ValidationError({
                'status': _('A stay that has started cannot be cancelled online. Please contact the hotel.')
            })

        return data

    def update(self, instance, validated_data):
        """Bronnan bas tartıw hám inventory di qaytarıw."""
        try:
            instance.cancel_booking(validated_data.get('cancellation_reason'))
            tell_cancelled_by_guest(instance)
            return instance
        except ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        except DatabaseError:
            raise
        except Exception:
            logger.exception('Unexpected error cancelling booking')
            raise serializers.ValidationError({
                'non_field_errors': _('Failed to cancel booking. Please try again.')
            })
