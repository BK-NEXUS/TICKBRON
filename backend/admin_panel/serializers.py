"""
Admin API endpoint leri ushın serializer ler.

Bul modul mehmanxana moderation ı, paydalanıwshılardı basqarıw,
amenity di basqarıw hám tólemdi baqlaw serializer lerin óz ishine aladı.
"""
from django.db import transaction
from common.validators import validate_person_name
from rest_framework import serializers
from partner.models import OwnerPlace
from geography.models import Country, Region
from geography.serializers import REF_FIELDS, check_geography
from properties.models import Property, Amenity, AmenityCategory
from properties.serializers import PropertyTypeSerializer, AmenityCategorySerializer
from users.models import User
from users.serializers import LowercaseEmailField, unique_email_field, validate_new_password, validate_phone_number_format
from users.validators import EmailFormatValidator
from admin_panel.models import InternalNote
from django.utils.translation import gettext as _


class AdminPropertySerializer(serializers.ModelSerializer):
    """
    Admin ler tárepinen mehmanxana moderation ı ushın serializer.

    Tastıyıqlaw/toqtatıw funkciyasın óz ishine aladı.
    """
    property_type = PropertyTypeSerializer(read_only=True)
    owner_email = serializers.SerializerMethodField()
    owner_name = serializers.SerializerMethodField()
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            'id', 'owner', 'owner_email', 'owner_name', 'property_type', 'status',
            'max_guests', 'bedrooms', 'bathrooms', 'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country', 'country_ref', 'region_ref',
            'latitude', 'longitude',
            'base_price', 'currency', 'full_address', 'approved_at', 'approved_by',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'approved_at', 'approved_by', 'created_at', 'updated_at']

    def get_owner_email(self, obj) -> str | None:
        """Iyeniń e-mail ın alıw."""
        return obj.owner.email if obj.owner else None

    def get_owner_name(self, obj) -> str | None:
        """Iyeniń tolıq atın alıw."""
        return obj.owner.get_full_name() if obj.owner else None

    def get_full_address(self, obj) -> str:
        """Tolıq mánzildi qatar retinde alıw."""
        return obj.get_full_address()


