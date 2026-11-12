# PLAN_INFRA_SCALE: backup, server almastırıw, S3 hám load balancer

Jaǵdayı: **A hám B fazaları TASTIYIQLANǴAN (2026-11-12).** C-F tastıyıq kútedi.
Sána: 2026-11-11. Dálil: `docker-compose.yml`, `deploy/backup.sh`, `deploy/Caddyfile`, `backend/gunicorn.conf.py`, `.ai/PERFORMANCE_REPORT.md`.

## 0. Iyesiniń qararları (2026-11-12)
- Server: **AWS, `eu-central-1` (Frankfurt)**, bir `t3.medium`; load balancer **házir joq**. Jergilikli huqıqıy qarar (maǵlıwmat qayerde saqlanıwı) yurist penen anıqlanadı, kerek bolsa kóshiriledi (B fazası).
- Backup ombarı: AWS S3, **basqa region** (`eu-west-1` yamasa `eu-north-1`), shifrlanǵan, bólek bucket.
- Saqlaw: **14 kún + 8 hápte + 6 ay** (sazlanadı: `KEEP_DAILY`, `KEEP_WEEKLY`, `KEEP_MONTHLY`).
- Qosımsha: kúndelik toliq nusqadan tısqarı **úzliksiz arxivlew** (PostgreSQL WAL, `pgBackRest` yamasa `WAL-G`): hár ózgeris S3 ke barıp turadı, qálegen sekundqa qaytıw múmkin. Bul A2 bólegi, haqıyqıy serverde sınap kórip qosıladı.
- Orınlanıwı: **A1** (kúndelik shifrlanǵan sırtqı nusqa, saqlaw qaǵıydası, Telegram eskertiw, tekseriw skripti) hám **B** (kóshiriw qollanbası) házir; A2 (WAL) serverden keyin.

## 1. Házirgi jaǵday (tekserilgen)

| Zat | Házir |
|---|---|
| Database | `db` konteyner (PostgreSQL 16), `pgdata` diski, bir server ishinde |
| Redis | `redis` konteyner (7), `redisdata`, 512 MB, kesh + throttle + Celery |
| Web | bir `web` konteyner (gunicorn, `WEB_WORKERS=3`, `WEB_THREADS=4`), aldında Caddy |
| Súwretler | server diskinde (`media` volume, `MEDIA_ROOT`); Caddy `/media/*` ni usı diskten beredi |
| Backup | `deploy/backup.sh` bar, **avtomat emes** (`crontab` qoyılmaǵan), usı server ishinde qaladı |
| Load balancer | joq |
| Session | database (default), sol sebepli bir neshe web server menen islewge tayar |

Ayırmashılıq: kod bir serverge baylanıp qalmaǵan, biraq **súwretler diskke** baylanǵan (`storage.path`, `shrink_photos`). Bir neshe server bolsa, súwretler ortaq bolmaydı.

## 2. Maqset

1. Database hám súwretler **hesh qashan joǵalmaydı** (basqa jerge avtomat backup, qayta tiklew tekserilgen).
2. Loyihanı **basqa serverge kóshiriw** 1-2 saat ishinde, qádem-qádem hújjat boyınsha.
3. Paydalanıwshı kóp bolsa, **bólek-bólek úlkeytiw** múmkin (aldın database, keyin web, keyin súwret ombarı).

## 3. Fazalar (hár fazanı bólek PR hám bólek tastıyıq penen)

