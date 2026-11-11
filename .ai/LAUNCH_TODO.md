# Saytti iske túsiriwden aldın ne qaldı (2026-11-11 jańalandı)

Jaǵday: kod tayar (backend 4114 hám frontend 2520 test ótken, Docker sazlaması master'de, Android APK tayar). Sayt ele hesh qaysı server'de iske túsirilmegen.

## 1. Server hám domen (iyesi + biz birge)
- [x] Domen `tickbron.com` satıp alındı.
- [ ] Server alıw (Linux, Docker ornatıladı). Qádemler: `.ai/DEPLOY_DOCKER.md`.
- [ ] Domende `@` hám `www` ushın A jazıwları server IP'sine.
- [ ] `.env` toltırıw (`deploy/docker.env.example`'den), parollardı ózgertiw. `.env` hesh qashan git'ke qoyılmaydı.
- [ ] `docker compose up -d --build`, birinshi administratordı jaratıw.
- [ ] Haqıyqıy HTTPS sertifikat alınǵanın tekseriw (ele sınalmaǵan).
- [ ] Backup'tı (`deploy/backup.sh`) hár kún isleytuǵın etiw hám bir ret qayta tiklap kóriw.
- [ ] `TWO_FACTOR_KEY` nusqasın database backup'tan bólek saqlaw.

## 2. Xat hám xabarlar (iyesi qarar etedi)
- [ ] SMTP provayder (Brevo): parol tiklew, kirisiw kodları hám bron xatları ushın. Mail islemese hesh kim dizimnen óte almaydı. `no-reply@tickbron.com` jiberiwshisin hám domendi tastıyıqlaw (DNS jazıwları).
- [ ] `SUPPORT_NOTIFY_EMAIL`: murojaatlar kimge baradı.
- [ ] Telegram bot (kerek bolsa).
- [ ] SMS provayder (Eskiz.uz yamasa basqa): akkaunt, token, jiberiwshi atı. Tayar bolǵanda `SMS_ENABLED=true` (`.ai/PLAN_SMS_CHAT.md`).

## 3. Mobil ilovalar
- [x] Android qabıqshası (TWA) hám APK/AAB tayar (`D:\TICKBRON-ANDROID`); sayt ornatılatuǵın (PWA) etildi.
- [ ] Server'den keyin APK'nı telefonda sınaw (`.ai/ANDROID.md`).
- [ ] Google Play Console: ilova jaratıw, `.aab` júklew, "App signing key" SHA-256'nı `frontend/public/.well-known/assetlinks.json`'ge qosıw.
- [ ] Play hám Apple ushın májbúriy: hesabın óshiriw funksiyası, maxfiylik siyasatı beti, "Data safety" forması, tekseriwshi ushın demo akkaunt.
- [ ] iOS ilova (Mac yamasa bulıtlı Mac, Apple Developer akkaunt, $99/jıl).

## 4. Karta
- [ ] Sun'iy joldas qatlamı házir Esri biypul xızmetinde ("jeńil paydalanıw"). Haqıyqıy trafikten aldın kilt'li provayder tańlaw.

## 5. Biznes hám huqıq (iyesi)
- [ ] Haqıyqıy baylanıs maǵlıwmatları (telefon, mánzil, e-pochta).
- [ ] Yurist kóriwi: paydalanıw shártleri, maxfiylik siyasatı.
- [ ] Komissiya modeli.
- [ ] Buyırtpashı menen jazba kelisim (narx, tólem tártibi, koddıń huqıqı, qollap-quwatlaw).

## 6. Tekstler
- [ ] uz, ru hám qaraqalpaq tekstlerdi ana tilinde sóylewshiniń oqıp shıǵıwı (bul hújjetlerdiń qaraqalpaqshası da).

## 7. GitHub'te ashıq
- [ ] Dependabot PR'lar: qaysısı qáwipsiz bolsa, birewge jıynap beriw.
- [ ] Iqtıyarıy: CI'de Docker image'lerdi qurıw hám brauzer testlerin hár keshe isletiw.
