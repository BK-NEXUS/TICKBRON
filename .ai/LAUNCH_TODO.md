# Saytni ochishdan oldin nima qolgan

Holat: kod tayyor (backend 3263 va frontend 2145 test o'tgan, Docker sozlamasi master'da). Sayt hali hech qaysi serverda ishga tushirilmagan.

## 1. Server va domen (egasi + men birga)
- [ ] Domenni ahost.uz'dan olish.
- [ ] Server olish (Linux, Docker o'rnatiladi). Qadamlar: `.ai/DEPLOY_DOCKER.md`.
- [ ] Domenda `@` va `www` uchun A yozuvlari server IP'siga.
- [ ] `.env` to'ldirish (`deploy/docker.env.example` dan), parollarni o'zgartirish. `.env` hech qachon gitga qo'yilmaydi.
- [ ] `docker compose up -d --build`, birinchi administratorni yaratish.
- [ ] Haqiqiy HTTPS sertifikati olinganini tekshirish (hali sinalmagan).
- [ ] Backup'ni (`deploy/backup.sh`) har kun ishlaydigan qilish va bir marta qayta tiklab ko'rish.

## 2. Xat va xabarlar (egasi qaror qiladi)
- [ ] SMTP provayderi: parol tiklash va bron xatlari uchun. Hozir xat ketmaydi.
- [ ] `SUPPORT_NOTIFY_EMAIL`: murojaatlar kimga borishi.
- [ ] Telegram bot (kerak bo'lsa).

## 3. Xarita
- [ ] Sun'iy yo'ldosh qatlami hozir Esri bepul xizmatida ("yengil foydalanish"). Haqiqiy trafikdan oldin kalitli provayder tanlash.

## 4. Biznes va huquq (egasi)
- [ ] Haqiqiy aloqa ma'lumotlari (telefon, manzil, e-pochta).
- [ ] Yurist ko'rigi: foydalanish shartlari, maxfiylik siyosati.
- [ ] Komissiya modeli.
- [ ] To'lov tizimi: bor-yo'qligini va kerakligini aniqlash.

## 5. Matnlar
- [ ] uz va ru matnlarni ona tilida so'zlashuvchi o'qib chiqishi.

## 6. GitHub'da ochiq
- [ ] #106 (QA hisoboti) ni ko'rib chiqish.
- [ ] 10 ta Dependabot PR: qaysilari xavfsiz bo'lsa, men bittaga yig'ib beraman.
- [ ] Ixtiyoriy: CI'da Docker image'larni yig'ish va brauzer testlarini har tunda ishga tushirish.
