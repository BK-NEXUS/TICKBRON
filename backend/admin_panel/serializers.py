"""
Serializers for admin API endpoints.

This module contains serializers for property moderation, user management,
amenity management, and payment monitoring.
"""
from rest_framework import serializers
from properties.models import Property, Amenity, AmenityCategory
from properties.serializers import PropertyTypeSerializer, AmenityCategorySerializer
from users.models import User
from users.serializers import UserSerializer
from admin_panel.models import InternalNote


class AdminPropertySerializer(serializers.ModelSerializer):
    """
    Serializer for property moderation by admins.
    
    Includes approval/suspension functionality.
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
            'city', 'state', 'postal_code', 'country', 'latitude', 'longitude',
            'base_price', 'currency', 'full_address', 'approved_at', 'approved_by',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'approved_at', 'approved_by', 'created_at', 'updated_at']
    
    def get_owner_email(self, obj):
        """Get owner email."""
        return obj.owner.email if obj.owner else None
    
    def get_owner_name(self, obj):
        """Get owner full name."""
        return obj.owner.get_full_name() if obj.owner else None
    
    def get_full_address(self, obj):
        """Get the full address as a string."""
        return obj.get_full_address()


class AdminPropertyApproveSerializer(serializers.Serializer):
    """
    Serializer for property approval action.
    """
    rejection_reason = serializers.CharField(required=False, allow_blank=True)


class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for user management by admins.
    
    Limited fields for admin user listing.
    """
    full_name = serializers.SerializerMethodField()
    role_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number',
            'is_staff', 'is_active', 'role_name', 'date_joined', 'last_login',
            'email_verified', 'two_factor_enabled'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Get user full name."""
        return obj.get_full_name()
    
    def get_role_name(self, obj):
        """Get role name."""
        return obj.role.name if obj.role else None


class AdminUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating hotel-owner accounts by super-admins.
    
    Super-admin only endpoint for direct hotel-owner account creation.
    """
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'first_name', 'last_name', 'phone_number',
            'password', 'password_confirm'
        ]
    
    def validate(self, data):
        """Validate password confirmation."""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Passwords do not match'
            })
        return data
    
    def create(self, validated_data):
        """Create user with hotel-owner role."""
        from permissions.models import Role
        
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm')
        
        # Get or create hotel-owner role
        hotel_owner_role, _ = Role.objects.get_or_create(
            name='hotel-owner',
            defaults={
                'description': 'Hotel owner role for property management',
                'is_system_role': True
            }
        )
        
        # Create user with hotel-owner role
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone_number=validated_data.get('phone_number', ''),
            role=hotel_owner_role
        )
        
        return user


class AdminAmenityCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for amenity category management by admins.
    """
    class Meta:
        model = AmenityCategory
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'sort_order'
        ]
        read_only_fields = ['id']


class AdminAmenitySerializer(serializers.ModelSerializer):
    """
    Serializer for amenity management by admins (write operations).
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
    Serializer for amenity read operations (includes nested category).
    """
    category = AmenityCategorySerializer(read_only=True)
    
    class Meta:
        model = Amenity
        fields = [
            'id', 'category', 'name', 'slug', 'description', 'icon',
            'is_searchable', 'sort_order'
        ]
        read_only_fields = ['id']


class AdminPaymentTransactionSerializer(serializers.Serializer):
    """
    Serializer for payment transaction monitoring by admins.
    
    Read-only view of payment transactions for admin oversight.
    """
    id = serializers.IntegerField()
    booking_id = serializers.IntegerField()
    provider = serializers.CharField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class AdminCustomerSerializer(serializers.Serializer):
    """
    Serializer for admin customers directory.
    
    Returns customer information with booking aggregates.
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
    total_amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    customer_status = serializers.CharField()


class AdminCustomerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed customer profile in admin panel.
    
    Returns full customer contact information.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone_number',
            'whatsapp', 'telegram', 'preferred_contact_method', 'date_joined',
            'last_login', 'is_active', 'email_verified', 'phone_verified'
        ]
        read_only_fields = ['id', 'email', 'date_joined', 'last_login']
    
    def get_full_name(self, obj):
        """Get user full name."""
        return obj.get_full_name()


class AdminBookingSummarySerializer(serializers.Serializer):
    """
    Serializer for booking summary in customer detail.
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


class AdminPaymentSummarySerializer(serializers.Serializer):
    """
    Serializer for payment summary in customer detail.
    """
    id = serializers.IntegerField()
    booking_id = serializers.IntegerField()
    provider = serializers.CharField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField()


class AdminInternalNoteSerializer(serializers.ModelSerializer):
    """
    Serializer for internal notes (staff-only).
    """
    author_name = serializers.SerializerMethodField()
    author_email = serializers.SerializerMethodField()
    
    class Meta:
        model = InternalNote
        fields = [
            'id', 'customer', 'author', 'author_name', 'author_email',
            'note', 'created_at', 'updated_at'
        ]
        # A note belongs to the customer in its URL; it cannot be moved by editing
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']
    
    def get_author_name(self, obj):
        """Get author full name."""
        return obj.author.get_full_name() if obj.author else None
    
    def get_author_email(self, obj):
        """Get author email."""
        return obj.author.email if obj.author else None


class AdminInternalNoteCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating internal notes.
    """
    class Meta:
        model = InternalNote
        fields = ['customer', 'note']
        # Taken from the URL by the view (serializer.save(customer=...)), not the body
        read_only_fields = ['customer']
    
    def create(self, validated_data):
        """Create internal note with current user as author."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
