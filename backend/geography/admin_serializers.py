"""Serializers for the super-admin geography API (Geography plan G3)."""
from django.db.models import Q
from rest_framework import serializers

from geography.models import City, Country, Region


class _NamesMixin:
    def validate(self, attrs):
        for field in ('name_uz', 'name_ru', 'name_en'):
            if field in attrs:
                attrs[field] = attrs[field].strip()
                if not attrs[field]:
                    raise serializers.ValidationError({field: 'This field may not be blank.'})
        return super().validate(attrs)


class _ParentImmutableMixin:
    """The parent decides what a property's location means: it is set on create only."""
    parent_field = None

    def validate(self, attrs):
        if self.instance is not None and self.parent_field in attrs \
                and attrs[self.parent_field] != getattr(self.instance, self.parent_field):
            raise serializers.ValidationError({self.parent_field: 'The parent cannot be changed.'})
        return super().validate(attrs)


class AdminCountrySerializer(_NamesMixin, serializers.ModelSerializer):
    region_count = serializers.IntegerField(read_only=True)
    hotel_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Country
        fields = ['id', 'code', 'currency', 'name_uz', 'name_ru', 'name_en', 'is_active', 'sort_order',
                  'region_count', 'hotel_count']
        read_only_fields = ['sort_order']
        extra_kwargs = {'code': {'validators': []}}  # uniqueness is checked in validate_code

    def validate_code(self, value):
        value = value.strip().upper()
        if len(value) != 2 or not value.isascii() or not value.isalpha():
            raise serializers.ValidationError('Use the two-letter ISO 3166-1 code, e.g. UZ.')
        if Country.objects.filter(code=value).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError('A country with this code already exists.')
        return value

    def validate_currency(self, value):
        value = value.strip().upper()
        if len(value) != 3 or not value.isascii() or not value.isalpha():
            raise serializers.ValidationError('Use the three-letter ISO 4217 code, e.g. UZS.')
        return value


class AdminRegionSerializer(_ParentImmutableMixin, _NamesMixin, serializers.ModelSerializer):
    parent_field = 'country'
    city_count = serializers.IntegerField(read_only=True)
    hotel_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Region
        fields = ['id', 'country', 'slug', 'name_uz', 'name_ru', 'name_en', 'is_active', 'sort_order',
                  'city_count', 'hotel_count']
        read_only_fields = ['slug', 'sort_order']
        validators = []  # the name is checked below, so a clash is a plain 400 with a clear message

    def validate(self, attrs):
        attrs = super().validate(attrs)
        country = attrs.get('country') or getattr(self.instance, 'country', None)
        name = attrs.get('name_en') or getattr(self.instance, 'name_en', None)
        duplicates = Region.objects.filter(country=country, name_en__iexact=name)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError({'name_en': 'This country already has a region with this name.'})
        return attrs


class AdminCitySerializer(_ParentImmutableMixin, _NamesMixin, serializers.ModelSerializer):
    parent_field = 'region'
    hotel_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = City
        fields = ['id', 'region', 'slug', 'name_uz', 'name_ru', 'name_en', 'is_active', 'sort_order',
                  'hotel_count']
        read_only_fields = ['slug', 'sort_order']
        validators = []

    def validate(self, attrs):
        attrs = super().validate(attrs)
        region = attrs.get('region') or getattr(self.instance, 'region', None)
        name = attrs.get('name_en') or getattr(self.instance, 'name_en', None)
        duplicates = City.objects.filter(region=region, name_en__iexact=name)
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError({'name_en': 'This region already has a city with this name.'})
        return attrs


def search_filter(queryset, term, extra=()):
    """Match the term against all three names (and any extra field), case-insensitive."""
    term = (term or '').strip()
    if not term:
        return queryset
    query = Q()
    for field in ('name_uz', 'name_ru', 'name_en', *extra):
        query |= Q(**{f'{field}__icontains': term})
    return queryset.filter(query)
