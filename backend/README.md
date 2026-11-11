# TICKBRON Backend

TICKBRON ushın Django + Django REST Framework + PostgreSQL + Redis + Celery tiykarındaǵı backend.

## Ornatıw (Setup)

### Aldın ala talaplar (Prerequisites)
- Python 3.13 (3.11+ de isleydi)
- PostgreSQL 16 (14+ de isleydi). Taza kompyuterde eń ańsat jol: Docker (`scripts/demo-tunnel.ps1` yamasa `.ai/DEPLOY_DOCKER.md`)
- Redis 7+ (tek production ushın; development ha test waqtında local memory cache isleydi)

### Ornatıw ámeller

1. Virtual environment dúziń:
```bash
python -m venv venv
source venv/bin/activate  # Windows'ta: venv\Scripts\activate
```

2. Dependency'lerdi ornatıń:
```bash
pip install -r requirements-dev.txt   # development ushın; production tek requirements.txt'ti ornatadı
```

3. Environment variable'larǵa sazlamalardı jazıń:
```bash
cp .env.example .env
# .env faylın óz sazlamalarıńızǵa qarap túzetiń (development ushın DEBUG=True qoyıń)
```
Windows'ta DB_HOST ushın `127.0.0.1` jazıń (`localhost` IPv6 arqalı barıp, hár API soraw 2 sekund kútip qaladı).

4. Migration'lardı isletiń:
```bash
python manage.py migrate
```

5. Superuser jaratıń:
```bash
python manage.py createsuperuser
```

6. Development server'di iske túsiriń:
```bash
python manage.py runserver
```

Demo maǵlıwmatlar kerek bolsa (tek `DEBUG=True` waqtında): `python manage.py seed_demo` hám `python manage.py seed_demo_stats`.

## Celery isletiw

### Worker
```bash
celery -A config worker -l info
```

### Beat (rejelestirilgen tapsırmalar ushın)
```bash
celery -A config beat -l info
```
Beat'tiń tek **bir** nusqası isleýi kerek. Rejelestirilgen tapsırmalar: valyuta kursları, bronlardı tekseriw, ótken jasawlardı jabıw, reklama jańalaw, ótken sessiyalardı tazalaw.

## Testlew

Testlerdi isletiw:
```bash
pytest
```
Model ózgergennen keyin: `pytest --create-db`. Bazı bir tolıq test (taza bazada) uzaq dawam etedi, sonıń ushın bir fayldı isletiw múmkin: `pytest bookings/tests/test_views.py`.

Coverage menen:
```bash
pytest --cov=. --cov-report=html
```

Eki pytest bir waqıtta bir test database'di ortaq paydalanbawı kerek: `TICKBRON_TEST_DB_SUFFIX` ózgeriwshisin qoyıń (`.ai/README.md`).

## API hújjetleri

- Swagger UI: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- OpenAPI Schema: http://localhost:8000/api/schema/

(Production'da tek staff ushın ashıq.) Server tiriligin tekseriw: `/healthz/` hám `/readyz/`.

## Kod sapası (Code Quality)

Kodtı formatlaw:
```bash
black .
isort .
```

Lint:
```bash
flake8
```

## Proekt dúzilisi (Project Structure)

```
backend/
├── config/          # Django proekt sazlamaları (settings, urls, celery)
├── manage.py        # Django management script
├── requirements.txt # Python dependency'ler (production)
├── requirements-dev.txt # development dependency'ler
├── .env.example     # Environment variable úlgisi
└── README.md        # Usı fayl
```
Qalǵan app'lar: `users`, `properties`, `bookings`, `partner`, `admin_panel`, `geography`, `promotions`, `chat`, `accounts`, `currency`, `common`.

## Qáwipsizlik eskertpeleri (Security Notes)

- `.env` faylın hesh qashan commit qılmań
- Production'da kúshli SECRET_KEY paydalanıń
- Production'da DEBUG=False qoyıń
- CSRF hám CORS sazlamaların durıs sazlań
- Production'da HTTPS paydalanıń
