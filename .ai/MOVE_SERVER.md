# Loyihanı basqa serverge kóshiriw (MOVE_SERVER)

Maqset: 1-2 saat ishinde, minimal toqtap qalıw (downtime) penen jańa serverge ótiw. Plan: `PLAN_INFRA_SCALE.md` B fazası. Tiykarǵı server qurıw: `DEPLOY_DOCKER.md`.

## Aldın biliw kerek
- Hámme maǵlıwmat 3 jerde: database (`pgdata`), súwretler (`media`) hám **`.env` fayl**. Kod git'te, olardı qayta alıw múmkin.
- `.env` git'te joq. Onıń ishinde `SECRET_KEY` hám **`TWO_FACTOR_KEY`**: sońǵısı joǵalsa, administratorlardıń authenticator sırları ashılmaydı (olar qayta sazlanıwı kerek). `.env` nusqasın backup'tan **bólek, qáwipsiz jerde** (parol menejeri) saqlań.
- HTTPS sertifikatın Caddy jańa serverde ózi aladı (domen jańa IP ge qaratılǵannan keyin).

## Aldınǵı tayarlıq (kóshiriwden 1-2 kún aldın)
1. DNS qatarınıń (A yozuv) **TTL** in 300 sekundqa (5 minut) túsiriń. Sebebi: IP almasqanda jańa adres tez tarqaladı.
2. Jańa serverdi tayarlań: `DEPLOY_DOCKER.md` 1-5 qádemler (Docker, kod, `.env`), lekin sayt házirshe **iske túspesin** (DNS ele eskige qaraydı).
3. `restic` ornatıń hám `deploy/offsite.env` ti kóshiriń (`DEPLOY_DOCKER.md` "Backup'lar").
4. Sınaq: jańa serverde `sh deploy/verify_backup.sh` islewi kerek (nusqalar oqıladı).

## Kóshiriw kúni
1. **Eski serverde** sońǵı nusqa alıń hám sırtqa jiberiń: `sh deploy/backup.sh` ("Offsite copy done" kórinsin).
2. Eski serverde saytti toqtatıń (jańa bronlar kelmesin): `docker compose stop caddy web worker beat`.
3. Toqtatılǵannan keyin yana nusqa alıń: `sh deploy/backup.sh`. Usı nusqada eń jańa maǵlıwmat bar, kóshiriw usı nusqadan boladı.
4. **Jańa serverde** nusqanı tiklań:
   ```
   set -a; . deploy/offsite.env; set +a
   restic restore latest --tag tickbron --target /tmp/restore
   docker compose up -d db redis
   docker compose exec -T db sh -c 'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner' < /tmp/restore/backups/db-YYYYMMDD-HHMMSS.dump
   docker compose up -d web
   docker compose cp /tmp/restore/backups/media-YYYYMMDD-HHMMSS.tar.gz web:/tmp/m.tgz
   docker compose exec -T web tar xzf /tmp/m.tgz -C /app
   rm -rf /tmp/restore
   ```
5. Hámmesin iske túsiriń: `docker compose up -d`. Tekseriw: `/healthz/` hám `/readyz/` 200 qaytarsın, administrator kirisi isleydi, bir bron hám bir súwret kórinedi.
6. DNS ti **jańa IP ge** ózgertiń. 5 minutta jańa serverge ótedi; Caddy sertifikat aladı.
7. Eski serverdi **kamida 1 hápte óshirmeń** (qaytıw ushın). Keyin: nusqa alıp, serverdi óshiriń.
8. DNS TTL ti qayta úlkeytiń (mısalı 3600).

## Qaytıw (kóshiriw sátsiz bolsa)
DNS ti eski IP ge qaytarıń hám eski serverde `docker compose up -d`. Jańa serverde alınǵan bronlar bolsa, olar eski serverde joq: sol sebepli 6-qádemnen keyin bir neshe saat tekserip, tek sonnan keyin eski serverdi toqtatıń.

## Basqa regionǵa yamasa basqa provayderge ótiw
Qádemler birdey: kod Docker'da, sazlama `.env` de. Faqat `DOMAIN` hám sırtqı ombar (S3) mánzili ózgeredi. Jergilikli huqıqıy talap (maǵlıwmat qayerde saqlanıwı) sebepli kóshiriw kerek bolsa, aldın yurist penen kelisiń.

## Belgili sheklewler
- Bir serverde islew: kóshiriw waqtında (3-6 qádemler) sayt 10-30 minutqa toqtaydı. Bul az paydalanıwshı bolatuǵın waqıtta, túnde islewdi usınıs etemiz.
- Úzliksiz arxivlew (WAL) qosılǵanda, usı qollanba jańalanadı (eń sońǵı sekundqa shekem tiklew).
