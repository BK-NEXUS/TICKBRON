"""
Mehmanxanalardıń eski erkin tekst jaylasıwın (country / state) Geography
sózligine (country_ref / region_ref) sáykeslew.

Qala sózligi endi joq. `city_model` tek eski properties/0013 data migration ı ushın qabıllanadı,
ol qala kestesi ele bar waqıtta isleydi.

Sáykeslew bos orınlarsız, register ti hám apostrofti esapqa almay, uz, ru
hám en atlarına hám geography/data.py degi alias larǵa qarsı isleydi. Anıq bir qatarǵa
sáykes kelmeytuǵın mánis NULL qaladı hám esabatta dizimlenedi. Aldınan
ref i bar mehmanxanalar onı saqlaydı.
"""
import re
from collections import Counter

from geography.data import CITY_ALIASES, COUNTRY_ALIASES, REGION_ALIASES

_APOSTROPHES = re.compile(r"[ʻʼ‘’`'´]")
_SPACES = re.compile(r'\s+')
# Tek regionnıń qanday túri ekenin aytatuǵın sózler ("Samarkand Region" -> "samarkand"); zapas jol retinde paydalanıladı
_REGION_WORDS = re.compile(
    r'\b(region|province|city|oblast|viloyati|shahri|respublikasi|область|город|ил)\b|\(ил\)')


def normalize(value):
    """'  O‘zbekiston ' -> 'ozbekiston'"""
    if not value:
        return ''
    value = _APOSTROPHES.sub('', value.strip().lower())
    return _SPACES.sub(' ', value).strip()


def _strip_region_words(key):
    return _SPACES.sub(' ', _REGION_WORDS.sub(' ', key)).strip()


def _region_keys(region):
    """(exact, loose): tolıq atlar hám alias lar, hám "Region" / "City" sózlerisiz sol sıyaqlılar."""
    names = [region.name_uz, region.name_ru, region.name_en, *REGION_ALIASES.get(region.slug, [])]
    exact = {normalize(name) for name in names if name}
    loose = {_strip_region_words(key) for key in exact}
    return {key for key in exact if key}, {key for key in loose if key}


def _names(row, aliases):
    return {normalize(n) for n in (row.name_uz, row.name_ru, row.name_en, *aliases) if n}


class GeographyIndex:
    """Barlıq sózlik qatarları, normallastırılǵan at boyınsha indekslengen."""

    def __init__(self, country_model, region_model, city_model=None):
        self.countries = {}
        for country in country_model.objects.all():
            for key in _names(country, [country.code, *COUNTRY_ALIASES.get(country.code, [])]):
                self.countries.setdefault(key, set()).add(country)
        # Aldın anıq atlar: "Tashkent" (qala) hám "Tashkent Region" "Region" alıp taslanǵanda ǵana
        # uqsas bolıp qalatuǵın eki region, sol sebepli alıp taslanǵan kilt ler zapas jol.
        self.regions = {}
        self.loose_regions = {}
        for region in region_model.objects.select_related('country'):
            exact, loose = _region_keys(region)
            for key in exact:
                self.regions.setdefault(key, set()).add(region)
            for key in loose:
                self.loose_regions.setdefault(key, set()).add(region)
        self.cities = {}
        centres = set()
        cities = () if city_model is None else city_model.objects.select_related('region__country').order_by(
            'region_id', 'sort_order', 'id')
        for city in cities:
            keys = _names(city, CITY_ALIASES.get(city.slug, []))
            for key in keys:
                self.cities.setdefault(key, set()).add(city)
            # Region óziniń orayı (birinshi qalası) menen de belgili: "Termez" -> Surkhandarya
            if city.region_id not in centres:
                centres.add(city.region_id)
                for key in keys:
                    self.loose_regions.setdefault(key, set()).add(city.region)

    @staticmethod
    def _one(candidates):
        return next(iter(candidates)) if len(candidates) == 1 else None

    def match(self, country_text, state_text, city_text):
        """Bir tekst úshligi ushın (mámleket, region, qala); jalǵız sáykeslik joq bolsa None."""
        country = self._one(self.countries.get(normalize(country_text), set()))
        if country is None:
            return None, None, None
        key = normalize(state_text)
        region = None
        for index, lookup in ((self.regions, key), (self.loose_regions, _strip_region_words(key))):
            region = self._one({r for r in index.get(lookup, set()) if r.country_id == country.id})
            if region is not None:
                break
        cities = {c for c in self.cities.get(normalize(city_text), set()) if c.region.country_id == country.id}
        if region is not None and len(cities) > 1:
            cities = {c for c in cities if c.region_id == region.id}
        city = self._one(cities)
        if city is not None:
            # Qala eń anıq: onıń regionı jeńedi
            region = city.region
        return country, region, city


def map_properties(property_model, country_model, region_model, city_model=None, dry_run=False, queryset=None):
    """
    Bos bolǵan jerde country_ref / region_ref di tekst maydanlardan toltırıw (qala modeli berilse city_ref de).

    Model klaslardı aladı, sonda data migration óziniń tariyxıy model lerin bere aladı.
    `queryset` islewdi ayırım mehmanxanalarǵa shekemleydi (mısalı seed command jasaǵanlar).
    Esabat dict in qaytaradı; dry_run=True bolsa hesh nárse jazılmaydı.
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
    # order_by(): modeldiń ádetdegi tártibi distinct() ge created_at tı da kórsetken bolar edi
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
        if city_model is not None:
            if city is not None:
                report['city'] += count
            else:
                report['unmatched_city'][f'{country.name_en} / {city_text or "(empty)"}'] += count
        if not dry_run:
            places = {'country_ref': country, 'region_ref': region}
            if city_model is not None:
                places['city_ref'] = city
            rows.update(**places)
    return report


def format_report(report, dry_run=False):
    lines = [
        f"Geography mapping{' (dry run, nothing written)' if dry_run else ''}: "
        f"{report['properties']} properties, {report['already_mapped']} already mapped.",
        f"  matched: country {report['country']}, region {report['region']}",
    ]
    for level in ('country', 'region'):
        unmatched = report[f'unmatched_{level}']
        if unmatched:
            lines.append(f'  left NULL ({level}):')
            lines += [f'    {count:>4}  {value}' for value, count in unmatched.most_common()]
    return '\n'.join(lines)
