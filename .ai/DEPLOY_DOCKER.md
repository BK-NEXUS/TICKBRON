# TICKBRON'dı Docker menen serverge qoyıw

Bul bir Linux server ushın qádem-qádem nusqaw (iyesiniń óz server'i, jalǵa alınǵan VPS yamasa AWS EC2 mashinası: qádemler birdey). Hár qádemde onıń isleǵenin qalay tekseriw aytılǵan. Fayllar: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `deploy/Caddyfile`, `deploy/docker.env.example`, `deploy/backup.sh`.

## Ne isleydi (What runs)

| Container | Ne isleydi | Internetke ashıq |
|---|---|---|
| `caddy` | Web server: sayt, `/api/`, súwretler; HTTPS sertifikatın ózi aladı | awa, 80 hám 443 portlar |
| `web` | API (Django, gunicorn) | yaq |
| `worker` | Fon tapsırmaları: e-mail'ler, Telegram xabarları, valyuta kursları, ótken sessiyalardı tazalaw | yaq |
| `beat` | Rejelestiriwshi (kúnine eki ret valyuta kursı hám t.b.). Tap bir nusqa, hesh qashan kóbeytpeń | yaq |
| `migrate` | Hár iske túskende bir ret isleydi: jańa database ózgerislerin qollaydı, sonda toqtaydı | yaq |
| `db` | PostgreSQL 16 (maǵlıwmatlar `pgdata` volume'da) | yaq |
| `redis` | Redis (cache, throttle'lar, tapsırma náwbeti; `redisdata` volume) | yaq |

Saqlanıwı shárt maǵlıwmatlar: `pgdata` (database), `media` (júklengen súwretler) hám `caddy_data` (HTTPS sertifikatlar) volume'ları. Container'lardı toqtatıw yamasa qayta qurıw olarǵa tiymeydi; `docker compose down -v` olardı ÓSHIREDI: haqıyqıy server'de hesh qashan jazbań. Hár container'dıń log fayllari eń kóp 3 x 10 MB (`docker-compose.yml`), sonıń ushın disk log'lardan toltpaydı.

## Ne kerek

- Linux server, Ubuntu 22.04 yamasa 24.04, keminde 2 CPU, 4 GB RAM (baslanıw ushın 2 GB da boladı), 40 GB disk hám `sudo` huqıqlı paydalanıwshı.
- Server'ge bağıtlanǵan DNS jazıwlı domen (1-qádem).
- Qálegen mail xızmetinen mail sazlamaları (SMTP host, user, password): parol tiklew hám kirisiw kodları ushın.
- Server'degi kod (3-qádem).

## 1-qádem. Domen (ahost.uz)

Domenniń DNS panelinde eki **A** jazıw qosıń, ekewi de server'diń ashıq IP mánzili menen:
- `@` (taza at `tickbron.com`)
- `www`

Óz kompyuterińizden tekseriń (bir neshe minuttan bir neshe saatqa shekem ketiwi múmkin): `nslookup tickbron.com` server IP'sin kórsetiwi kerek. Buni 5-qádemnen aldın isleń: sertifikat tek at server'ge qarap turǵanda beriledi.

### IPv6 (ıqtıyarıy, keyinirek)

Sayt tek IPv4 penen isleydi, oǵan hár kelushi kire aladı. IPv6 - qosımsha: **AAAA** jazıwdı (`@` hám `www`) server'diń IPv6 mánzili menen **tek** usı tekseriw ótkennen **keyin** qosıń, sebebi Docker kelushiniń haqıyqıy mánzilin óz mánzili artında jasırıwı múmkin:

1. Saytqa tek IPv6 arqalı kiriń (mısalı IPv6 bar kompyuterden `curl -6 https://tickbron.com/healthz/` yamasa onlayn "IPv6 only" tester), AAAA jazıw qoyılǵannan keyin.
2. `docker compose logs caddy | tail`: sol soraw qatarında sizdiń haqıyqıy IPv6 mánzilińiz kóriniwi kerek. Docker mánzili (`172.` yamasa `fd00:`) kórinse, AAAA jazıwdı qaytadan óshiriń: sonda hár IPv6 kelushi limit'lerge hám kirisiw qulıpına bir kelushi bolıp kórinedi.

Ilova óz aldına ne isleydi: IPv6 mánzillerdi saqlaydı hám kórsetedi (audit log, sońǵı kirisiw), hám limit'ler (kirisiw, dizimnen ótiw, anonim API, reklama kóriw sanaw, kirisiw qulıpı) IPv6 kelushini /64 blogı boyınsha sanaydı, sebebi provayder bir baylanısqa pútkil blok beredi hám kelushi blok ishinde mánzilin ózgerte aladı. IPv4 burınǵıday hár mánzil boyınsha sanaladı. Caddy ushın IPv6 sazlaması kerek emes.

## 2-qádem. Server'di tayarlaw

```
sudo apt update && sudo apt -y upgrade
sudo apt -y install ufw git
sudo ufw allow OpenSSH && sudo ufw allow 80/tcp && sudo ufw allow 443 && sudo ufw enable
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER      # bunnan keyin shıǵıp qayta kiriń
docker compose version              # versiya shıǵarıwı kerek
```

Firewall tek SSH, 80 hám 443'ke ruxsat beredi. Database hám Redis server'de ulıwma ashılmaydı.

## 3-qádem. Kodtı alıw

Yamasa `git clone <repository mánzili> tickbron && cd tickbron` (repository jabıq: deploy key yamasa access token paydalanıń), yamasa papkanı kompyuterińizden kóshiriń (`scp`/`rsync`). Tómendegi hámme ámel usı papka ishinde isleydi.

## 4-qádem. Sazlamalardı toltırıw

```
cp deploy/docker.env.example .env
chmod 600 .env
nano .env
```

`CHANGE_ME` jazılǵan hár mánisti, hám `DOMAIN`, `ALLOWED_HOSTS`, `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `DEFAULT_FROM_EMAIL`'di haqıyqıy domenge ózgertiń. Jasırın kilt'ti (secret key) mınaw menen jasań:

```
docker compose run --rm --no-deps web python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

Administratorlardıń eki basqıshlı kirisiw sırların qorǵaytuǵın kilt'ti (`TWO_FACTOR_KEY`) mınaw menen jasań:

```
docker compose run --rm --no-deps web python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Onıń nusqasın database backup'larınan bólek saqlań: onsız ózi qoyılǵan authenticator kodlardı hesh kim paydalana almaydı, al tek database aǵıp ketse, urı oǵan paydalana almaydı. `DEBUG=False` waqtında administratorlar hám staff ushın eki basqıshlı kirisiw májbúriy.

`.env` parollardı saqlaydı: ol git'te joq, chat yamasa e-mail arqalı jibermeń. Ilova náshar yamasa joq sazlama menen iske túspeydi hám qaysısın aytadı (`docker compose logs migrate`).

Sayt SMS jibermeydi: qollap-quwatlaw juwabı paydalanıwshıǵa tek e-mail menen baradı (SMS 2026-11-11 de alıp taslandı).

## 5-qádem. Iske túsiriw

```
docker compose up -d --build
docker compose ps          # hár qatar "Up", db/redis/web "(healthy)"; migrate joq (pitti)
```

Birinshi iske túsiriw image'lerdi qurıp aladı (bir neshe minut). Keyin `https://sizdiń-domen` ashıń: sayt durıs sertifikat penen júklenwi kerek. Bolmasa "Mashqalalar" bólimin qarań.

## 6-qádem. Birinshi administrator

```
docker compose exec -e DJANGO_SUPERUSER_PASSWORD='uzın-parol' web python manage.py createsuperuser --noinput --email siz@sizdiń-domen
```

Keyin mehmanxana túrlerin qosıń (hotel, hostel, guest house, apartment, resort). Jańa server'de olar joq hám iyesi túrsiz mehmanxana qosa almaydı. Qayta isletiw qáwipsiz:

```
docker compose exec web python manage.py seed_property_types
```

`https://sizdiń-domen/login` betinde sol e-mail menen kiriń. Birinshi kirisiw administratordı eki basqıshlı sazlaw betine alıp baradı: telefonǵa authenticator ilovasın ornatıń (Google Authenticator, Microsoft Authenticator, Authy yamasa 2FAS), súwretti skanerleń, 6 xanalı kodtı jazıń hám 10 zapas kodtı qaǵazda saqlań. Mehmanxana iyesiniń akkauntların usı administrator admin panelde jaratadı. Haqıyqıy server'de `seed_demo`'nı ISLETPEŃ (ol development ushın hám DEBUG bolmasa isletpeydi).

## 7-qádem. Maǵlıwmatlardı tayarlaw hám mail'di tekseriw (basqa adam kelmesten aldın)

Jańa server'de valyuta kursı, mail sınawı hám amenity'ler joq. Usılardı bir ret, usı tártipte islań:

1. **Valyuta kursı.** Dollarda bahalanǵan mehmanxanalardı orayılıq bank kursı saqlanǵanǵa shekem bronlaw múmkin emes (kúndelik tapsırma tek Toshkent waqtı menen 09:00 hám 18:00'de isleydi). Server internetke shıǵa alıwı kerek:
   ```
   docker compose exec web python manage.py fetch_exchange_rates
   ```
   Ol `USD: <kurs> UZS for <sana>` dep shıǵaradı. "fetch failed" desse, server `https://cbu.uz`'dı ashıp alatuǵının tekseriń.
2. **Mail.** Mehmanlar hám mehmanxana iyeleriniń dizimnen ótiwi hám kirisiwi mail menen kelgen altı xanalı kodtı talap etedi, hám parol tiklew de sol mail'di talap etedi: mail islemese, hesh kim dizimnen óte almaydı hám kire almaydı. Ózińizge sınaw maili jiberiń:
   ```
   docker compose exec web python manage.py sendtestemail siz@sizdiń-mánzil.com
   ```
   Ol bir minut ishinde kelwi kerek (spam papkasın da qarań). Jeke Gmail account kúnine shama menen 500 mail jiberedi; kúndelik limiti úlken mail xızmetin paydalanıń (Brevo, SendGrid, Mailgun, Amazon SES) hám `.env` ishinde `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` hám `DEFAULT_FROM_EMAIL`'di qoyıń, keyin `docker compose up -d web worker`.
3. **Amenity'ler** (wifi, parking, nashta hám t.b.): administrator retinde kiriń, admin panel, "Amenities" bólimin ashıń hám mehmanxanalar belgilewi múmkin bolǵanların qosıń. Olarsız mehmanxana forması hám izlew filtrinde usınıs etiwge hesh nárse joq.
4. **Bóten adam sıyaqlı sınań**, ekinshi e-mail mánzilińiz menen: saytta dizimnen óting (kod mail menen keledi), shıǵıń, qaytadan kiriń (qaytadan kod), parol tiklewdi sorań. Keyin administrator retinde mehmanxana iyesi akkauntın jaratıń (ol komissiya procentin soraydı), jabıq oynada sol iyesi retinde kiriń, mehmanxana qosıń hám admin panelde tastıyıqlań, hám mehmanlıq akkauntınan bronlań.
5. **Alert'ler** (ıqtıyarıy): `.env` ishindegi `TELEGRAM_BOT_TOKEN` hám `TELEGRAM_ALERT_CHAT_ID` qulıplanǵan akkaunt hám server qátesi alert'lerin Telegram chat'ke jiberedi.
6. **Android hám PWA** (saytıńız ashılǵannan keyin): bul úsh mánzil óz mazmunın kórsetiwi kerek (bas bet HTML'i emes): `https://sizdiń-domen/manifest.webmanifest`, `https://sizdiń-domen/sw.js`, `https://sizdiń-domen/.well-known/assetlinks.json`. Keyin `.ai/ANDROID.md` boyınsha APK'nı telefonda sınań.

## Jańa versiyaǵa jańalaw

```
sh deploy/backup.sh                 # hámme waqıt birinshi
git pull
docker compose up -d --build        # jańa database ózgerislerin `migrate` avtomat qollaydı
docker compose ps
```

## Backup'lar

`sh deploy/backup.sh` database hám súwretlerdi `backups/` ishine jazadı hám 14 kúnnen eski fayllardı óshiredi. Hár keshe isletiń:

```
crontab -e
30 3 * * *  sh /home/<user>/tickbron/deploy/backup.sh >> /home/<user>/backup.log 2>&1
```

Sol server'degi backup server menen birge joǵaladı, sol sebepli skript **sırtqı nusqa** da jiberedi (shifrlanǵan, `restic` penen, AWS S3 ke, server turǵan regionnan basqa regionda):

```
sudo apt install restic
cp deploy/offsite.env.example deploy/offsite.env
chmod 600 deploy/offsite.env
nano deploy/offsite.env            # bucket, RESTIC_PASSWORD, AWS kilt'ler, KEEP_*, Telegram
set -a; . deploy/offsite.env; set +a; restic init      # tek birinshi ret
sh deploy/backup.sh                # sınap kóriw: "Offsite copy done" shıǵıwı kerek
```

- `deploy/offsite.env` git'te joq. `RESTIC_PASSWORD` ti **eki jerde** saqlań (parol menejeri hám qaǵazda): onsız nusqalardı hesh kim tiklep almaydı.
- AWS user tek usı bucket'ke **jazıw** huqıqına iye bolsın (óshiriw huqıqısız); bucket private, versioning yoq.
- Saqlaw: 14 kún + 8 hápte + 6 ay (`KEEP_DAILY`, `KEEP_WEEKLY`, `KEEP_MONTHLY`).
- `deploy/offsite.env` shell retinde isletiledi, sol sebepli skriptler ol tek ózińizge tiyisli hám `chmod 600` bolmasa isleytuǵın emes ("Refused").
- **`.env` nusqaǵa kirmeydi** (ishinde `SECRET_KEY` hám `TWO_FACTOR_KEY` bar). Onsız tiklengen database degi 2FA sırları oqılmaydı: `.env` nusqasın parol menejerinde saqlań (`verify_backup.sh` bunı eske salıp turadı). Server qayta qurılsa birinshi sol nusqa kerek.
- Cron serverdiń waqıt zonasında isleydi: `timedatectl` ti tekserip, bir zonanı (mısalı UTC) qoyıń, bolmasa 03:30 jaz/qıs waqıtı menen jılısıp ketedi.
- Nusqa sátsiz bolsa Telegram'ǵa xabar baradı (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALERT_CHAT_ID`); local nusqa saqlanıp qaladı.
- **Aydıń bir ret tekseriń** nusqa haqıyqattan tiklenetuǵının: `sh deploy/verify_backup.sh` (repository tekseriledi, eń jańa nusqa waqtınsha papkaǵa tiklenedi, súwret arxivi hám database dump oqıladı).
- Jaqın keleshekte: kúndelik toliq nusqadan tısqarı úzliksiz arxivlew (PostgreSQL WAL) qosıladı, `PLAN_INFRA_SCALE.md` A2 bólegi.

### Tiklew (Restore)

```
# database (óziń tańlaǵan fayldan)
docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < backups/db-YYYYMMDD-HHMMSS.dump
# súwretler
docker compose cp backups/media-YYYYMMDD-HHMMSS.tar.gz web:/tmp/m.tgz
docker compose exec -T web tar xzf /tmp/m.tgz -C /app
```

Tiklew usı sazlamanıń test nusqasında sınalǵan (óshirilgen paydalanıwshı qaytıp keldi, óshirilgen súwret qaytıp keldi hám qayta berildi).

## Kóriw

- `docker compose ps`: ne isleydi hám dene-sawlıǵı qanday.
- `docker compose logs -f web` (yamasa `worker`, `beat`, `caddy`, `db`): házir ne bolıp atır; Ctrl+C shıǵadı.
- `curl -s https://sizdiń-domen/api/v1/properties/search/ | head -c 200`: API juwap beredi.

## Mashqalalar (Problems)

- **Sertifikat berilmeydi / brauzer eskertedi**: DNS at server'ge házirge shekem qaramaydı (1-qádem), yamasa 80/443 portlar jabıq (2-qádem). `docker compose logs caddy` qaysısın aytadı. Caddy ózi qayta uriǵadı.
- **`migrate` yamasa `web` iske túskende toqtaydı**: `docker compose logs migrate` qáte yamasa joq sazlamanı ataydı (ilova production sazlamaların tekseredi).
- **400 "DisallowedHost" / API bas tartadı**: `.env` ishindegi `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` yamasa `CORS_ALLOWED_ORIGINS` domenge sáykes kelmeydi (olar domendi dál aladı, sońǵı ekewinde `https://` menen). `.env` ózgergennen keyin: `docker compose up -d`.
- **Sayt qáte mánzilge soraw jiberedi**: API mánzili saytqa qurılǵan. `DOMAIN` ózgergennen keyin `docker compose up -d --build` isletiń.
- **E-mail'ler joq**: `.env` ishindegi SMTP mánisleri; `docker compose logs worker` qátelerdi kórsetedi.
- **Administrator telefonın (hám zapas kodların) joǵaltsa**: basqa super admin admin panelde paydalanıwshılar dizimin ashıp, sol akkauntta "Reset two-step sign-in" basadı (super adminniń óz házirgi kodı kerek). Eger ol sońǵı super admin bolsa, server'de: `docker compose exec web python manage.py reset_2fa olardıń@email`. Akkaunt keyingi kirisiwde qaytadan sazlaydı.
- **Disk tolıp qaldı**: `docker system df`; eski image'ler: `docker image prune`. Haqıyqıy server'de hesh qashan `docker volume prune` jazbań.

## Qáwipsizlik eskertpeleri (Security notes)

- Tek SSH, 80 hám 443 ashıq. SSH key paydalanıń, parol menen kiriwdi óshiriń, server'di jańalap turıń (`sudo apt install unattended-upgrades`).
- `.env` `chmod 600` hám tek server'de. Image'lerde hesh qanday jasırın maǵlıwmat joq (`.dockerignore`).
- Ilova óz container'inde ápiwayı paydalanıwshı retinde isleydi, root retinde emes.
- Bir server - bir ǵana sınıq noqat: joqarıdaǵı backup'lar qaytıwdıń jolı. Eki server yamasa avtomat almasıw ushın basqa sazlama kerek (mısalı Kubernetes yamasa AWS ECS); sol image'lerdi paydalanıw múmkin.

## Aldın kompyuterde sınap kóriw

`.env` ishinde `DOMAIN=localhost`, `ALLOWED_HOSTS=localhost`, úsh https:// mánzilin `https://localhost:8443`, `HTTP_PORT=8080`, `HTTPS_PORT=8443` qoyıń, keyin `docker compose up -d --build` hám `https://localhost:8443` ashıń (brauzer local sertifikat haqqında eskertedi: bul jerde tek sol kútiledi).

## Belgili sheklewler (Known limits)

- Log fayllar (`security.log`, `error.log`, ...) `applogs` volume inde (`/app/logs`): konteyner qayta jaratılsa joǵalmaydı. Olar `docker compose cp` yamasa `docker compose exec web tail /app/logs/security.log` arqalı oqıladı. Volume backup qa kirmeydi; kerek bolsa qosıń.
- Caddy aldındaǵı sheklew: `NUM_PROXIES=1` (Caddy ǵana). Eger Caddy aldına CDN (Cloudflare t.b.) qoyılsa, Caddy tek CDN mánzilin kóredi, barlıq kelwshiler bir rate-limit "shelegine" túsedi. Aldın `NUM_PROXIES=2` hám Caddy da CDN dıń IP diapazonına isenim (`trusted_proxies`) sazlań, sonnan keyin ǵana CDN qosıń.
- `dump.rdb` (Redis, kishi mazmun: keshlengen betler, throttle sanawıshları) erte git tariyxında bar edi, endi `.gitignore` da. Tariyxtı qayta jazıw (qáwipli, hámme klon buzıladı) **islenbedi**: ienesi sheshedi. Ishinde parol yamasa token joq dep esaplanadı; gúmán bolsa sol waqıttaǵı `SECRET_KEY` hám Redis parolin almastırıń.
- Celery worker procesleri sanı `CELERY_CONCURRENCY` (ádetde 2); migratsiya kestede 10 s dan artıq kútse qátelik penen toqtaydı (`lock_timeout`), gunicorn access log da haqıyqıy kelwshi IP si (`X-Forwarded-For`) jazıladı.

- Haqıyqıy domenli haqıyqıy server'de házirge shekem isletilmegen: joqarıdaǵı hámmesi test ortalıǵında isletilgen (hámme container'ler, API, ólshem limitleri, header'ler, backup hám tiklew), biraq haqıyqıy sertifikat hám haqıyqıy mail emes.
- Sun'iy joldas súwretleri haqıyqıy trafikten aldın kilt'li provayderdi talap etedi (`.ai/RELEASE_CHECKLIST.md`).
- Fayllar AWS'te de birdey: EC2 mashinası hám joqarıdaǵı qádemler. Súwretler S3'te hám database RDS'te bolıwı ushın (kóbirek qáwipsizlik, kóbirek xarejet) sazlamalar (`STORAGE_TYPE`, `DB_HOST`) bar, biraq ol variant qurılmaǵan hám sınalmaǵan.
