"""
TICKBRON ushın Booking model leri.

Bul modul bronlar, bron elementleri hám olarǵa baylanıslı dúzilislerdiń model lerin óz ishine aladı,
transaction qáwipsiz inventory qulıplaw hám qos bronlawdıń aldın alıw menen.
"""
import logging

from django.db import models, transaction
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils import timezone
from common.dates import business_today
from common.models import BaseModel
from common.money import CHARGE_CURRENCY, quantize, to_uzs
from currency.rates import ExchangeRateUnavailable, current_rate
from .state_machine import BookingStateMachine, BookingState

logger = logging.getLogger(__name__)


class ExpiredBookingProcessingError(Exception):
    """Bir yamasa birneshe bron múddeti ótti dep belgilenbegen expiry isleniwinen keyin kóteriledi."""


class Booking(BaseModel):
    """
    TICKBRON ushın tiykarǵı Booking modeli.

    Transaction qáwipsiz inventory qulıplaw menen bronnı kórsetedi.
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('confirmed', _('Confirmed')),
        ('cancelled', _('Cancelled')),
        ('completed', _('Completed')),
        ('no_show', _('No Show')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('failed', _('Failed')),
        ('refunded', _('Refunded')),
        ('partially_refunded', _('Partially Refunded')),
    ]

    # Paydalanıwshı maǵlıwmatı
    guest = models.ForeignKey(
        'users.User',
        on_delete=models.PROTECT,
        related_name='bookings',
        db_index=True
    )

    # Mehmanxana maǵlıwmatı
    property = models.ForeignKey(
        'properties.Property',
        on_delete=models.PROTECT,
        related_name='bookings',
        db_index=True
    )

    # Bron statusı
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Mehmanxanada naqd: mehmann kiriw kúni qaysı waqıtta keletuǵının aytqanda hám mehmanxana
    # onı kelgen dep belgilegende. arrived_at joq tastıyıqlanǵan bron berilgen waqıttan ARRIVAL_GRACE_HOURS
    # saat keyin biykar etiledi (bookings/arrival.py). Eski bronlarda keliw waqtı joq hám hesh qashan biykar etilmeydi.
    expected_arrival_time = models.TimeField(null=True, blank=True)
    arrived_at = models.DateTimeField(null=True, blank=True)

    # Sana maǵlıwmatı
    check_in = models.DateField(db_index=True)
    check_out = models.DateField(db_index=True)
    number_of_nights = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Number of nights for the booking')
    )

    # Mehmann maǵlıwmatı
    guest_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_('Number of guests')
    )

    # Mehmannıń baylanıs maǵlıwmatı (belgili bir bron ushın paydalanıwshı profilinen ayrıla aladı)
    guest_full_name = models.CharField(max_length=300, blank=True, null=True)
    guest_phone = models.CharField(max_length=20, blank=True, null=True)
    guest_email = models.EmailField(blank=True, null=True)

    # Xona hám balalar maǵlıwmatı
    number_of_rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text=_('Number of rooms booked')
    )
    children = models.JSONField(default=list, blank=True, help_text=_('List of children with ages'))

    # Baha maǵlıwmatı
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Total price for the booking')
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 valyuta kodı

    # Mehmannan ne alınatuǵını (R6): bron jaratılǵanda bir márte belgilenedi, inventory ti qulıplaytuǵın
    # transaction ishinde, hám hesh qashan ózgertilmeydi (qarań: save()). Joqarıdaǵı total_price
    # hám currency mehmanxananıń óz valyutasındaǵı baha.
    charge_currency = models.CharField(max_length=3)
    charge_amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, help_text=_('UZS per one unit of currency'))
    exchange_rate_date = models.DateField(null=True, blank=True)
    exchange_rate_source = models.CharField(max_length=16)  # 'cbu.uz', 'identity' yamasa 'legacy'
    exchange_rate_stale = models.BooleanField(default=False)

    # Mehmanxana mehmandı no-show dep xabarlasa hám staff tastıyıqlasa, mehmanǵa ne wáde etilgeni (R12
    # 3-basqısh): bron jaratılǵan waqıttaǵı NO_SHOW_REFUND_PERCENT, inventory qulıplaytuǵın
    # transaction da jazıladı hám hesh qashan ózgertilmeydi (qarań: save()). 0 = hesh nárse wáde etilmegen: bul
    # payda bolmastan burın jasalǵan bronlar hám create_booking sırtında jazılǵan qatarlar.
    no_show_refund_percent = models.PositiveSmallIntegerField(
        default=0, validators=[MaxValueValidator(100)],
        help_text=_('Percent of the amount paid refunded if the guest does not arrive (snapshot)'))

    # Mehmann tólengen bronnan bas tartsa, oǵan ne wáde etilgeni (R11, .ai/PLAN_R11_CANCELLATION.md): bron
    # jaratılǵan waqıttaǵı rate plan shártleri, hesh qashan ózgertilmeydi (qarań: SNAPSHOT_FIELDS).
    # cancel_refund_percent_after NULL = wáde joq: bul payda bolmastan burın jasalǵan bronlar avtomat qaytarıw almaydı.
    cancel_free_until = models.DateTimeField(
        null=True, blank=True,
        help_text=_('Cancelling up to this moment refunds everything paid (snapshot); empty = no free window'))
    cancel_refund_percent_after = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100)],
        help_text=_('Percent of the amount paid refunded when cancelling after the free window (snapshot)'))

    # Qosımsha maǵlıwmat
    special_requests = models.TextField(blank=True, null=True)
    confirmation_code = models.CharField(
        max_length=6,
        unique=True,
        db_index=True,
        help_text=_('Unique 6-character booking reference code')
    )

    # Biykar etiw maǵlıwmatı
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    # Múddet maǵlıwmatı
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True, help_text=_('Timestamp when pending booking expires'))

    class Meta:
        db_table = 'bookings'
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['payment_status', 'created_at']),
            models.Index(fields=['check_in', 'check_out']),
            models.Index(fields=['confirmation_code']),
            models.Index(fields=['guest', 'status']),
            models.Index(fields=['property', 'status']),
            models.Index(fields=['expires_at']),
            # Status bólimleri: dáwirdegi (kiriw sanası) counted bronlar (status)
            models.Index(fields=['status', 'check_in'], name='booking_status_checkin_idx'),
            # Mehmanxananıń keliwleri hám kalendarı: bir mehmanxananıń bronları kiriw sanası boyınsha
            models.Index(fields=['property', 'check_in'], name='booking_prop_checkin_idx'),
        ]

    def __str__(self):
        return f"Booking {self.confirmation_code} - {self.property}"

    def clean(self):
        """Bron maǵlıwmatın tekseriw."""
        super().clean()

        if self.check_out <= self.check_in:
            raise ValidationError({
                'check_out': _('Check-out date must be after check-in date')
            })

        if self.number_of_nights != (self.check_out - self.check_in).days:
            raise ValidationError({
                'number_of_nights': _('Number of nights must match the date range')
            })

        # Status ózgerip atırǵan bolsa, ótiwdi tekseriw
        if self.pk:
            try:
                old_booking = Booking.objects.get(pk=self.pk)
                if old_booking.status != self.status:
                    from_state = BookingState(old_booking.status)
                    to_state = BookingState(self.status)
                    is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state)
                    if not is_valid:
                        raise ValidationError({
                            'status': error_message
                        })
            except Booking.DoesNotExist:
                pass  # Jańa bron, ótiwdi tekseriw kerek emes

    # Baha hám tólem snapshot ı: bron payda bolǵannan keyin hesh qashan ózgermeydi
    SNAPSHOT_FIELDS = (
        'total_price', 'currency', 'charge_currency', 'charge_amount', 'exchange_rate',
        'exchange_rate_date', 'exchange_rate_source', 'exchange_rate_stale', 'no_show_refund_percent',
        'cancel_free_until', 'cancel_refund_percent_after',
    )

    @classmethod
    def from_db(cls, db, field_names, values, **kwargs):
        # Django 6.1 `fetch_mode` qosadı; bekitilgen 5.2 hesh nárse bermeydi, sol sebepli keyword lar ózgerissiz ótedi
        instance = super().from_db(db, field_names, values, **kwargs)
        instance._loaded_snapshot = {
            name: getattr(instance, name) for name in cls.SNAPSHOT_FIELDS if name in instance.__dict__
        }
        return instance

    def _check_snapshot_unchanged(self):
        loaded = getattr(self, '_loaded_snapshot', None)
        if self._state.adding or loaded is None:
            return
        changed = [name for name, value in loaded.items() if getattr(self, name) != value]
        if changed:
            raise PermissionError(f'Booking price and charge snapshot cannot be changed: {", ".join(changed)}')

    def _fill_snapshot_if_missing(self):
        """
        create_booking sırtında jaratılǵan qatarlar (seed ler, eski kod jolları) olarǵa haqıyqatında
        ne bolıp atırǵanın jazadı: UZS qatarı sol qalpında alınadı, basqa hár valyuta legacy qatar bolıp,
        óz valyutasında 1 kurs penen alınadı. create_booking snapshot tı hárdayım belgileydi.
        """
        if self.charge_currency:
            return
        self.charge_currency = self.currency
        self.charge_amount = self.total_price
        self.exchange_rate = 1
        self.exchange_rate_source = 'identity' if self.currency == CHARGE_CURRENCY else 'legacy'

    def save(self, *args, **kwargs):
        """Snapshot ózgeriwin qabıllamaw, jańa qatarlardıń snapshot ın toltırıw, tastıyıqlaw kodın hám múddetti jaratıw."""
        self._check_snapshot_unchanged()
        if self._state.adding:
            self._fill_snapshot_if_missing()
        self._save_with_confirmation_code(*args, **kwargs)
        self._loaded_snapshot = {name: getattr(self, name) for name in self.SNAPSHOT_FIELDS}

    def _save_with_confirmation_code(self, *args, **kwargs):
        from django.db import IntegrityError

        # Belgilenbegen bolsa, túnler sanın esaplaw
        if not self.number_of_nights:
            self.number_of_nights = (self.check_out - self.check_in).days

        # Kútip turǵan bronlar ushın múddet waqtın belgilew (jaratılǵannan 15 minut keyin)
        if self.status == 'pending' and not self.expires_at:
            from datetime import timedelta
            self.expires_at = timezone.now() + timedelta(minutes=15)

        # Belgilenbegen bolsa, tastıyıqlaw kodın jaratıw
        if not self.confirmation_code:
            max_attempts = 10
            for attempt in range(max_attempts):
                self.confirmation_code = self.generate_confirmation_code()
                try:
                    super().save(*args, **kwargs)
                    return  # Tabıslı, erte shıǵıw
                except IntegrityError:
                    # Tastıyıqlaw kodı tuwrı keldi (collision), qayta urınıw
                    self.confirmation_code = None
                    continue
            # Usı jerge jetsek, barlıq urınıwlar sátsiz boldı
            raise IntegrityError("Could not generate unique confirmation code after multiple attempts")
        else:
            super().save(*args, **kwargs)

    def generate_confirmation_code(self):
        """
        Kriptografiyalıq qáwipsiz tosınarlıq sandı paydalanıp, unikal 6 belgili bron reference code jaratadı.

        Shatasıwdıń aldın alıw ushın aytılmaǵan belgiler toplamın paydalanadı, bunnan 0/O, 1/I/L shıǵarılǵan.
        Belgiler toplamı: 2-9, A-H, J-K, M-N, P, R-Z (0, 1, I, L, O shıǵarılǵan)

        Eskertiw: save() metodı tuwrı kelwdi (collision) database constraint arqalı biledi
        hám IntegrityError bolsa qayta urınadı.
        """
        import secrets

        # Aytılǵan belgiler toplamı (0/O, 1/I/L shıǵarılǵan)
        unambiguous_chars = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'

        # Bir tosınarlıq kod jaratıw: unikallıq save() metodı tárepinen támiyinlenedi
        return ''.join(secrets.choice(unambiguous_chars) for _ in range(6))

    @classmethod
    def create_booking(cls, guest, property_obj, room_type, rate_plan, check_in, check_out, guest_count, special_requests=None, guest_full_name=None, guest_phone=None, guest_email=None, number_of_rooms=1, children=None, expected_arrival_time=None, confirmed=False):
        """
        Transaction qáwipsiz inventory qulıplaw menen bron jaratıw.

        Bul metod qos bronlawdıń aldın alıw hám inventory dıń izbe-izligin támiyinlew ushın
        database transaction ların hám qatar dárejesindegi qulıplawdı paydalanadı.

        Argumentler:
            guest: User obyekti (bronlaytuǵın mehmann)
            property_obj: Property obyekti
            room_type: RoomType obyekti
            rate_plan: RatePlan obyekti
            check_in: Kiriw sanası (date obyekti)
            check_out: Shıǵıw sanası (date obyekti)
            guest_count: Mehmanlar sanı
            special_requests: Ixtıyarıy arnawlı sorawlar teksti
            guest_full_name: Ixtıyarıy mehmannıń tolıq atı (ádetde paydalanıwshınıń tolıq atı)
            guest_phone: Ixtıyarıy mehmannıń telefonı (ádetde paydalanıwshınıń telefonı)
            guest_email: Ixtıyarıy mehmannıń e-mail ı (ádetde paydalanıwshınıń e-mail ı)
            number_of_rooms: Xonalar sanı (ádetde 1)
            children: guest_count ishinde esaplanatuǵın balalar jasları dizimi (ádetde bos dizim)

        Qaytaradı:
            Tabıslı bolsa Booking obyekti

        Kóteredi:
            ValidationError: Bron jaratıp bolmasa (bos orın joq, tekseriw qátelikleri)
            Exception: Database qátesi bolsa
        """
        from decimal import Decimal
        from bookings.pricing import quote_stay

        # Kirisiwdi tekseriw
        if check_out <= check_in:
            raise ValidationError({'check_out': _('Check-out date must be after check-in date')})

        number_of_nights = (check_out - check_in).days

        # Balalar jasların (berilgen bolsa) tekseriw
        if children is None:
            children = []
        for age in children:
            if not isinstance(age, int) or age < 0 or age > 17:
                raise ValidationError({'children': _('Children ages must be integers between 0 and 17')})
        # Balalar guest_count tıń (adamlar) bir bólegi, hám bronlawshı úlken adam
        if len(children) >= guest_count:
            raise ValidationError({'children': _('Children are part of the guest count; at least one guest must be an adult')})

        if property_obj.status != 'active' or not property_obj.is_active or property_obj.is_deleted:
            raise ValidationError({'property_id': _('Property not found or not available')})

        if number_of_rooms < 1:
            raise ValidationError({'number_of_rooms': _('At least one room must be booked')})

        if check_in < business_today():
            raise ValidationError({'check_in': _('Check-in date cannot be in the past')})

        if guest_count > room_type.max_occupancy * number_of_rooms:
            raise ValidationError({'guest_count': _('Guest count exceeds the capacity of the booked rooms')})

        # Izbe-izlik ushın atomic transaction paydalanıw
        with transaction.atomic():
            # Hár túnniń inventory qatarın qulıplaydı hám turıwdıń bahasın esaplaydı; ashıq quote
            # endpoint i sol funkciyanı paydalanadı, sol sebepli mehmann kórsetilgen bahanı tóleydi
            quote = quote_stay(rate_plan, check_in, check_out, number_of_rooms, lock=True)
            room_inventory_records = quote.room_inventory
            nightly_total = quote.nightly_total  # pútkil turıw ushın bir xonanıń bahası
            currency = rate_plan.currency
            total_price = quantize(quote.total_price, currency)

            # Alınatuǵın summa snapshot ı (som). Bar bolsa, usı turıw ushın iyeniń óz som bahası
            # (R16): valyuta kursı kerek emes. Bolmasa kurs, inventory qulıplanǵannan keyin házir oqıladı,
            # tek database den; sırtqı valyuta ushın kurs ele joq bolsa -> hesh nárse rezervlenbeydi.
            charge_amount, charge_source = quote.total_in(CHARGE_CURRENCY)
            if charge_source == 'owner':
                rate_value, rate_date, rate_stale = (
                    (charge_amount / total_price).quantize(Decimal('0.000001')) if total_price else Decimal('1'),
                    None, False)
            else:
                rate = current_rate(currency)
                if rate is None:
                    raise ExchangeRateUnavailable()
                charge_amount, charge_source = to_uzs(total_price, rate.rate), rate.source
                rate_value, rate_date, rate_stale = rate.rate, rate.date, rate.stale

            # Bronnı jaratıw
            booking = cls.objects.create(
                guest=guest,
                property=property_obj,
                # Booking API confirmed=True beredi: mehmanxanada naqd, tólem oynası joq, xona birden
                # alınadı. Tikkeley shaqırıwshılar tólem kodı óshirilgenshe (3-basqısh) eski pending bronǵa iye boladı.
                status='confirmed' if confirmed else 'pending',
                payment_status='pending',
                expected_arrival_time=expected_arrival_time,
                check_in=check_in,
                check_out=check_out,
                number_of_nights=number_of_nights,
                guest_count=guest_count,
                total_price=total_price,
                currency=currency,
                charge_currency=CHARGE_CURRENCY,
                charge_amount=charge_amount,
                exchange_rate=rate_value,
                exchange_rate_date=rate_date,
                exchange_rate_source=charge_source,
                exchange_rate_stale=rate_stale,
                special_requests=special_requests,
                guest_full_name=guest_full_name or guest.get_full_name(),
                guest_phone=guest_phone or guest.phone_number,
                guest_email=guest_email or guest.email,
                number_of_rooms=number_of_rooms,
                children=children
            )

            # Bron elementin jaratıw
            BookingItem.objects.create(
                booking=booking,
                room_type=room_type,
                rate_plan=rate_plan,
                number_of_rooms=number_of_rooms,
                # Bir xonanıń ortasha túngi bahası (túngi bahalar parıqlı bolıwı múmkin)
                price_per_night=(nightly_total / number_of_nights).quantize(Decimal('0.01')),
                currency=rate_plan.currency
            )

            # Inventory di jańalaw - hár bronlanǵan xonanı atomic túrde rezervlew. RoomInventory
            # rate plan emes, xona túri boyınsha, sol sebepli usı bir xona túriniń ekinshi rate
            # plan ı sol bir fizikalıq xonanı ekinshi ret satıwınan usı saqlaydı (#31).
            for inventory in room_inventory_records:
                inventory.booked_rooms = F('booked_rooms') + number_of_rooms
                inventory.save(update_fields=['booked_rooms'])

            return booking

    def _lock_row(self):
        """
        Usı bronnıń qatarın qulıplaw hám onıń ózgeriwshi jaǵdayın sonnan qayta oqıw.

        transaction.atomic() ishinde shaqırılıwı kerek; keyin ótkerilgen state-machine
        tekseriwleri eskirgen jaddaǵı nusqanı emes, eń sońǵı saqlanǵan statustı kóredi.
        """
        locked = type(self).objects.select_for_update().get(pk=self.pk)
        for field in ('status', 'payment_status', 'cancelled_at', 'cancellation_reason', 'expires_at'):
            setattr(self, field, getattr(locked, field))

    def cancel_booking(self, cancellation_reason=None):
        """
        Bronnan bas tartıw hám inventory di qaytarıw.

        Bul metod biykar etiw ortasında sátsiz bolsa da inventory durıs qaytarılıwı
        ushın transaction larǵa tayanadı.

        Argumentler:
            cancellation_reason: Ixtıyarıy biykar etiw sebebi

        Kóteredi:
            ValidationError: Bronnan bas tartıp bolmasa
            Exception: Database qátesi bolsa
        """
        from datetime import timedelta

        with transaction.atomic():
            # Qatardı qulıplaw hám jaǵdayın qayta oqıw, sonda birdey waqıttaǵı ótiwler
            # (mısalı biykar etiw hám múddet ótiw hám tólem) izbe-iz isleydi
            self._lock_row()
            # State machine arqalı ótiwdi tekseriw
            from_state = BookingState(self.status)
            to_state = BookingState('cancelled')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state)
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })

            # Bron elementlerin alıw
            booking_items = self.booking_items.all()

            # Hár bron elementi ushın inventory di qaytarıw
            for item in booking_items:
                date_range = []
                current_date = self.check_in
                while current_date < self.check_out:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)

                # Inventory di qulıplaw hám jańalaw (RoomInventory: usı xona túriniń hár rate
                # plan ı ortaq paydalanadı, qarań create_booking)
                from properties.models import RoomInventory
                inventory_records = RoomInventory.objects.filter(
                    room_type=item.room_type,
                    date__in=date_range
                ).select_for_update()

                for inventory in inventory_records:
                    # booked_rooms di kemeytiw
                    inventory.booked_rooms = F('booked_rooms') - item.number_of_rooms
                    inventory.save(update_fields=['booked_rooms'])

            # Bron statusın jańalaw
            old_status = self.status
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = cancellation_reason
            self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])

            # Status ótiwin log qa jazıw
            self._log_state_transition(old_status, 'cancelled', cancellation_reason or 'user_cancelled')

    def expire_booking(self):
        """
        Kútip turǵan bronnıń múddetin ótkeriw hám inventory di qaytarıw.

        Bul metod kútip turǵan bronnıń múddeti ótkende (ádetde 15 minuttan keyin) shaqırıladı.
        Inventory durıs qaytarılıwı ushın transaction lardı paydalanadı.

        Kóteredi:
            ValidationError: Bronnıń múddetin ótkerip bolmasa
            Exception: Database qátesi bolsa
        """
        from datetime import timedelta

        with transaction.atomic():
            # Qatardı qulıplaw hám jaǵdayın qayta oqıw, sonda birdey waqıttaǵı ótiwler
            # (mısalı biykar etiw hám múddet ótiw hám tólem) izbe-iz isleydi
            self._lock_row()
            # State machine arqalı ótiwdi tekseriw
            from_state = BookingState(self.status)
            to_state = BookingState('cancelled')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='expiry')
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })

            # Bron elementlerin alıw
            booking_items = self.booking_items.all()

            # Hár bron elementi ushın inventory di qaytarıw
            for item in booking_items:
                date_range = []
                current_date = self.check_in
                while current_date < self.check_out:
                    date_range.append(current_date)
                    current_date += timedelta(days=1)

                # Inventory di qulıplaw hám jańalaw (RoomInventory: usı xona túriniń hár rate
                # plan ı ortaq paydalanadı, qarań create_booking)
                from properties.models import RoomInventory
                inventory_records = RoomInventory.objects.filter(
                    room_type=item.room_type,
                    date__in=date_range
                ).select_for_update()

                for inventory in inventory_records:
                    # booked_rooms di kemeytiw
                    inventory.booked_rooms = F('booked_rooms') - item.number_of_rooms
                    inventory.save(update_fields=['booked_rooms'])

            # Bron statusın jańalaw
            old_status = self.status
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            self.cancellation_reason = 'Booking expired - payment not completed within time limit'
            self.save(update_fields=['status', 'cancelled_at', 'cancellation_reason'])

            # Status ótiwin log qa jazıw
            self._log_state_transition(old_status, 'cancelled', 'expiry')

    @classmethod
    def process_expired_bookings(cls, raise_on_error=False):
        """
        Múddeti ótken barlıq kútip turǵan bronlardı islew hám inventory di qaytarıw.

        Bul metod waqtı-waqtı menen shaqırılıwı kerek (mısalı management command yamasa Celery task arqalı),
        múddeti ótken bronlardı tazalaw hám inventory di qaytarıw ushın.

        Múddeti ótip bolmaǵan bron log qa jazıladı hám ótkizip jiberiledi, sonda qalǵanları
        islenedi. raise_on_error=True bolsa, qanday da bir bron sátsiz bolsa, isleniwden keyin
        ExpiredBookingProcessingError kóteriledi.

        Qaytaradı:
            int: Islengen bronlar sanı
        """
        expired_bookings = cls.objects.filter(
            status='pending',
            expires_at__lt=timezone.now(),
            is_deleted=False
        )

        processed_count = 0
        failed_ids = []
        for booking in expired_bookings:
            try:
                booking.expire_booking()
                processed_count += 1
            except ValidationError:
                # Usı isleniw dizimdi jasaǵannan keyin basqa soraw tárepinen tólengen yamasa biykar etilgen:
                # ótkeriw ushın hesh nárse qalmadı, sol sebepli qátelik emes
                if booking.status != 'pending':
                    continue
                logger.exception(f"Failed to expire booking {booking.pk}")
                failed_ids.append(booking.pk)
            except Exception:
                # Dawam etiw, sonda bir jaman bron basqalardı tosıp qoymaydı
                logger.exception(f"Failed to expire booking {booking.pk}")
                failed_ids.append(booking.pk)

        if failed_ids and raise_on_error:
            raise ExpiredBookingProcessingError(
                f"{len(failed_ids)} expired booking(s) could not be processed: {failed_ids}"
            )
        return processed_count

    def complete_booking(self):
        """
        Shıǵıwdan keyin bronnı juwmaqlaw.

        Bul metod mehmann shıqqanda bronnı confirmed statustan
        completed statusqa ótkiziw ushın shaqırıladı.

        Kóteredi:
            ValidationError: Bronnı juwmaqlap bolmasa
            Exception: Database qátesi bolsa
        """
        with transaction.atomic():
            # Qatardı qulıplaw hám jaǵdayın qayta oqıw, sonda birdey waqıttaǵı ótiwler
            # (mısalı biykar etiw hám múddet ótiw hám tólem) izbe-iz isleydi
            self._lock_row()
            # State machine arqalı ótiwdi tekseriw
            from_state = BookingState(self.status)
            to_state = BookingState('completed')
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason='checkout_completed')
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })

            # Bron statusın jańalaw
            old_status = self.status
            self.status = 'completed'
            self.save(update_fields=['status'])

            # Status ótiwin log qa jazıw
            self._log_state_transition(old_status, 'completed', 'checkout_completed')

    def mark_no_show(self, via_approved_report=False):
        """
        Mehmann kelmese, bronnı no-show dep belgilew.

        Bul metod tastıyıqlanǵan bron no-show bolǵanda shaqırıladı. via_approved_report=True
        bolsa (R12, staff mehmanxananıń no-show esabatın tastıyıqladı) juwmaqlanǵan bron da
        no-show bola aladı; basqa hesh nárse bunı ruxsat etpeydi.

        Kóteredi:
            ValidationError: Bronnı no-show dep belgilep bolmasa
            Exception: Database qátesi bolsa
        """
        with transaction.atomic():
            # Qatardı qulıplaw hám jaǵdayın qayta oqıw, sonda birdey waqıttaǵı ótiwler
            # (mısalı biykar etiw hám múddet ótiw hám tólem) izbe-iz isleydi
            self._lock_row()
            # State machine arqalı ótiwdi tekseriw
            from_state = BookingState(self.status)
            to_state = BookingState('no_show')
            reason = 'no_show_report_approved' if via_approved_report else 'guest_no_show'
            if via_approved_report and from_state == BookingState.CONFIRMED:
                reason = 'guest_no_show'
            is_valid, error_message = BookingStateMachine.validate_transition(from_state, to_state, reason=reason)
            if not is_valid:
                raise ValidationError({
                    'status': error_message
                })

            # Bron statusın jańalaw
            old_status = self.status
            self.status = 'no_show'
            self.save(update_fields=['status'])

            # Status ótiwin log qa jazıw
            self._log_state_transition(
                old_status, 'no_show', 'no_show_report_approved' if via_approved_report else 'guest_no_show')

    def restore_after_reversed_no_show(self, completed):
        """
        Staff tastıyıqlanǵan no-show esabatın túzetti: bron `completed` ke (turıw
        pitti) yamasa `confirmed` ke qaytadı. Tek no_show_report.reverse_report usını shaqıradı.

        Kóteredi:
            ValidationError: bron endi no-show emes bolsa
        """
        with transaction.atomic():
            self._lock_row()
            from_state = BookingState(self.status)
            to_state = BookingState('completed' if completed else 'confirmed')
            is_valid, error_message = BookingStateMachine.validate_transition(
                from_state, to_state, reason='no_show_report_reversed')
            if not is_valid:
                raise ValidationError({'status': error_message})
            old_status = self.status
            self.status = to_state.value
            self.save(update_fields=['status'])
            self._log_state_transition(old_status, to_state.value, 'no_show_report_reversed')

    def _log_state_transition(self, old_status, new_status, reason):
        """
        Audit maqsetinde bron status ótiwin log qa jazıw.

        Argumentler:
            old_status: Aldınǵı bron statusı
            new_status: Jańa bron statusı
            reason: Ótiw sebebi
        """
        try:
            from payments.models import PaymentAuditLog
            # Savepoint: bul jerdegi database qátesi shaqırıwshınıń transaction ın toqtatpawı kerek
            with transaction.atomic():
                PaymentAuditLog.log_action(
                    action='booking_status_changed',
                    booking=self,
                    old_status=old_status,
                    new_status=new_status,
                    details={'reason': reason}
                )
        except Exception:
            # Status ózgerisiniń ózi kúshte qaladı; joq tariyx qatarı ún-túnsiz qalmawı kerek
            logger.exception('Could not write the audit entry for booking %s (%s -> %s)', self.pk, old_status, new_status)


class BookingItem(BaseModel):
    """
    Bron ishindegi jeke xona bronları ushın bron element modeli.

    Bronlanǵan belgili xona túrleri hám rate plan lardı kórsetedi.
    """
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name='booking_items',
        db_index=True
    )
    room_type = models.ForeignKey(
        'properties.RoomType',
        on_delete=models.PROTECT,
        related_name='booking_items',
        db_index=True
    )
    rate_plan = models.ForeignKey(
        'properties.RatePlan',
        on_delete=models.PROTECT,
        related_name='booking_items',
        db_index=True
    )
    number_of_rooms = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text=_('Number of rooms of this type')
    )
    price_per_night = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Price per night for this room type')
    )
    currency = models.CharField(max_length=3, default='USD')  # ISO 4217 valyuta kodı

    class Meta:
        db_table = 'booking_items'
        verbose_name = 'Booking Item'
        verbose_name_plural = 'Booking Items'
        ordering = ['booking', 'room_type']
        indexes = [
            models.Index(fields=['booking', 'room_type']),
            models.Index(fields=['rate_plan']),
        ]

    def __str__(self):
        return f"{self.booking.confirmation_code} - {self.room_type.name}"


class AutoCompletionRun(models.Model):
    """
    Túngi avtomat juwmaqlawdıń bir haqıyqıy isleniwi (R12): qashan isledi, ne iske túsirdi,
    neshe tastıyıqlanǵan turıw completed boldı hám neshewi bolmadı. Dry run lar
    jazılmaydı. Super-admin lerge /admin-panel/auto-completion/status/ de kórsetiledi.
    """
    TRIGGER_CHOICES = [('beat', 'Celery beat'), ('command', 'Management command')]

    trigger = models.CharField(max_length=10, choices=TRIGGER_CHOICES)
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField()
    changed = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'booking_auto_completion_runs'
        ordering = ['-started_at', '-id']

    def __str__(self):
        return f'{self.started_at} {self.trigger}: {self.changed} completed, {self.failed} failed'


class NoShowReport(models.Model):
    """
    Mehmanxananıń mehmannıń kelmegeni haqqındaǵı esabatı (R12 3-basqısh). Mehmanxana xabarlaydı, staff sheshedi:
    iyeler óz kútip turǵan esabatın qaytarıp ala aladı, biraq hesh qashan tastıyıqlay yamasa biykar ete almaydı.

    - bir bronǵa bir `pending` esabat (bólekleyin unique constraint); esabat tek
      tastıyıqlanǵan yamasa juwmaqlanǵan bron ushın, kiriwden keyingi kúnnen shıǵıwdan keyingi NO_SHOW_REPORT_WINDOW_DAYS
      kúnge shekem ruxsat etiledi (bookings.noshow.create_report)
    - tastıyıqlaw bronnı no_show ǵa ótkizedi hám bron waqtında wáde etilgen qaytarıwdı tóleydi;
      biykar etiw hesh nárseni ózgertpeydi; staff eki qararın da túzete aladı (bookings.noshow.reverse_report)
    - qatarlar hesh qashan óshirilmeydi
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('withdrawn', 'Withdrawn'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name='no_show_reports')
    property = models.ForeignKey('properties.Property', on_delete=models.PROTECT, related_name='no_show_reports')
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='no_show_reports_created')
    comment = models.TextField(help_text=_('The hotel\'s statement, plain text, 10-500 characters'))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    decided_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='no_show_reports_decided')
    decision_comment = models.TextField(blank=True, default='')
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_no_show_reports'
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='noshow_status_created_idx'),
            models.Index(fields=['property', 'status', 'created_at'], name='noshow_prop_status_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['booking'], condition=models.Q(status='pending'),
                                    name='noshow_one_pending_per_booking'),
        ]

    def __str__(self):
        return f'NoShowReport {self.pk} booking {self.booking_id} {self.status}'

    def delete(self, *args, **kwargs):
        raise PermissionError('No-show reports cannot be deleted')
