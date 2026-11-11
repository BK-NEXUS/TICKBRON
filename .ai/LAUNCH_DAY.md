# TICKBRON iske túsiw kúni (2026-11-11 jańalandı: mehmanxanada naqd tólem, Android hám PWA, shaharsız geografiya)

Mehmanlar mehmanxanada naqd tóleydi; platforma pul júrgizbeydi (`PLAN_CASH_ONLY.md`). Tómendegi dizim tek kod isley almaytuǵın nárselerdi qamtıydı: iyesi qararları, akkauntlar, server'ler. Tolıq maǵlıwmatlar hám dál ózgeriwshi atları: `RELEASE_CHECKLIST.md` ("Production settings", "Prices in four currencies").

## 0. Kod jaǵdayı
Hámmesi master'ge birlestirilgen: input qaǵıydaları, telefon nomeri, naqd bronlar, onlayn tólem joq (#72), iyeniń súwretleri (#64), mámleket/region súwretleri hám iyeniń akkaunt orni (#67), tórt valyutalı bahalar (#61), Android ushın ornatılatuǵın sayt (PWA, #177), SMS tiykarı (`SMS_ENABLED=False`, provayder joq), ótken sessiyalardı tazalaw hám Docker log'lardı shekewlew. Geografiyada tek mámleket hám region qaldı (shahar daǵa tuman pogʻonası alıp taslandı, `PLAN_GEO_REMOVE_CITY.md`). Tek Dependabot PR'ları ashıq. Tómendegi smoke test'ti branch'te emes, joylastırılǵan build'te isleń.

## 1. Iyesi usınıwı kerek
- Hosting: server, domen (`tickbron.com` satıp alınǵan), TLS sertifikat, Caddy yamasa nginx (`NUM_PROXIES`, `USE_X_FORWARDED_PROTO`), Postgres, Redis, Celery worker HAM beat.
- E-mail SMTP (`EMAIL_*`, `FRONTEND_URL`): parol tiklew hám kirisiw kodları ushın (mail islemese, hesh kim dizimnen óte almaydı). Telegram bot token + chat id alert'ler ushın.
- SMS provayder (Eskiz.uz, Play Mobile yamasa basqa): akkaunt, token, tastıyıqlanǵan jiberiwshi atı. Bul bolmaǵansha SMS isleymeydi.
- Qararlar: mehmanlar mehmanxanada naqd tólegeni ushın komissiya qalay alınadı; logo fayllar.
- Tekseriwler: yurist (kelip jetiw qaǵıydası ("sol waqıtta kelmeseńiz taǵı 2 saat kútemiz, sonda bron biykar etiledi"), "Reklama", paydalanıw shártleri, maxfiylik siyasatı); barlıq uz/ru/qaraqalpaq tekstler boyınsha ana tilinde sóylewshi.
- 2026-10-23 qarar etildi: mehmanda eń kóp 2 kelesi bron boladı hám olardıń sanaları hesh qashan kesilispeydi; mehmanxana bugin hám erteńgi kelip jetiw dizimin tolıq telefon menen kóredi (`bookings/views.py` ishindegi `MAX_UPCOMING_BOOKINGS_PER_GUEST`).

## 2. Joylastırıw tártibi (hár qádemniń qaytıw jolı bar)
1. `pg_dump -Fc` backup, server'den tısqarıda saqlanadı (tómendegi jańa migration'lar).
2. Production `.env`: Docker jolı ushın `deploy/docker.env.example`'di `.env`'ge kóshiriń (`.ai/DEPLOY_DOCKER.md`); Docker'siz jol ushın `deploy/env.production.example`'di `backend/.env`'ge hám `deploy/frontend.env.production.example`'di `frontend/.env.production`'ge kóshiriń; hár `CHANGE_ME`'di almastırıń. Domen ahost.uz'da: A jazıwın (hám `www`) server'ge qaratıń, keyin `tickbron.com` hám `www.tickbron.com` ushın TLS sertifikat alıń (www taza atqa jiberiledi). `DEBUG=False`. Tólem sazlamaları joq. `ARRIVAL_GRACE_HOURS` standart 2.
3. Turaqlı `MEDIA_ROOT` hám `/media/` (iyeniń súwretleri, mámleket hám region súwretleri; checklist "safe `/media/` serving").
4. `python manage.py migrate` (jańalar: `bookings/0012_cash_arrival`, `geography/0004`, `0005`, `partner/0002`, `0004`, `properties/0016`, `0017`, `promotions/0004`, `users/0012`, `chat/0002`), keyin `python manage.py check --deploy` ("no issues" shıǵarıwı kerek).
5. `python manage.py fetch_exchange_rates` (USD, KZT, RUB cbu.uz'den); beat onı 09:00 hám 18:00'de isletetuǵının tekseriń. Beat kelip jetiwdi tekseriwdi hár 10 minutta (`cancel_unarrived_bookings`) hám ótken sessiyalardı tazalawdı kúnine bir ret isleytuǵının da tekseriń: beat bolmasa kelmegen mehmanlar hesh qashan biykar etilmeydi.
6. Super-admin jaratıń; `seed_demo*`'nı ISLETPEŃ; database development'ten kelgen bolsa `*@tickbron.demo` qatarların óshiriń.
7. Iyeler hár rate plan ushın tórt bahanı (UZS, USD, KZT, RUB) kiritedi (májbúriy, `RATE_PLAN_PRICES_REQUIRED=true`). Super admin mehmanxana iyesi akkauntların telefon hám orın (mámleket, region) menen jaratadı.
8. Jonli saytta qolda smoke test: telefon nomeri menen dizimnen ótiw, izlew, bronlaw (kelip jetiw waqtı), tastıyıqlanǵan bet, biykar etiw (biypul), iyeniń kelip jetiw dizimi hám "Guest arrived", admin Status (kirim = tamamlanǵan bronlar), iyeniń súwret júklewi.
9. Android: `.ai/ANDROID.md` boyınsha APK'nı telefonda sınań, keyin Google Play Console'ǵa júkleń.

## 3. Mehmanxanalarǵa aytıń
- Kelgen hár mehmanǵa kelip jetiw dizimde "Guest arrived" basıń. Belgilenbegen tastıyıqlanǵan bron mehmannıń aytqan kelip jetiw waqtınan 2 saat keyin biykar etiledi hám xona bosaydı.
- Biykar etiw mehmanǵa jasaw baslanıwınan aldın hár waqıt biypul; onlayn hesh nárse alınbaydı yamasa qaytarılmaydı.

## 4. Belgili, biraq túzetilmegen (hesh biri iske túsiwge tosqınlıq emes)
Mehmanxana iyeleri mehmanxana jaratılǵannan keyin onıń atın ózgerte almaydı; mehmannıń bronlar dizimi bet-betke bólinbegen; tólem kestelari hám `PaymentAuditLog` tariyx retinde database'de qaladı (bron jaǵday tariyxı sonda jazıladı); hesabın óshiriw funksiyası joq (Apple hám Google talap etedi); professional penetration test ele ótkizilmegen; Redis nátiyje cache hám thumbnail'ler ataylap taslanǵan (R14: 200 paydalanıwshı, 0 qátelik, izlew p95 163 ms).

Sońǵı tolıq isletiwler (2026-11-11, shaharsız geografiyadan keyin): backend 4114 test ótti (Windows'qa baylanıslı 3 test qulaydı), frontend 2520 test ótti.
