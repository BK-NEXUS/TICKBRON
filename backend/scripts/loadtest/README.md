# Load test (R14)

Mehmanlardıń jolları ushın Locust script'i: izlew (search), filter variantları, mehmanxana beti, bandlıq (availability), quote hám bron jaratıw.
Tek local development ushın: ol bulk demo maǵlıwmatlardı talap etedi hám `X-Forwarded-For` header'in jasalma qoyadı, sonıń ushın hesh qashan production'ǵa baǵdarlamań.

```bash
# 1. kólemli ayrıqsha database (tek DEBUG waqtında)
DB_NAME=tickbron_perf python manage.py migrate
DB_NAME=tickbron_perf python manage.py seed_demo_bulk --hotels 2000 --guests 300 --bookings 10000 --days 90

# 2. 1000 taza mehman hám olardıń sessiyaları (scripts/loadtest/sessions.json faylına jazadı, git ignore etilgen)
DB_NAME=tickbron_perf python scripts/loadtest/make_sessions.py

# 3. production sıyaqlı server: bir proxy qádemi artında birneshe worker, sonda hár jasalma kelushiniń óz mánzili boladı
# (throttle'lar QOSILǴAN qaladı: olar mánzil boyınsha)
DB_NAME=tickbron_perf NUM_PROXIES=1 gunicorn config.wsgi -w 4 -b 127.0.0.1:8000

# 4. 200 paydalanıwshı, 2 minut, CSV + juwmaq
locust -f scripts/loadtest/locustfile.py --headless -u 200 -r 20 -t 2m --host http://127.0.0.1:8000 --csv /tmp/loadtest
```

Kóriwshi paydalanıwshılar (salmaq 8) izleydi, mehmanxananı ashadı, bandlıqtı tekseredi hám quote sorayı. Bron jasawshılar (salmaq 2) sonı isleydi
hám keyin `sessions.json`'daǵı sessiya menen pending bron jaratadı. Hár bronnan keyin bron jasawshı jańa mehmandı aladı. Biznes qaǵıydası boyınsha bas tartıw (400/409/429: pending bronlar kóp,
bos xona joq, throttle) endpoint'tiń tabısı dep esaplanadı hám óz atı menen aytıladı.

## Production sıyaqlı server hám 3000 kelushi
`DEBUG=False` bolǵan server tek https'ke juwap beredi hám jazıw sorawlarınıń origin'in tekseredi. Script'ke onıń `CSRF_TRUSTED_ORIGINS`'inen birin beriń,
ol proxy arqalı https penen kelgen kelushi sıyaqlı isleydi; sessiyalardı `DEBUG=True` penen jasań (script basqasha bas tartadı):

```bash
DEBUG=True DB_NAME=tickbron_perf python scripts/loadtest/make_sessions.py
LOADTEST_ORIGIN=https://perf.example.com LOADTEST_WAIT_MIN=40 LOADTEST_WAIT_MAX=80 \
  locust -f scripts/loadtest/locustfile.py --headless -u 3000 -r 30 -t 12m --host http://127.0.0.1:8000
```
`LOADTEST_WAIT_MIN/MAX` - kelushi keyingi basıwdan aldın neshe sekund oqıydı: 1-3 (standart) stress test, 40-80 adamlar oqıp turǵan jaǵday.
Test aralıǵında Redis'tiń tek `public:` kilt'lerin óshiriń (ashıq betlerdiń nusqaları), pútkil Redis'ti emes: onda throttle esaplawıshları da bar.
