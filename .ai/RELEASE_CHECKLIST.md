# TICKBRON Backend Release Checklist

Esletpe: bul dizim tariyxıy jazıwlardı (checkpoint'ler, R-itemler) saqlaydı. Eń sońǵı jaǵday hám iske túsiriw tártibi ushın `.ai/LAUNCH_DAY.md`, `.ai/LAUNCH_TODO.md` hám `.ai/DEPLOY_DOCKER.md` qarań. Eń tómende "Sońǵı qosımshalar (2026-11)" bólimi bar.

## Backend Main Plan (Checkpoints 1-20)
**Jaǵday:** TAYAR
**Sana:** 2026-09-21
**Iyesi:** Kolya

## Test nátiyjeleri
- **Tolıq test suite:** 568 test ótti, 2 ótkizip jiberildi
- **Test qamtıwı:** Barlıq tiykarǵı funkciyalar testlengen
- **Test isletiw waqtı:** ~2:49 minut
- **Test ortalıǵı:** Django 4.2.7, Python 3.13.1, pytest 9.1.1

## Migration jaǵdayı
- **Taza database migration:** ✅ TAZA
- **Qollanılǵan migration fayllar:** 12 app boyınsha 27 migration
- **Sońǵı migration:** payments.0002_alter_paymentauditlog_action
- **Joq migration'lar:** Joq
- **Maǵlıwmat joǵalıw qáwipi:** Joq (barlıq maydanǵa tek jańa tańlaw qosıldı)

## OpenAPI Schema jaǵdayı
- **Jaratıw:** ✅ TABISLI
- **Shıǵıs fayl:** schema.yml
- **Eskertiwler:** 43 (17 biregey) - kritik emes tip hám serializer eskertiwleri
- **Qátelikler:** 68 (17 biregey) - serializer'siz APIView'ler ushın tınısh almastırıw
- **Qamtıw:** Barlıq iske asırılǵan endpoint'ler hújjetlestirilgen

## Bir waqıtta islew (Concurrency) tekseriwi
- **Bron dvigateli testleri:** ✅ 24 test ótti
- **Eki ret bronlawdıń aldın alıw:** ✅ Tastıyıqlandı
- **Transaction qáwipsizligi:** ✅ Tastıyıqlandı
- **State machine putinligi:** ✅ Tastıyıqlandı

## Ruxsat shegaraların tekseriw (Permission Boundary Sweep)
### Rolge tiykarlanǵan kirisiw (RBAC)
- **Anonim paydalanıwshılar:** ✅ Autentifikaciya talap etetuǵın endpoint'lerge kire almaydı (403 qaytadı)
- **Ápiwayı paydalanıwshılar:** ✅ Admin/partner endpoint'lerge kire almaydı (403 qaytadı)
- **Hotel-Owner roli:** ✅ Tek óz mehmanxanaları menen shegaralanǵan (basqa mehmanxanalar ushın 404)
- **Staff paydalanıwshılar:** ✅ Admin endpoint'lerge kire aladı, biraq hotel-owner akkauntın jarata almaydı (403)
- **Super-Admin:** ✅ Tolıq admin kirisiwi

### Maǵlıwmat izolyaciyası
- **Partner API:** ✅ Hotel-owner'ler tek óz mehmanxanaların, xonaların, rate'lerin kóre hám basqara aladı
- **Payment API:** ✅ Paydalanıwshılar tek óz tólem tranzakciyaların kóredi (queryset filtrlew)
- **Account API:** ✅ Paydalanıwshılar tek óz sevimlilerine, sharıhlarına, tariyxına kire aladı
- **Booking API:** ✅ Paydalanıwshılar tek óz bronlarına kire aladı
- **Admin API:** ✅ Staff/super-admin tiyisli shegaralanıwǵa iye

### Ruxsat testleriniń qamtıwı
- **partner/tests/test_partner_api.py:** 13 ruxsat shegarası testi
- **admin_panel/tests/test_admin_api.py:** 4 ruxsat shegarası testi
- **accounts/tests/test_views.py:** 3 ruxsat shegarası testi
- **bookings/tests/test_views.py:** 4 ruxsat shegarası testi
- **users/tests/test_views.py:** Authentication standart boyınsha kerek
- **payments/tests/test_views.py:** Queryset arqalı paydalanıwshı izolyaciyası

## Qáwipsizlik kóriwin tastıyıqlaw
### Checkpoint 04 (Auth Security)
- ✅ Parol quramalılıǵı (12+ belgi, quramalılıq tekseriwi)
- ✅ 5 sәtsiz urınıstan keyin akkaunt qulıplanadı (30 minut)
- ✅ Waqıtsha e-mail'lerdi biykarlaw
- ✅ Kirisiw urınısları ushın IP baqlaw
- ✅ Qáwipsiz cookie'ler menen session tiykarındaǵı authentication

### Checkpoint 15 (Payment Security)
- ✅ Webhook imza tekseriw (Payme HMAC-SHA256, Click MD5)
- ✅ Waqıt tekseriw (5 minut aynası)
- ✅ Replay hújimniń aldın alıw (qaytalanǵan event ID biykarlanadı)
- ✅ Idempotency qollap-quwatlawı (qaytalanǵan kilt anıqlaw)
- ✅ Karta maǵlıwmatı saqlanbaydı (tek token/siltemeler)
- ✅ Audit izi (PaymentAuditLog)

### Checkpoint 18 (Partner Security)
- ✅ Hotel-owner rolge tiykarlanǵan kirisiw
- ✅ Mehmanxana iyeligi shegaralawı (iyeler tek óz mehmanxanalarına kire aladı)
- ✅ Rolge tiykarlanǵan endpoint qorǵawı
- ✅ Mehmanxananı tastıyıqlaw ushın admin moderaciya endpoint'leri

### Checkpoint 19 (Rate Limiting Security)
- ✅ Login endpoint: IP boyınsha minutına 10 soraw
- ✅ Registration endpoint: IP boyınsha minutına 5 soraw
- ✅ Payment initiation: paydalanıwshı boyınsha minutına 20 soraw
- ✅ Property search: IP boyınsha minutına 100 soraw
- ✅ OTP endpoint: házirge qollanılmaydı (checkpoint 21 iske asırılmaǵan)
- ✅ Test rejimin anıqlaw (testlerdiń qulawınıń aldın alıw)

## Production ushın Environment Variable'lar

### Kritik qáwipsizlik ózgeriwshileri (MÁJBÚRIY QOYILIWI KEREK)
- `SECRET_KEY` - Django secret key (mınaw menen jasań: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`)
- `DEBUG` - Production'da `False` qoyıń
- `ALLOWED_HOSTS` - Ruxsat etilgen host atlarınıń vergul menen ayırılǵan dizimi (mısalı `tickbron.com`)

### Database sazlaması
- `DB_NAME` - Database atı
- `DB_USER` - Database paydalanıwshısı
- `DB_PASSWORD` - Database paroli
- `DB_HOST` - Database host'ı
- `DB_PORT` - Database porti
- `DB_SSLMODE` - PostgreSQL SSL rejimi (standart: `prefer`)

### CORS hám qáwipsizlik
- `CSRF_TRUSTED_ORIGINS` - Isenimli origin'lerdiń vergul menen ayırılǵan dizimi
- `CORS_ALLOWED_ORIGINS` - Ruxsat etilgen CORS origin'lerdiń vergul menen ayırılǵan dizimi
- `SECURE_SSL_REDIRECT` - HTTPS májbúrlew ushın `True` qoyıń
- `SESSION_COOKIE_SECURE` - Qáwipsiz cookie'ler ushın `True` qoyıń
- `CSRF_COOKIE_SECURE` - Qáwipsiz CSRF cookie'ler ushın `True` qoyıń
- `SECURE_HSTS_SECONDS` - HSTS max-age (standart: 31536000)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS` - `True` qoyıń
- `SECURE_HSTS_PRELOAD` - `True` qoyıń
- `SECURE_CONTENT_TYPE_NOSNIFF` - `True` qoyıń
- `SECURE_BROWSER_XSS_FILTER` - `True` qoyıń
- `X_FRAME_OPTIONS` - Frame variantları (standart: `DENY`)

### Redis/Celery sazlaması
- `REDIS_HOST` - Redis host'ı (standart: `localhost`)
- `REDIS_PORT` - Redis porti (standart: `6379`)
- `REDIS_DB` - Redis database nomeri (standart: `0`)
- `CELERY_BROKER_URL` - Celery broker URL (standart: `redis://localhost:6379/0`)
- `CELERY_RESULT_BACKEND` - Celery result backend (standart: `redis://localhost:6379/0`)

### Rate Limiting

### Monitoring

## Tólemler (Payments)
Onlayn tólem joq: mehmanlar mehmanxanada naqd tóleydi (`.ai/PLAN_CASH_ONLY.md`). Tólem sazlamaları (`PAYMENT_TEST_MODE`, Payme, Click, Visa kilt'leri) endi joq, sonıń ushın sazlaytuǵın hesh nárse joq. Eski tólem qatarları tariyx retinde database'de qaladı.

## Joylastırıwǵa tayarlıq
- ✅ Barlıq migration'lar nolden taza qollanıladı
- ✅ Tolıq test suite ótedi
- ✅ Ruxsat shegaraları saqlanadı
- ✅ Qáwipsizlik sharaları bar
- ✅ Rate limiting sazlanǵan
- ✅ OpenAPI schema hújjetlestirilgen
- ⚠️ SMS provayder ele iske asırılmaǵan (checkpoint 21; qarań `.ai/PLAN_SMS_CHAT.md`)

## Release Notes
- Backend tiykarǵı jobası (checkpoint'ler 1-20) pitti
- Barlıq tiykarǵı funkciyalar iske asırılǵan hám testlengen
- Ruxsat sisteması durıs shegaralanǵan
- Qáwipsizlik sharaları keń
- Rate limiting sezimtal endpoint'lerdi qorǵaydı
- Taza migration tariyxı
- Keń test qamtıwı

## Keyingi qádemler
1. Production ushın barlıq qáwipsizlik ózgeriwshilerin sazlań
2. Production database'di qurıń (PostgreSQL usınıs etiledi)
3. Celery ushın Redis'ti sazlań
4. Checkpoint 21 iske asırılǵanda SMS provayderdi sazlań
5. Production joylastırıwın sınań
6. Monitoring hám logging sazlań

## Belgili sheklewler (Known Limitations)
- SMS funkciyası ele iske asırılmaǵan (checkpoint 21)
- Tip hint'ler ushın bazı OpenAPI eskertiwleri (kritik emes)
- Admin endpoint'ler serializer'siz APIView'ler paydalanadı (tınısh almastırıw)

## Tosqınlıqlar (Blockers)
Joq - Backend durıs sazlama menen joylastırıwǵa tayar.

## Qáwipsizlik header'leri (R4, 2026-10-03)

Django ilovası hár API juwapta ne jiberedi (`common/middleware.py` SecurityHeadersMiddleware, `django.middleware.security.SecurityMiddleware`, `XFrameOptionsMiddleware`; `config/settings.py:185-200`):

| Header | Mánis | Kim qoyadı |
|---|---|---|
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` (tek HTTPS sorawlar) | Django SecurityMiddleware + SecurityHeadersMiddleware (env `SECURE_HSTS_*`) |
| `X-Content-Type-Options` | `nosniff` | ekewi de |
| `X-Frame-Options` | `DENY` | XFrameOptionsMiddleware (env `X_FRAME_OPTIONS`) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | SecurityHeadersMiddleware |
| `Permissions-Policy` | `geolocation=(), microphone=(), camera=()` | SecurityHeadersMiddleware |
| `Cross-Origin-Opener-Policy` | `same-origin` | Django standartı |
| Cookie'ler | session + csrftoken: `HttpOnly`, `SameSite=Lax`, DEBUG óshirilgende `Secure` | settings |

Web server (nginx yamasa uqsas, SPA hám `/api/` aldında turatuǵın) ne qosıwı kerek, sebebi SPA'nıń HTML/JS/CSS'i Django arqalı ótpeydi. `/api/` ushın ol klient mánzilin hám scheme'ni de jiberiwi, hám klient jibergenin almastırıwı (hesh qashan qosıp qoymaw) kerek:

```
proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Host              $host;
```

- Hár HTTPS juwapta `Strict-Transport-Security: max-age=31536000; includeSubDomains` (`preload`'nı tek domendi hstspreload.org'qa jibergennen keyin qosıń); barlıq `http://`'ti `https://`'ke jiberiń (yamasa Django'da `SECURE_SSL_REDIRECT=True` hám proxy ushın `SECURE_PROXY_SSL_HEADER`).
- SPA ushın `Content-Security-Policy`, baslanıw nuqtası (shriftler 930214a'dan beri ózinde saqlanadı; karta tile host'ı `tile.openstreetmap.org` tómende kórsetilgen, sebebi izlew kartası hám orın tańlaǵısh bar, hám Payme/Click integraciyalanǵanda tólem provayder host'larin qosıń):
  `default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://tile.openstreetmap.org https://server.arcgisonline.com; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'`
- Karta maxfiyligi: brauzer karta tile'lerin tikkeley OpenStreetMap'tan júkleydi, sonıń ushın OSM kelushiniń IP mánzilin hám kórilgen aymaqtı kóredi; maxfiylik siyasatı (huqıqıy tekstler) bunı aytıwı kerek. OSM tile siyasatı kórinetuǵın atribuciyanı talap etedi (`components/mapTiles.ts` ishinde qoyılǵan) hám jeńil paydalanıw ushın; awır trafikten aldın tile provayderdi yamasa óz tile server'in jobalań.
- Clickjacking: joqarıdaǵı CSP ishinde `frame-ancestors 'none'`, hám eski brauzerler ushın `X-Frame-Options: DENY` (SPA juwapları).
- SPA hám `/media/` juwaplarında `X-Content-Type-Options: nosniff` hám `Referrer-Policy: strict-origin-when-cross-origin`.
- `/media/` (júklengen súwretler): `Content-Disposition: inline` penen, tek fayl keńeytpesinen súwret MIME túri (jpg/png/gif/webp), `nosniff`, script isletiw joq hám dizim kórsetiw joq.
- `Server` / `X-Powered-By` versiya jazıwların alıp taslań; request body ólshemin shekleń. Tolıq úlgi fayl `deploy/nginx.conf.example` (JSON ushın 1 MB, tek súwret júklew ushın 12 MB). Django da 4 MB'tan úlken JSON body'di hám 12 MB'tan úlken júklewdi (413) Content-Length header'inen biykarlaydı.
- Runtime dependency'lerdi `backend/requirements.txt`'ten ornatıń; `requirements-dev.txt` (testler, linter'ler) tek development hám CI ushın. CI - `.github/workflows/ci.yml` (testler, lint, build, `pip-audit`, `npm audit --omit=dev`).

## Production dizimi (R4, 2026-10-03)

### Environment variable'lar (juldızshalıları qáwipsiz bolmasa ilova iske túspeydi)
- [ ] `DEBUG=False` (`ALLOWED_HOSTS` ashıq domendi kórsetse, ilova `DEBUG=True`'ni da biykarlaydı)
- [ ] `FRONTEND_URL`* saytıń https:// mánzili (tiklew siltemeleri oǵan baradı) hám `EMAIL_HOST`* (+ `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`): parol tiklew e-mail'leri sol arqalı jiberiledi. Celery worker isleýi kerek, mail tapsırma arqalı jiberiledi
- [ ] `TELEGRAM_BOT_TOKEN` hám `TELEGRAM_ALERT_CHAT_ID`: qulıplanǵan akkaunt hám server qátelerine alert'ler (bos = alert joq; aldın bot'tı chat'ke qosıń)
- [ ] `SECRET_KEY`* tosınnan, 50+ belgi (`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`), `.env.example` mánisi emes
- [ ] `ALLOWED_HOSTS`* haqıyqıy host atları, `*` joq
- [ ] `CORS_ALLOWED_ORIGINS`* hám `CSRF_TRUSTED_ORIGINS`* tek SPA'nıń `https://` origin'leri
- [ ] `SECURE_SSL_REDIRECT=True`* (basqasha biykarlanadı)
- [ ] `NUM_PROXIES`* anıq qoyılıwı kerek: 0 = proxy joq, 1 = `X-Forwarded-For`'ǵa qosatuǵın bir nginx/load balancer. Qoyılmasa yamasa qáte bolsa, hár kelushi bir IP bolıp kórinedi (login throttle, lockout hám promotion esaplawıshları qulaydı, qálegen adam qálegen belgili email'di qulıplay aladı)
- [ ] `USE_X_FORWARDED_PROTO=True`* `NUM_PROXIES` > 0 bolsa hámme waqıt (nginx `X-Forwarded-Proto`'nı almastırıwı kerek); onsız Django http dep kóredi, https redirect aylanıp qaladı hám HSTS hesh qashan jiberilmeydi
- [ ] `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE`* True qaladı (standart); `USE_REDIS_CACHE`* True qaladı (standart)
- [ ] `SECURE_HSTS_PRELOAD` iyesi domendi hstspreload.org'qa jiberiwdi qarar etkenshe False qaladı (qaytarıwı qıyın); `SESSION_COOKIE_AGE` standart 7 kún
- [ ] `DB_*`, database basqa host'ta bolsa `DB_SSLMODE`* = `require`, `verify-ca` yamasa `verify-full` (ilova `disable`, `allow`, `prefer`'di biykarlaydı)
- [ ] `REDIS_URL` / `CELERY_*` (cache ortaq Redis bolıwı kerek: throttle'lar hám login lockout sonda jasaydı)
- [ ] `THROTTLE_ANON_RATE` / `THROTTLE_USER_RATE` ólshenbegenshe standart qaladı

### Test rejimleri óshirilgen
- [ ] `SMS_TEST_MODE=False`* (True OTP kodlardı juwaplarda qaytaradı)
- [ ] `scripts/checkpoint_checks/*.py` script'leri hám `scripts/smoke_test.py` hesh qashan production'ǵa qarsı isletilmeydi (olar test rejimlerin qosadı)

### Property type'lar
- [ ] Jańa server'de `python manage.py seed_property_types` isletildi (onsız iyeniń "mehmanxana qosıw" formasında tańlaytuǵın túr joq)

### Demo maǵlıwmatlar
- [ ] Production'da hesh qashan `seed_demo` / `seed_demo_stats` isletpeń (DEBUG óshirilgende olar bas tartadı)
- [ ] Production database eger qashan da dev database'den kóshirilgen bolsa, iske túsiwden aldın hár `*@tickbron.demo` akkauntın hám demo mehmanxanalardı óshiriń: `User.objects.filter(email__endswith='@tickbron.demo')`

### HTTPS hám server header'leri
- [ ] Jaramlı TLS sertifikat, HTTP→HTTPS redirect, HSTS (joqarıdaǵı "Qáwipsizlik header'leri" qarań)
- [ ] SPA juwaplarında CSP, frame-ancestors, nosniff, Referrer-Policy; qáwipsiz `/media/` xızmeti
- [ ] `/api/docs/`, `/api/redoc/`, `/api/schema/` proxy'de bloklanǵan yamasa tek staff ushın (SECURITY_REVIEW L-2)

### Database
- [ ] Eń az huqıqlı ilova DB paydalanıwshısı: `tickbron` schema obyektleriniń iyesi tek migration ushın; runtime'da CONNECT + app kesteleri boyınsha SELECT/INSERT/UPDATE/DELETE, SUPERUSER / CREATEDB / CREATEROLE joq (CREATEDB tek dev mashinalardaǵı test runner ushın kerek)
- [ ] Hár kúngi `pg_dump -Fc` backup'lar server'den tısqarıda saqlanadı (mısalı 14 kúnlik + 8 háptelik), tiklew keminde bir ret sınalǵan; hár migration'dan aldın backup
- [ ] Hár release'te `python manage.py migrate` hám `python manage.py check --deploy` ("no issues" shıǵarıwı kerek)

### Ele joq haqıyqıy akkauntlar (iyesi qararı / shártnamalar)
- [ ] Eskiz (OTP ushın SMS): API credentials hám sender id; sol waqıtqa shekem production'da OTP login isley almaydı (`SMS_TEST_MODE` False qalıwı kerek)


## Valyuta hám valyuta kursları (R6, 2026-10-03)

Mehmanxanalar USD yamasa UZS'te bahalanadı; mehmanlardan hámme waqıt UZS alınadı (Payme hám Click tek UZS qabıl etedi). Valyuta kursı bolmaǵansha USD mehmanxananı bronlaw múmkin emes (503 `exchange_rate_unavailable`, hesh nárse rezerv etilmeydi).

### Birinshi joylastırıw (bir ret)
- [ ] Aldın backup: `pg_dump -Fc` (R6 migration'ları bron alıw snapshot'ın qosadı hám hár bar bronnı toltıradı)
- [ ] `python manage.py migrate`. Birinshi R6 migration'ı (`currency.0001`) hesh nárse ózgertpesten TOQTAYDI, eger qálegen property, room type yamasa rate plan USD/UZS'ten basqa valyutada bahalanǵan bolsa, hám olardı dizimleydi. Sol qatarlardı túzetiń (haqıyqıy USD yamasa UZS bahasın mehmanxana iyesi menen anıqlań), keyin `migrate`'ti qayta isletiń.
- [ ] Migration'nan soń dárhal `python manage.py fetch_exchange_rates`: búgingi CBU USD kursın saqlaydı, USD mehmanxanalar birden bronlanıwı múmkin. Ol kursın yamasa nege islemegenin shıǵaradı. Server `https://cbu.uz`'ge shıǵa alıwı kerek (outbound HTTPS).
- [ ] Celery **beat** hám worker isleydi: `currency.tasks.fetch_exchange_rates` hár kúni Asia/Tashkent waqtı menen 09:00 hám 18:00'de isleydi (`CELERY_BEAT_SCHEDULE`), 10 minut aralıqlı 3 qayta urınıs penen.
- [ ] `GET /api/v1/admin-panel/exchange-rates/status/`'ti super-admin retinde tekseriń: `rate` bar, `stale: false`, `last_error: null`.

### Qolda "kursın házir alıw"
- `python manage.py fetch_exchange_rates` (rejelestirilgen tapsırma menen birdey kod; qálegen waqıtta qáwipsiz, birdey CBU sanası bir ret saqlanadı).

### Sazlamalar (environment, standart mánisler)
- `FX_STALE_AFTER_DAYS=3`: eski kurs ele de isletiledi, biraq `stale: true` dep belgilenedi (quote, bron, status) hám warning retinde jazıladı.
- `FX_MAX_CHANGE=0.10`: házirgi kurstan 10% artıq parıq qılatuǵın jańa kurs `rejected` retinde saqlanadı hám super-admin qabıllamaǵansha isletilmeydi (`POST /api/v1/admin-panel/exchange-rates/{id}/accept/`, eski hám jańa kurs penen admin audit log'qa jazıladı).
- `FX_MIN_RATE=1000`, `FX_MAX_RATE=100000`: USD ushın so'm shegarası; sırtqısı biykarlanadı.
- `FX_FETCH_TIMEOUT=10` (sekund).

### Kurs eskirgende yamasa joq bolǵanda
- [ ] Status endpoint'inde `last_error`'ǵa qarań (tarmaq, CBU juwap formatı, biykarlanǵan sekirik), `fetch_exchange_rates`'ti qolda isletiń, hám haqıyqıy sekirik sebepli durıs kurs biykarlanǵan bolsa, super-admin retinde qabıllań.

### Production'dan aldın tekserilmegen (R6, 2026-10-05)
Tólem summa birlikleri, `backend/payments/adapters.py` ishinde iske asırılǵanday:
- Payme: tiyin (1 so'm = 100 tiyin). Payme'niń óz Merchant API hújjetinde tastıyıqlanǵan ("Сумма платежа (в тийинах)").
- Click: onlıq san retinde so'm ("1000.00"). Click'tiń óz hújjetinen TEKSERILMEGEN; házirge birden-bir derek - Click integraciya kitapxanasındaǵı summa formatı. Boljaw dep esaplań.

Hár qanday haqıyqıy tólemnen aldın, tómendegi hár punkt provayderdiń sandbox'ında haqıyqıy merchant credentials penen tolıq sınalıwı kerek (házirge hesh biri tekserilmegen):
- [ ] Click summa birligi (so'm yamasa tiyin): create, prepare/complete webhook'lar hám refund.
- [ ] Payme bólekshe qaytarıw qaǵıydaları (ulıwma ruxsat etilgen be, neshe ret, eń kem summa, webhook ne jiberedi).
- [ ] Click bólekshe qaytarıw qaǵıydaları (sol sorawlar).
- [ ] Payme adapter tolıq: create, webhook imza hám summa tekseriw, tolıq qaytarıw, bólekshe qaytarıw, qátelik hám qayta urınıs.
- [ ] Click adapter tolıq: sol qádemler.

## Biznes sanası hám avtomat tamamlaw (R12 phase 1, 2026-10-05)

- [ ] `TIME_ZONE` `UTC` qaladı. `BUSINESS_TIME_ZONE` (env, standart `Asia/Tashkent`) bron check-in, statistika hám avtomat tamamlaw ushın "búgin"'di anıqlaydı. Basqa mámleketlerdegi mehmanxanalar házirge birdey biznes sanasın paydalanadı.
- [ ] **Production'da Celery beat, worker hám Redis isleýi kerek.** `CELERY_TIMEZONE = BUSINESS_TIME_ZONE`: `CELERY_BEAT_SCHEDULE` ishindegi beat waqıtları Toshkent waqtı (valyuta kursları 09:00 hám 18:00, avtomat tamamlaw 00:05). Beat bolmasa tastıyıqlanǵan jasawlar hesh qashan tamamlanbaydı hám Status "stayed" sanları 0'de qaladı.
- [ ] **Aldın backup: hár ret `migrate`'den aldın `pg_dump -Fc`.** R12 phase 1 migration'ları: `bookings/0009` (avtomat tamamlaw isletiw tariyxı), `payments/0003` (Refund kestesi), `payments/0004` (hár `refunded` / `partially_refunded` tólem ushın `succeeded` Refund qatarın toltıradı; onıń reverse'i tek sol qatarlardı óshiredi), `admin_panel/0006` (audit actionlar), `accounts/0002` (notification `code` / `params`). Hámmesi qaytarıladı.
- [ ] Joylastırıwdan keyin bir ret: `python manage.py complete_finished_stays --dry-run` (ele `confirmed` bolǵan ótken jasawlar sanın shıǵaradı), keyin `--dry-run`'sız (olardı tamamlaydı; pending, cancelled yamasa no_show'ǵa tiymeydi).
- [ ] Erteńine tańda super-admin retinde `GET /api/v1/admin-panel/auto-completion/status/`'ti tekseriń: `last_run.finished_at` Toshkent waqtı menen 00:05'ten keyin, `failed: 0`, `waiting: 0`.

## Qaytarıwlar (Refunds) (R12 phase 1, 2026-10-06)

- [ ] **Payme, Click hám Visa menen bólekshe qaytarıw TEKSERILMEGEN** (`payments/adapters.py` ishinde `SUPPORTS_PARTIAL_REFUND = None`). Hár provayderdiń sandbox'ında bólekshe qaytarıw sınalmaǵansha, hár bólekshe qaytarıw provayderdi ótkizip jiberedi hám `needs_manual` retinde saqlanadı: staff qolda tóleydi hám onı `POST /api/v1/admin-panel/refunds/{id}/mark-done/` menen jabadı (`provider_reference` májbúriy). Sandbox testi tabıslı bolǵannan keyin, tek sol adapter'de `SUPPORTS_PARTIAL_REFUND = True` qoyıń (test penen).
- [ ] Tolıq qaytarıwlar refund qatarı commit etilgennen keyin provayderdi shaqıradı. Provayder qátesi refund'tı `failed` qaldıradı; super-admin'ler onı `GET /api/v1/admin-panel/refunds/needs-attention/`'den qayta isletedi.
- [ ] Staff'tan birew hár kúni needs-attention dizimin tekseredi (failed, needs_manual, bir saattan artıq pending).
- [ ] `migrate` `Refund backfill: N refund row(s) created, M payment(s) skipped` dep shıǵaradı. Skipped = audit qatarı joq `partially_refunded` tólem (summa belgisiz, hesh qashan oylap tabılmaydı) yamasa tólemnen artıq audit summaları: hárbirin qolda tekseriń hám haqıyqıy summa menen qaytarıwın jazıń.

## No-show esabatlar hám qaytarıw (R12b, 2026-10-07)

- [ ] **Aldın backup: `migrate`'den aldın `pg_dump -Fc`.** R12b migration'ları: `bookings/0010` (NoShowReport, `Booking.no_show_refund_percent`; bar bronlar 0 aladı), `admin_panel/0008` (audit actionlar). Ekewi de qaytarıladı.
- [ ] **Payme, Click hám Visa menen bólekshe qaytarıw tekserilmegen.** No-show qaytarıw tólemniń 50%'i, sonıń ushın haqıyqıy rejimde `needs_manual` retinde saqlanadı hám staff qolda tóleydi (joqarıdaǵı Refunds qarań). Qosıwdan aldın hár provayderdiń bólekshe qaytarıwın onıń sandbox'ında tekseriń.
- [ ] **Yurist mehmanlarǵa kórsetiletuǵın qaytarıw tekstin** (`no_show_refund_statement`, hár tilde) hám iyesi/staff tekstlerin iske túsiwden aldın tekseriwi kerek; 50% wáde - shártnama sharttı.
- [ ] Tastıyıqlaw ushın sazlamalar: `NO_SHOW_REFUND_PERCENT` (50), `NO_SHOW_REPORT_WINDOW_DAYS` (7), `NO_SHOW_FLAG_*`, `THROTTLE_NO_SHOW_REPORT_RATE` (20/hour).


## Mehmanxana promotion'ları (R10, 2026-10-09)

- [ ] **Aldın backup: `migrate`'den aldın `pg_dump -Fc`.** R10 migration'ları: `promotions/0001` (eki jańa keste) hám `admin_panel/0009` (audit actionlar). Ekewi de qaytarıladı; bar kestege maydan qosılmaydı.
- [ ] **Celery beat isleýi kerek** (tapsırma `promotions.tasks.end_expired_promotions`, 00:10 Asia/Tashkent). Onsız admin dizimindegi statuslar eskirip qaladı; mehmanlarǵa dál tuwrı kórsetiledi (sanalardan esaplanadı).
- [ ] **Production'da cache Redis bolıwı kerek** (`USE_REDIS_CACHE`): kóriw hám click sanları sonda dublikattan tazalanadı. Cache islemese hesh nárse sanalmaydı (`Promotion counter skipped` warning jazıladı).
- [ ] Yurist "Reklama" belgisiniń dál tekstin hám Ózbekstandaǵı reklama huqıqı talaplarin tastıyıqlaydı (frontend belgisi - i18n kilt).
- [ ] Reklama bahaları, invoice'ler hám qaytarıwlar platformadan tısqarıda islenedi; super-admin `mark-paid` hám kelisilgen bahanı jazadı.


## "Kelmadi" ekranları (R12b frontend, 2026-10-10)

- [ ] **Yurist mehmanlarǵa kórsetiletuǵın qaytarıw gápin** (`no_show_refund_statement` uz, ru, en) hám iyesi menen staff dialog tekstlerin (`noShow.*`, `noShowAdmin.*`) iske túsiwden aldın tekseriwi kerek.
- [ ] Bul funkciyanı ózgertetuǵın ashıq buyırtpashı qararları: provayder haqısın kim tóleydi, qaytarılmaytuǵın tariflerge qollanıladı ma, mehmanxana pulǵa iye bolama yamasa TICKBRON odan qaytaradı.


## Sońǵı tekseriw (R15, 2026-10-18)

Usı sanadaǵı koddaǵı nátiyjeler (PR #54 den keyingi `master`, hám R15 PR'diń E2E ózgerisleri):
- **Backend:** `pytest --create-db`: 3153 ótti, 0 qulaǵan (41 min 32 s), `makemigrations --check` taza.
- **Frontend:** `npm test` 170 fayl, 1954 test ótti; `npm run lint` taza; `npm run build` taza (birinshi júklew 85 KB app + 59 KB React, gzip).
- **Haqıyqıy stack'ke qarsı E2E** (seed_demo + seed_demo_stats, Chromium): 29 den 29 ótti (tolıq isletiwde 25; 3 crawl hám promotions J5 tómendegi eki ortalıq túzetiwinen keyin ekinshi isletiwde ótti). Crawl hár betti mehman, iyesi hám admin retinde 1440px hám 390px'te kóredi: 404 joq, ólik tugme yamasa console qáteligi joq.
- **Load test** (R14, `.ai/PERFORMANCE_REPORT.md`): 200 paydalanıwshı, 0 qátelik, server tárepinde p95 izlew 163 ms, bronlaw 36 ms.

E2E'ni qalay isletiw (`frontend/playwright.config.ts`): backend `seed_demo` hám `seed_demo_stats` penen, `THROTTLE_ANON_RATE` hám `THROTTLE_USER_RATE` júdá joqarı, hám hár IP boyınsha limitler óshirilgen (olar bekitilgen: izlew 100/min, promotions 60/min, login 10/min; E2E hámmesin bir mánzilden jiberedi), frontend 3000 portta `npm run dev`, keyin `npm run test:e2e`. Playwright'tiń óz Chromium'ı ornatılmaǵan bolsa, `E2E_CHROMIUM_PATH` Chromium'ǵa qaratıladı. Crawl OpenStreetMap tile'lerine ózi juwap beredi, sonıń ushın internet kerek emes.

### Birinshi production iske túsiwden aldın (birinshi dizimnen beri qosılǵan hámme nárse)
- [ ] **Aldın backup: `migrate`'den aldın `pg_dump -Fc`.** 2026-10-10'dan beri qosılǵan migration'lar, hámmesi qosımsha yamasa qaytarıladı: `bookings/0011` hám `properties/0014` (biypul biykar etiw: rate-plan shártleri, bronlarda biykar etiw snapshot'ı, refund sebebi `cancel`), `properties/0015` (`RoomType.is_vip`), `admin_panel/0010`, `0011` (audit actionlar, IP, tólem oqıwları), `users/0007`-`0009` (biregey tastıyıqlanǵan telefon, hash'lengen kodlar, SMS login baǵanaları óshirildi). R12 qosımshaları, R14 yamasa R15 menen migration kelmegen.
- [ ] Jańa kitapxana **XlsxWriter 3.2.9** (Excel eksport, `requirements.txt`); server'de `pip install -r requirements.txt`.
- [ ] CBU valyuta kursları júklengen (joqarıdaǵı R6 bólimi); USD yamasa EUR'da bahalanǵan mehmanxana kurs bolmaǵansha 503 `exchange_rate_unavailable` menen bronlawdı biykarlaydı.
- [ ] Karta tile'leri `tile.openstreetmap.org`'dan keledi (CSP `img-src`, joqarıdaǵı maxfiylik eskertpesi): mehmannıń brauzeri kartalı betlerde OpenStreetMap penen baylanısadı. OSM paydalanıw siyasatı kútilgen trafikke jaraydı ma, yamasa pullı tile provayder kerekpe, qarar etiń.
- [ ] Sun'iy joldas súwretleri Esri World Imagery'den keledi (`server.arcgisonline.com`, CSP `img-src`'te de, hám karta ústinde atribuciya kórsetiledi). Esri shártleri jeńil paydalanıwdı qamtıydı: haqıyqıy trafikten aldın kilt'li joldas provayderdi alıń (mısalı MapTiler yamasa Mapbox) hám frontend build'te `VITE_SATELLITE_TILE_URL` hám `VITE_SATELLITE_ATTRIBUTION`'dı qoyıń, keyin sol provayderdiń host'ın CSP'ge qosıń. Google súwretlerin Google'dıń óz kartasınan tısqarıda paydalanıp bolmaydı.
- [ ] Server'di load test'ten ólsheń (`.ai/LOAD_TEST.md`): `.env` ishinde `WEB_WORKERS` (shama menen hár yadroǵa bir) hám `WEB_THREADS` qoyıń, keminde 4 arnawlı yadro jobalań, hám reklamadan aldın haqıyqıy server'de sol Locust faylın isletiń.
- [ ] Qaytarıw tekstlerin (biykar etiw hám no-show) hám "Reklama" belgisin yurist tekseriwi, joqarıda dizimlengenindey.

### Iyesiniń ashıq qararları
- Frontend'te UZS/USD tańlaǵısh: backend USD baha jibermeydi. `base_price_usd_approx` qosıladı yamasa tańlaǵısh alıp taslanadı?
- Property API'den erkin tekstli orın sáykeslik maydanların alıp taslaw (eski frontend ushın saqlanǵan)?
- Redis izlew cache hám súwret thumbnail'leri ataylap qaldırılǵan (R14 esabatı); thumbnail'ler "iyeler súwret júkleydi" funkciyasına tiyisli.

### Belgili, biraq túzetilmegen (hárbirin HANDOFF'ta qarań)
- Iyeler súwret júkley almaydı; development'te súwretler media route arqalı berilmeydi.
- Mehmannıń bronlar dizimi bet-betke bólinbegen (iyesi qararı, R14 esabatı).
- Provayderlerdiń bólekshe qaytarıwları tekserilmegen (Payme, Click, Visa).
- Jańa R12 kartaları hám Excel tugmeleri hám VIP badge 390px hám 1440px'te kózge emes, tek testler menen tekserilgen (crawl betlerdi júkleydi hám qátelik tappaydı).

## Tórt valyutadaǵı bahalar (R16, 2026-10-19)

- [ ] **Aldın backup: `migrate`'den aldın `pg_dump -Fc`.** `properties/0016` migration'ı `rate_plan_prices` kestesin qosadı (qosımsha, qaytarıladı).
- [ ] `RATE_PLAN_PRICES_REQUIRED` true (standart): iyeler hár rate plan ushın USD, UZS, KZT hám RUB bahasın kiritiwi kerek, hám eski plan olar kiritilmegenshe ózgertilmeydi. Bar planlar islewin dawam etedi; olardıń basqa valyutaları iyesi kiritkenshe konvertaciya (≈) retinde kórinedi. Iske túsiwden aldın iyelerge aytıń.
- [ ] CBU alıwı endi KZT hám RUB'nı da saqlaydı; birinshi isletiwden keyin `GET /admin-panel/exchange-rates/status/` úsh valyutanıń da taza ekenin kórsetetuǵının tekseriń.
- [ ] Mehmanlar so'mda tóleydi: iyesi so'm bahasın kiritken bolsa, sol dál baha alınadı; basqasha CBU konvertaciyası. Tenge, rubl yamasa dollarda tólew olardı qabıl etetuǵın provayderdi talap etedi (tastıyıqlanbaǵan).

## Naqd bronlar (PLAN_CASH_ONLY 2-basqıshı, 2026-10-22)
- [ ] Aldın backup (`pg_dump -Fc`): `bookings/0012_cash_arrival` migration'ı eki baǵana qosadı hám ele 15 minutlıq aynası ishindegi `pending` bronlardı tastıyıqlaydı.
- [ ] Celery **beat** hám worker isleydi: `bookings.tasks.cancel_unarrived_bookings` hár 10 minutta, mehmanı "arrived" dep belgilenbegen tastıyıqlanǵan bronnı kelip jetiw waqtınan `ARRIVAL_GRACE_HOURS` (standart 2) keyin biykar etedi. Beat bolmasa hesh nárse hesh qashan biykar etilmeydi.
- [ ] Mehmanxanalarǵa Status > arrivals ishinde "Guest arrived" basıwın aytıń; basqasha haqıyqatında kelgen mehmanlar biykar etiledi.
- [ ] `MAX_UPCOMING_BOOKINGS_PER_GUEST` (2, `bookings/views.py`, 2026-10-23 qarar etilgen) hám kesilispew qaǵıydası - bir akkauntnıń tólemey xonalardı alıwına birden-bir tosqınlıq.

- [ ] Docker menen joylastırıw: `.ai/DEPLOY_DOCKER.md`'ni orınlań (compose fayl, avtomat HTTPS penen Caddyfile, hár keshelik `deploy/backup.sh` hám backup'lardı basqa mashinaǵa kóshiriw).

## Sońǵı qosımshalar (2026-11)

- [ ] **Aldın backup: `migrate`'den aldın `pg_dump -Fc`.** 2026-11'de qosılǵan migration'lar: `users/0012` hám `chat/0002` (SMS roziligi hám `SmsDelivery`, qosımsha), `partner/0004`, `promotions/0004`, `properties/0017`, `geography/0005`, `admin_panel/0019` (shahar pogʻonasın alıp taslaw: `geo_cities` kestesi hám `city_ref` baǵanaları óshedi, qaytarıw tek dúzilistı tiklaydı).
- [ ] Geografiya: tek mámleket hám region. Mehmanxanada shahar yamasa tuman maydanı joq (`PLAN_GEO_REMOVE_CITY.md`).
- [ ] SMS: `SMS_ENABLED=False` (standart), `SMS_BACKEND=console`. Haqıyqıy provayder ulanǵanda: `SMS_BACKEND`, token (tek `.env`'de), limitler `SMS_PER_USER_PER_DAY`, `SMS_MIN_GAP_MINUTES`, `SMS_DAILY_LIMIT`. Paydalanıwshı tek profilinde rozilik bergennen keyin SMS aladı.
- [ ] Beat: kúnine bir ret `common.tasks.clear_expired_sessions` (03:30 Asia/Tashkent) ótken kirisiw sessiyaların óshiredi; onsız `django_session` kestesi toqtawsız ósedi.
- [ ] Docker log'lar hár xızmet ushın eń kóp 3 x 10 MB (`docker-compose.yml`).
- [ ] Android hám PWA: `/manifest.webmanifest`, `/sw.js`, `/.well-known/assetlinks.json` óz mazmunın qaytaradı; Play'dan "App signing key" SHA-256 `assetlinks.json`'ge qosıladı (`.ai/ANDROID.md`).
- [ ] Play hám Apple ushın áli kerek: ilovada hesabın óshiriw, maxfiylik siyasatı beti, tekseriwshi ushın demo akkaunt.
