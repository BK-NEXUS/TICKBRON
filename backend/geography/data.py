"""
Initial geography data: Uzbekistan in full (14 first-level regions), plus the regions
and cities of Kazakhstan and Turkey used by the demo data and a few major ones.

NOTE: the Uzbek (Latin) and Russian names below need a review by native speakers.

Each name triple is (uz, ru, en). Loaded by migration geography/0002 and by
`python manage.py load_geography`; rows are matched by country code / slug and never
overwritten, so edits made in the admin Geography screen are kept.
"""
from django.utils.text import slugify

GEOGRAPHY = [
    {
        'code': 'UZ', 'currency': 'UZS', 'names': ("O'zbekiston", 'Узбекистан', 'Uzbekistan'),
        'regions': [
            (('Toshkent shahri', 'город Ташкент', 'Tashkent City'), [
                ('Toshkent', 'Ташкент', 'Tashkent'),
            ]),
            (('Toshkent viloyati', 'Ташкентская область', 'Tashkent Region'), [
                ('Nurafshon', 'Нурафшан', 'Nurafshon'),
                ('Chirchiq', 'Чирчик', 'Chirchiq'),
                ('Angren', 'Ангрен', 'Angren'),
                ("G'azalkent", 'Газалкент', 'Gazalkent'),
            ]),
            (('Samarqand viloyati', 'Самаркандская область', 'Samarkand Region'), [
                ('Samarqand', 'Самарканд', 'Samarkand'),
                ('Urgut', 'Ургут', 'Urgut'),
            ]),
            (('Buxoro viloyati', 'Бухарская область', 'Bukhara Region'), [
                ('Buxoro', 'Бухара', 'Bukhara'),
                ("G'ijduvon", 'Гиждуван', 'Gijduvan'),
            ]),
            (('Xorazm viloyati', 'Хорезмская область', 'Khorezm Region'), [
                ('Urganch', 'Ургенч', 'Urgench'),
                ('Xiva', 'Хива', 'Khiva'),
            ]),
            (("Qoraqalpog'iston Respublikasi", 'Республика Каракалпакстан', 'Republic of Karakalpakstan'), [
                ('Nukus', 'Нукус', 'Nukus'),
                ("Mo'ynoq", 'Муйнак', 'Moynaq'),
            ]),
            (("Farg'ona viloyati", 'Ферганская область', 'Fergana Region'), [
                ("Farg'ona", 'Фергана', 'Fergana'),
                ("Qo'qon", 'Коканд', 'Kokand'),
                ("Marg'ilon", 'Маргилан', 'Margilan'),
                ('Rishton', 'Риштан', 'Rishtan'),
            ]),
            (('Andijon viloyati', 'Андижанская область', 'Andijan Region'), [
                ('Andijon', 'Андижан', 'Andijan'),
            ]),
            (('Namangan viloyati', 'Наманганская область', 'Namangan Region'), [
                ('Namangan', 'Наманган', 'Namangan'),
            ]),
            (('Qashqadaryo viloyati', 'Кашкадарьинская область', 'Kashkadarya Region'), [
                ('Qarshi', 'Карши', 'Karshi'),
                ('Shahrisabz', 'Шахрисабз', 'Shahrisabz'),
            ]),
            (('Surxondaryo viloyati', 'Сурхандарьинская область', 'Surkhandarya Region'), [
                ('Termiz', 'Термез', 'Termez'),
                ('Boysun', 'Байсун', 'Boysun'),
            ]),
            (('Navoiy viloyati', 'Навоийская область', 'Navoi Region'), [
                ('Navoiy', 'Навои', 'Navoi'),
                ('Nurota', 'Нурата', 'Nurata'),
            ]),
            (('Jizzax viloyati', 'Джизакская область', 'Jizzakh Region'), [
                ('Jizzax', 'Джизак', 'Jizzakh'),
                ('Zomin', 'Заамин', 'Zaamin'),
            ]),
            (('Sirdaryo viloyati', 'Сырдарьинская область', 'Sirdarya Region'), [
                ('Guliston', 'Гулистан', 'Gulistan'),
            ]),
        ],
    },
    {
        'code': 'KZ', 'currency': 'KZT', 'names': ("Qozog'iston", 'Казахстан', 'Kazakhstan'),
        'regions': [
            (('Olmaota shahri', 'город Алматы', 'Almaty City'), [
                ('Olmaota', 'Алматы', 'Almaty'),
            ]),
            (('Astana shahri', 'город Астана', 'Astana City'), [
                ('Astana', 'Астана', 'Astana'),
            ]),
            (('Chimkent shahri', 'город Шымкент', 'Shymkent City'), [
                ('Chimkent', 'Шымкент', 'Shymkent'),
            ]),
            (('Turkiston viloyati', 'Туркестанская область', 'Turkistan Region'), [
                ('Turkiston', 'Туркестан', 'Turkistan'),
            ]),
        ],
    },
    {
        'code': 'TR', 'currency': 'TRY', 'names': ('Turkiya', 'Турция', 'Turkey'),
        'regions': [
            (('Istanbul viloyati', 'Стамбул (ил)', 'Istanbul Province'), [
                ('Istanbul', 'Стамбул', 'Istanbul'),
            ]),
            (('Anqara viloyati', 'Анкара (ил)', 'Ankara Province'), [
                ('Anqara', 'Анкара', 'Ankara'),
            ]),
            (('Antaliya viloyati', 'Анталья (ил)', 'Antalya Province'), [
                ('Antaliya', 'Анталья', 'Antalya'),
            ]),
            (('Nevshehir viloyati', 'Невшехир (ил)', 'Nevsehir Province'), [
                ('Nevshehir', 'Невшехир', 'Nevsehir'),
                ('Goreme', 'Гёреме', 'Goreme'),
                ('Urgup', 'Ургюп', 'Urgup'),
            ]),
        ],
    },
]


def region_slug(country_code, name_en):
    return slugify(f'{country_code}-{name_en}')


def city_slug(region_slug_value, name_en):
    return slugify(f'{region_slug_value}-{name_en}')


def load_geography(country_model, region_model, city_model):
    """
    Create the initial rows that do not exist yet; never change existing ones.

    Takes the model classes so a data migration can pass its historical models
    (which do not run the models' own save(): codes and slugs are set here).
    Returns (countries, regions, cities) created.
    """
    created = [0, 0, 0]
    for country_order, spec in enumerate(GEOGRAPHY, start=1):
        uz, ru, en = spec['names']
        country, was_created = country_model.objects.get_or_create(
            code=spec['code'],
            defaults={'name_uz': uz, 'name_ru': ru, 'name_en': en, 'currency': spec['currency'],
                      'sort_order': country_order * 10},
        )
        created[0] += was_created
        for region_order, (region_names, cities) in enumerate(spec['regions'], start=1):
            r_uz, r_ru, r_en = region_names
            slug = region_slug(spec['code'], r_en)
            region, was_created = region_model.objects.get_or_create(
                slug=slug,
                defaults={'country': country, 'name_uz': r_uz, 'name_ru': r_ru, 'name_en': r_en,
                          'sort_order': region_order * 10},
            )
            created[1] += was_created
            for city_order, (c_uz, c_ru, c_en) in enumerate(cities, start=1):
                _, was_created = city_model.objects.get_or_create(
                    slug=city_slug(region.slug, c_en),
                    defaults={'region': region, 'name_uz': c_uz, 'name_ru': c_ru, 'name_en': c_en,
                              'sort_order': city_order * 10},
                )
                created[2] += was_created
    return tuple(created)