class AdminPropertyApproveSerializer(serializers.Serializer):
    """
    Mehmanxananı tastıyıqlaw háreketi ushın serializer.
    """
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class AdminPropertyRegionSerializer(serializers.Serializer):
    """
    Mehmanxananıń jaylasıwı. Geografiya ref lerin (country_ref, region_ref; ekewi
    null bolsa tazalanadı) yamasa eski klientler ushın `state` jiberiń: region teksti (bos bolsa tazalanadı, sonda
    mehmanxana Status bóliminde "Unspecified" retinde toparlanadı). Ekewi jiberilse, ref ler ústin boladı.
    Serializer context inde mehmanxana kerek.
    """
    state = serializers.CharField(
        max_length=100, allow_blank=True, allow_null=True, trim_whitespace=True, required=False)
    country_ref = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), allow_null=True, required=False)
    region_ref = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), allow_null=True, required=False)

    def validate_state(self, value):
        return value or None

    def validate(self, attrs):
        sent_refs = any(field in attrs for field in REF_FIELDS)
        if not sent_refs and 'state' not in attrs:
            raise serializers.ValidationError({'state': _('This field is required.')})
        if sent_refs:
            errors = check_geography(attrs, current=self.context.get('property'), nullable=True)
            if errors:
                raise serializers.ValidationError(errors)
        return attrs


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Admin ler paydalanıwshılardı basqarıw ushın serializer.

    Admin paydalanıwshı dizimi ushın shekli maydanlar.
    """
    full_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    # role_name penen birdey mánis, admin UI oqıytuǵın atama astında
    role = serializers.SerializerMethodField(method_name='get_role_name')

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number',
            'is_staff', 'is_superuser', 'is_active', 'role', 'role_name', 'date_joined', 'last_login',
            'email_verified', 'two_factor_enabled'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']

    def get_full_name(self, obj) -> str:
        """Paydalanıwshınıń tolıq atın alıw."""
        return obj.get_full_name()

    def get_role_name(self, obj) -> str | None:
        """Rol atın alıw."""
        return obj.role.name if obj.role else None


class AccountCreateSerializer(serializers.ModelSerializer):
    """Super-admin qolda jaratatuǵın hár akkaunt ushın kerek maydanlar: kim, qalay baylanısıw, birinshi parol."""
    email = unique_email_field()
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(max_length=30)  # tek saqlanadı: SMS joq, kod joq

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone_number', 'password', 'password_confirm']
        extra_kwargs = {
            'first_name': {'validators': [validate_person_name]},
            'last_name': {'validators': [validate_person_name]},
        }

    def validate_phone_number(self, value):
        return validate_phone_number_format(value)

    def validate(self, data):
        """Parol tastıyıqlawın tekseriw."""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': _('Passwords do not match')
            })
        validate_new_password(data)
        return data


class AdminStaffCreateSerializer(AccountCreateSerializer):
    """
    Super-admin qosatuǵın administrator: staff (panelden paydalana aladı) yamasa `role` solay desse, basqa
    super-admin. Huquqlar tek `role` ten keledi; sorawdıń basqa hesh bir maydanı olardı ózgerte almaydı.
    Eki at ta májbúriy: panel tólemdi kim tastıyıqlaǵanın atı menen kórsetedi.
    """
    ROLES = ('staff', 'super_admin')
    role = serializers.ChoiceField(choices=ROLES, default='staff', write_only=True)

    class Meta(AccountCreateSerializer.Meta):
        fields = AccountCreateSerializer.Meta.fields + ['role']
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False, 'validators': [validate_person_name]},
            'last_name': {'required': True, 'allow_blank': False, 'validators': [validate_person_name]},
        }

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        return User.objects.create_user(
            email=validated_data['email'], password=validated_data['password'],
            first_name=validated_data['first_name'], last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'], is_staff=True,
            is_superuser=validated_data['role'] == 'super_admin',
        )


class AdminContactSerializer(serializers.Serializer):
    """Administrator jazǵan akkauttıń jańa telefon nomeri hám/yamasa e-mail ı. Eń keminde ekewiniń biri."""
    email = LowercaseEmailField(required=False)
    phone_number = serializers.CharField(required=False, max_length=30)

    def __init__(self, *args, account, **kwargs):
        super().__init__(*args, **kwargs)
        self.account = account

    def validate_email(self, value):
        EmailFormatValidator().validate(value)
        if User.objects.filter(email__iexact=value).exclude(pk=self.account.pk).exists():
            raise serializers.ValidationError(_('User with this email already exists.'))
        return value

    def validate_phone_number(self, value):
        return validate_phone_number_format(value)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(_('Send a new phone number or a new e-mail.'))
        return attrs


class AdminUserCreateSerializer(AccountCreateSerializer):
    """
    Super-admin ler tárepinen mehmanxana iyesi akkaunt ların jaratıw ushın serializer.

    Mehmanxana iyesi akkauntın tikkeley jaratıw ushın tek super-admin endpoint i.
    """
    # Iyeniń mehmanxanaları qayerde kórinedi: ekewi de májbúriy hám bir-birine sáykes bolıwı kerek
    country_ref = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), write_only=True)
    region_ref = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all(), write_only=True)

    # Sayt usı iyeniń hár bronınan ne aladı: super-admin jaratılǵanda sonı belgilewi kerek
    commission_percent = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=0, max_value=100, write_only=True)

    class Meta(AccountCreateSerializer.Meta):
        fields = AccountCreateSerializer.Meta.fields + ['country_ref', 'region_ref', 'commission_percent']

    def validate(self, data):
        data = super().validate(data)
        errors = check_geography(data)
        if errors:
            raise serializers.ValidationError(errors)
        return data

    @transaction.atomic
    def create(self, validated_data):
        """Mehmanxana iyesi rolindegi paydalanıwshını hám akkauttıń ornın jaratıw."""
        from permissions.models import Role

        validated_data.pop('password_confirm')
        place = {
            'country': validated_data.pop('country_ref'),
            'region': validated_data.pop('region_ref'),
        }

        # Mehmanxana iyesi rolin alıw yamasa jaratıw
        hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={
                'description': 'Hotel owner role for property management',
                'is_system_role': True
            }
        )

        # Mehmanxana iyesi rolindegi paydalanıwshı jaratıw
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data['phone_number'],
            role=hotel_owner_role
        )
        OwnerPlace.objects.create(owner=user, **place)

        return user


class AdminAmenityCategorySerializer(serializers.ModelSerializer):
    """
    Admin ler amenity kategoriyasın basqarıw ushın serializer.
    """
    class Meta:
        model = AmenityCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'sort_order'
        ]
        read_only_fields = ['id']


class AdminAmenitySerializer(serializers.ModelSerializer):
    """
    Admin ler amenity di basqarıw ushın serializer (jazıw ámelleri).
    """
    category = serializers.PrimaryKeyRelatedField(queryset=AmenityCategory.objects.all())

    class Meta:
        model = Amenity
        fields = [
            'id', 'category', 'name', 'slug', 'description', 'icon',
            'is_searchable', 'sort_order'
        ]
        read_only_fields = ['id']


class AdminAmenityReadSerializer(serializers.ModelSerializer):
    """
    Amenity oqıw ámelleri ushın serializer (ishki kategoriyanı óz ishine aladı).
    """
    category = AmenityCategorySerializer(read_only=True)

    class Meta:
        model = Amenity
        fields = [
            'id', 'category', 'name', 'slug', 'description', 'icon',
            'is_searchable', 'sort_order'
        ]
        read_only_fields = ['id']


class AdminCustomerSerializer(serializers.Serializer):
    """
    Admin mijozlar dizimi ushın serializer.

    Bron jıynaqları menen mijoz maǵlıwmatın qaytaradı.
    """
    id = serializers.IntegerField()
    registration_date = serializers.DateTimeField()
    full_name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    email = serializers.EmailField()
    whatsapp = serializers.CharField(allow_null=True)
    telegram = serializers.CharField(allow_null=True)
    preferred_contact_method = serializers.CharField(allow_null=True)
    total_booking_count = serializers.IntegerField()
    last_booking_date = serializers.DateTimeField(allow_null=True)
    customer_status = serializers.CharField()


class AdminCustomerDetailSerializer(serializers.ModelSerializer):
    """
    Admin panelindegi mijozdıń tolıq profili ushın serializer.

    Mijozdıń tolıq baylanıs maǵlıwmatın qaytaradı.
    """
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number',
            'whatsapp', 'telegram', 'preferred_contact_method', 'date_joined',
            'last_login', 'is_active', 'email_verified'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']

    def get_full_name(self, obj) -> str:
        """Paydalanıwshınıń tolıq atın alıw."""
        return obj.get_full_name()


class AdminBookingSummarySerializer(serializers.Serializer):
    """
    Mijoz tolıq maǵlıwmatındaǵı bron qısqasha mazmunı ushın serializer.
    """
    id = serializers.IntegerField()
    reference_code = serializers.CharField()
    status = serializers.CharField()
    payment_status = serializers.CharField()
    check_in = serializers.DateField()
    check_out = serializers.DateField()
    number_of_nights = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    property_name = serializers.CharField()
    property_city = serializers.CharField()
    created_at = serializers.DateTimeField()


class AdminInternalNoteSerializer(serializers.ModelSerializer):
    """
    Ishki jazbalar ushın serializer (tek staff).
    """
    author_name = serializers.SerializerMethodField()
    author_email = serializers.SerializerMethodField()

    class Meta:
        model = InternalNote
        fields = [
            'id', 'customer', 'author', 'author_name', 'author_email',
            'note', 'created_at', 'updated_at'
        ]
        # Jazba óz URL indegi mijozǵa tiyisli hám dáslepki avtorın saqlaydı;
        # ózgertiw menen ekewin de ózgertip bolmaydı
        read_only_fields = ['id', 'customer', 'author', 'created_at', 'updated_at']

    def get_author_name(self, obj):
        """Avtordıń tolıq atın alıw."""
        return obj.author.get_full_name() if obj.author else None

    def get_author_email(self, obj):
        """Avtordıń e-mail ın alıw."""
        return obj.author.email if obj.author else None


class AdminInternalNoteCreateSerializer(serializers.ModelSerializer):
    """
    Ishki jazbalar jaratıw ushın serializer.
    """
    class Meta:
        model = InternalNote
        fields = ['customer', 'note']
        # View tárepinen URL den alınadı (serializer.save(customer=...)), body den emes
        read_only_fields = ['customer']

    def create(self, validated_data):
        """Házirgi paydalanıwshını avtor etip ishki jazba jaratadı."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