### Faza A: Backup (eń zárúr, kishi, **birinshi islenedi**)
- `deploy/backup.sh` ke qosımsha: backup'tı **sırtqı jerge** kóshiriw (`rclone` yamasa `restic`, S3-sıyaqlı ombar yamasa basqa mashina). Sırlar `.env` te, kodta emes.
- Shifrlaw: backup fayllar kóshirilmesten aldın shifrlanadı (database'de jeke maǵlıwmat bar).
- `crontab` qatarı hám qadamları `.ai/DEPLOY_DOCKER.md` te; **restore sınaǵı** (basqa bos mashinada tiklep kóriw) shólkemlestirilip, hújjatlanadı.
- Backup sátsiz bolsa, Telegram alert (`common/alerts.py` bar).
- Test: skript testleri (`common/tests/test_backup_script.py` sıyaqlı), tek ǵana ózgergen jerler.
- Retention: 14 kún kúndelik + 8 hápte hápteliq + 6 ay ayliq (tastıyıq kerek).

### Faza B: Kóship júriwge tayarlaw ("bir komanda menen jańa server")
- Hámme sazlama `.env` arqalı: DB host/port, Redis URL, media orni, domen. Házir kópshiligi solay; qalǵanı tekserilip, `deploy/docker.env.example` ke jazıladı.
- `.ai/MOVE_SERVER.md`: kóshiriw ret-retligi: jańa server → Docker → `.env` → `pg_restore` → media tiklew → DNS ózgertiw → `healthz` hám `readyz` tekseriw → eski serverdi toqtatıw. Kútiw waqtı (downtime) minimumǵa.
- DNS TTL aldın kemeytiledi (mısalı 5 minut).
- Test: tolıq restore sınaǵı (Faza A menen birge).

### Faza C: Súwretler ushın object storage (S3-sıyaqlı)
- `django-storages` (+ `boto3`) qosıladı; `STORAGES` `MEDIA_BACKEND=local|s3` env menen tańlanadı (default `local`, sol sebepli házirgi jumıs buzılmaydı).
- Kod ózgeriwi: `storage.path()` ke tayanǵan jerler (`properties/management/commands/shrink_photos.py`, `common/storage.py`) S3 de isleytuǵın etip jazıladı; media URL ortaq (CDN yamasa ombardıń ózi).
- Mavjud súwretlerdi kóshiriw skripti (bir márte, qaytarıp alıw múmkin, aldın backup).
- Caddy `/media/*` lokal diskten ornına ombarǵa jónelte aladı yamasa CDN qoyıladı.
- Qáwipsizlik: ombar **private**, súwretler tek oqıw URL arqalı; kilt'ler tek serverde.
- Provayder tańlaw: Uzbekistan paydalanıwshıları ushın kechikiw (latency) esapqa alınadı. **Iyesi tańlaydı** (mısalı Yevropadaǵı ombar yamasa jergilikli provayder).
- Test: storage backend almastırılǵanda tolıq upload/oqıw testi (mock S3).

### Faza D: Database'ti bólek qılıw
- `DB_HOST` arqalı bólek mashinaǵa yamasa **managed PostgreSQL** ge (avtomat backup hám replika bar) shıǵarıw. Kod ózgermeydi, tek `.env` hám kóshiriw ret-retligi.
- Keyin kerek bolsa: read replica (izlew hám statistika ushın), `pgbouncer` (connection pooling), kerekli index'ler (bul pas bir bólegi islengen).

### Faza E: Load balancer hám bir neshe web server
- **Házir kerek emes.** Bir jaqsı server (4-8 CPU) minlaǵan paydalanıwshını kóteredi, eger N+1, index hám kesh durıs bolsa (bul islengen).
- Kerek bolıw belgileri (load test hám monitoring boyınsha): web CPU turaqlı 70% tan joqarı; p95 jawap waqtı maqsetten asıp ketedi; bir serverdiń RAM tolıp qaladı; serverdi toqtatpay jańalaw kerek.
- Eń arzan jol: **Caddy ózi** bir neshe `web` replika arasında balanslaydı (`reverse_proxy web1:8000 web2:8000`, health check), bir serverde `docker compose up --scale web=3`. Bul CPU ni paydalanadı, biraq server bir bolǵanı ushın server óship qalsa to'xtaydı.
- Real LB: bir neshe server bolǵanda bulut LB (provayder xizmeti) yamasa 2 Caddy/HAProxy + ortaq IP. **Shart:** Faza C (ortaq súwretler) hám Faza D (ortaq database) aldın islengen bolıwı kerek; session hám throttle allaqashan ortaq (database / Redis).
- Celery `worker` hám `beat`: `beat` **tek bir** nusqada isleydi (ekewi bolsa tapsırmalar eki ret isleydi). Hújjatlanadı.

### Faza F: Redis hám monitoring
- Redis'ti bólek mashinaǵa shıǵarıw (Faza D menen birge), parol hám tarmaq cheklewi.
- Monitoring: disk, RAM, CPU, DB ulanıwları, Celery kezegi; alert Telegram arqalı. Uptime tekseriw (`/readyz/`).

## 4. "Paydalanıwshı kóp bolsa" haqqında pikir

- Házirgi dizayn (session + Redis kesh + stateless web) **gorizontal úlkeytiwge tayar**. Ullı muammo web emes, **database** bolıp qaladı (bronlar, inventory qulıplaw `select_for_update`).
- Sol sebepli tártip: backup → database'ti qorǵaw hám úlkeytiw → ortaq súwretler → bir neshe web → LB. Aldınan LB qoyıw payda bermeydi.
- Ullı aksiya (reklama, mawsim) aldınan: `scripts/loadtest` penen sınaw, jetispese web replikasın arttırıw.
- Anıq san (mısalı 100 mıń kúnlik paydalanıwshı) ushın load test nátiyjesi kerek; `PERFORMANCE_REPORT.md` ni jańa serverde qayta ótkiziw usınıladı.

## 5. Qáwipsizlik hám qaǵıydalar
- Sırlar (S3 kilt, backup parolı) tek `.env`/server de, git'te joq; loglarda joq.
- Hár faza: migratsiya joq yamasa qaytarıladı; testler aldın; `master` ge birlestiriwdi iyesi isleydi.
- Kodqa tiyetuǵın fazalar (C) `API_CONTRACT.md` ge media URL qalıbı haqqında jazıladı.

## 6. Iyesinen kerek (qarar)
1. Faza A hám B ni derlew **hám qaysı sırtqı jerge** backup (jergilikli provayder, bulut, ekinshi mashina)?
2. S3 provayderi (Faza C) hám byudjet.
3. Server qayerde turadı (VPS/AWS/óz mashinasi)? Faza D/E sonıń kerekli bolıwı sol arqalı anıqlanadı.
4. Retention (Faza A): 14 kún + 8 hápte + 6 ay maqul ma?

## 7. Usınılatuǵın tártip
A → B (birge, 1-2 PR) → C → D → E, F (kerek bolǵanda). A hám B kodtı derlik ózgertpeydi, qáwipli emes.
