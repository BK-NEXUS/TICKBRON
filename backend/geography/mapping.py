"""
Map the old free-text location of properties (country / state / city) to the
Geography dictionary (country_ref / region_ref / city_ref).

Matching is trimmed, case-insensitive and apostrophe-insensitive, against the uz, ru
and en names plus the aliases in geography/data.py. A value that does not match
exactly one row stays NULL and is listed in the report. Properties that already have
a ref keep it.
"""
import re
from collections import Counter

from geography.data import CITY_ALIASES, COUNTRY_ALIASES, REGION_ALIASES

_APOSTROPHES = re.compile(r"[ʻʼ‘’`'´]")
_SPACES = re.compile(r'\s+')
# Words that only say what kind of region it is ("Samarkand Region" -> "samarkand")
_REGION_WORDS = re.compile(
    r'\b(region|province|city|oblast|viloyati|shahri|respublikasi|область|город|ил)\b|\(ил\)')


def normalize(value):
    """'  O‘zbekiston ' -> 'ozbekiston'"""
    if not value:
        return ''
    value = _APOSTROPHES.sub('', value.strip().lower())
    return _SPACES.sub(' ', value).strip()


def _region_keys(region):
    names = [region.name_uz, region.name_ru, region.name_en, *REGION_ALIASES.get(region.slug, [])]
    keys = {normalize(name) for name in names if name}
    keys |= {_SPACES.sub(' ', _REGION_WORDS.sub(' ', key)).strip() for key in list(keys)}
    return {key for key in keys if key}


def _names(row, aliases):
    return {normalize(n) for n in (row.name_uz, row.name_ru, row.name_en, *aliases) if n}


class GeographyIndex:
    """All dictionary rows, indexed by normalized name."""

    def __init__(self, country_model, region_model, city_model):
        self.countries = {}
        for country in country_model.objects.all():
            for key in _names(country, [country.code, *COUNTRY_ALIASES.get(country.code, [])]):
                self.countries.setdefault(key, set()).add(country)
        self.regions = {}
        for region in region_model.objects.select_related('country'):
            for key in _region_keys(region):
                self.regions.setdefault(key, set()).add(region)
        self.cities = {}
        centres = set()
        for city in city_model.objects.select_related('region__country').order_by('region_id', 'sort_order', 'id'):
            keys = _names(city, CITY_ALIASES.get(city.slug, []))
            for key in keys:
                self.cities.setdefault(key, set()).add(city)
            # A region is also known by its centre (its first city): "Samarkand" -> Samarkand Region
            if city.region_id not in centres:
                centres.add(city.region_id)
                for key in keys:
                    self.regions.setdefault(key, set()).add(city.region)

    @staticmethod
    def _one(candidates):
        return next(iter(candidates)) if len(candidates) == 1 else None

    def match(self, country_text, state_text, city_text):
        """(country, region, city) for one text triple; None where there is no single match."""
        country = self._one(self.countries.get(normalize(country_text), set()))
        if country is None:
            return None, None, None
        regions = {r for r in self.regions.get(normalize(state_text), set()) if r.country_id == country.id}
        region = self._one(regions)
        cities = {c for c in self.cities.get(normalize(city_text), set()) if c.region.country_id == country.id}
        if region is not None and len(cities) > 1:
            cities = {c for c in cities if c.region_id == region.id}
        city = self._one(cities)
        if city is not None:
            # The city is the most specific: its region wins
            region = city.region
        return country, region, city


def map_properties(property_model, country_model, region_model, city_model, dry_run=False, queryset=None):
    """
    Fill country_ref / region_ref / city_ref from the text fields where they are empty.

    Takes the model classes so a data migration can pass its historical models.
    `queryset` limits the run to some properties (e.g. the ones a seed command made).
    Returns a report dict; with dry_run=True nothing is written.
    """
    index = GeographyIndex(country_model, region_model, city_model)
    scope = property_model.objects.all() if queryset is None else queryset
    todo = scope.filter(country_ref__isnull=True)
    report = {
        'properties': scope.count(),
        'already_mapped': scope.filter(country_ref__isnull=False).count(),
        'country': 0, 'region': 0, 'city': 0,
        'unmatched_country': Counter(), 'unmatched_region': Counter(), 'unmatched_city': Counter(),
    }
    # order_by(): the model's default ordering would make distinct() see created_at too
    combos = todo.order_by().values_list('country', 'state', 'city').distinct()
    for country_text, state_text, city_text in combos:
        rows = todo.filter(country=country_text, state=state_text, city=city_text)
        count = rows.count()
        country, region, city = index.match(country_text, state_text, city_text)
        if country is None:
            report['unmatched_country'][country_text or '(empty)'] += count
            continue
        report['country'] += count
        if region is not None:
            report['region'] += count
        else:
            report['unmatched_region'][f'{country.name_en} / {state_text or "(empty)"}'] += count
        if city is not None:
            report['city'] += count
        else:
            report['unmatched_city'][f'{country.name_en} / {city_text or "(empty)"}'] += count
        if not dry_run:
            rows.update(country_ref=country, region_ref=region, city_ref=city)
    return report


def format_report(report, dry_run=False):
    lines = [
        f"Geography mapping{' (dry run, nothing written)' if dry_run else ''}: "
        f"{report['properties']} properties, {report['already_mapped']} already mapped.",
        f"  matched: country {report['country']}, region {report['region']}, city {report['city']}",
    ]
    for level in ('country', 'region', 'city'):
        unmatched = report[f'unmatched_{level}']
        if unmatched:
            lines.append(f'  left NULL ({level}):')
            lines += [f'    {count:>4}  {value}' for value, count in unmatched.most_common()]
    return '\n'.join(lines)
