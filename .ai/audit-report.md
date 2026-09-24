# Backend xavfsizlik va bug auditi

- Audit sanasi: 2026-09-23
- Qamrov: `backend/` (Django + DRF), faqat kod o'qish va izolyatsiyalangan in-memory bazada tekshiruv
- Belgilar: ✅ = skript bilan tasdiqlangan, belgisiz = kodni o'qib topilgan
- Fayl/qator havolalari audit paytidagi holatga tegishli; keyingi tuzatishlardan so'ng siljigan bo'lishi mumkin

## Holat jadvali

| # | Topilma | Jiddiylik | Holat |
|---|---|---|---|
| 1 | OTP kodi API javobida (SMS_TEST_MODE sukut bo'yicha True) | Kritik | ✅ Tuzatildi — `d6ff853` |
| 2 | Mehmon bronni PATCH/PUT bilan o'zgartira oladi | Kritik | ✅ Tuzatildi — `10f9f39` |
| 3 | Mehmon bronni DELETE bilan o'chiradi, inventar qaytmaydi | Kritik | ✅ Tuzatildi — `10f9f39` |
| 4 | To'lovni klient bepul tasdiqlaydi (/confirm/, PAYMENT_TEST_MODE) | Kritik | ✅ Tuzatildi — `d6ff853`, `4e20acf` (confirm faqat PAYMENT_TEST_MODE + DEBUG) |
| 5 | Webhook'lar ishlamaydi (auth talab qilinadi, holat yangilanmaydi) | Kritik | ✅ Tuzatildi — `0def054` (status mapping mock formatda, haqiqiy integratsiyada moslash kerak) |
| 6 | Webhook event imzodan oldin yoziladi — haqiqiy event bloklanadi | Kritik | ✅ Tuzatildi — `4843b9c` (+ secret bo'sh bo'lsa fail closed) |
| 7 | number_of_rooms: 1 xona narxi/inventari, bekor qilishda N | Kritik | ✅ Tuzatildi — `7be6a8d` |
| 8 | phone_number unikal emas | Yuqori | ✅ Tuzatildi — `f050dcd` |
| 9 | OTP brute-force (throttle yo'q, random, lock tekshiruvi keyin) | Yuqori | ✅ Tuzatildi — `73b0247` |
| 10 | X-Forwarded-For orqali throttle chetlab o'tiladi, LocMem cache | Yuqori | ✅ Tuzatildi — `9f0601d` (NUM_PROXIES deploy'ga qarab sozlanishi kerak) |
| 11 | Akkaunt bloklash DoS, user enumeration | Yuqori | ✅ Tuzatildi — `d51bd96` (login va OTP; `register` hali email/telefon mavjudligini oshkor qiladi) |
| 12 | Partner mulk statusini o'zi `active` qiladi | Yuqori | ✅ Tuzatildi — `6506d30` |
| 13 | Suspended/rejected mulk bronlanadi va ommaga ko'rinadi | Yuqori | ✅ Tuzatildi — `758a4bc` |
| 14 | Har qanday foydalanuvchi barcha webhook event'larini ko'radi | Yuqori | ✅ Tuzatildi — `23cb13d` |
| 15 | Refund: mehmon o'zi qiladi, mantiq teskari, summa tekshirilmaydi | Yuqori | ✅ Tuzatildi — `40558e8` (admin "bekor qilish + refund" amali hali yo'q) |
| 16 | Begona bronga to'lov tranzaksiyasi; tranzaksiya PATCH/DELETE ochiq | Yuqori | ✅ Tuzatildi — `0dce737` |
| 17 | Muddati o'tgan bronlar avtomatik bekor qilinmaydi (Celery yo'q) | Yuqori | ✅ Tuzatildi — `4fe3296` (beat jonli sinalmagan: lokal Redis yo'q) |
| 18 | Race condition: cancel/expire/confirm bron qatorini qulflamaydi | Yuqori | ✅ Tuzatildi — `94f96c6` (PostgreSQL parallel testlari bilan) |
| 19 | O'tgan sanaga bron, guest_count/xona tekshiruvi, narx yozuvi | O'rta | ✅ Tuzatildi — `a48c00e` |
| 20 | Bronsiz sharh; sharhda booking/property almashtirish | O'rta | ✅ Tuzatildi — `68ec591` (+ eligible_properties har bir bron alohida) |
| 21 | Admin RBAC ishlatilmaydi, audit log yo'q, InternalNote author yoziladi | O'rta | Qisman — InternalNote author read-only (`6b732ac`); RBAC, audit log va staff'ning begona sharhni PATCH qilishi ochiq |
| 22 | Mijozlar ro'yxati xotirada saralanadi, aggregat join xatosi | O'rta | ✅ Tuzatildi — `f55ff3e` |
| 23 | Rasm yuklash validatsiyasi DRF orqali chaqirilmaydi | O'rta | Ochiq |
| 24 | Ichki xatolar (`str(e)`) klientga, OTP va email loglarda | O'rta | Qisman — OTP kodi logdan olib tashlandi (`73b0247`), qolgani ochiq |
| 25 | SESSION/CSRF cookie secure sukut bo'yicha False | O'rta | ✅ Tuzatildi — `50a8a26` |
| 26 | Partner bronlar ro'yxati 500 (`booking.guest_name`) | Kichik | Ochiq |
| 27 | Sevimlini o'chirib qayta qo'shish 500 | Kichik | Ochiq |
| 28 | Noto'g'ri query parametrlarida 500 | Kichik | Ochiq |
| 29 | `process_expired_bookings` xatolarni yutadi | Kichik | ✅ Tuzatildi — `c07f409` |
| 30 | `conftest.py` testlarni sozlangan (dev) bazada ishlatadi | Kichik | ✅ Tuzatildi — `c98a48f` |
| 31 | Inventar rate_plan bo'yicha, room_type bo'yicha emas | Kichik | Ochiq — yechim variantlari quyida, tuzatilmagan |
| 32 | To'lov idempotency ishlamaydi (auditdan keyin topildi) | Yuqori | ✅ Tuzatildi — `0dce737` |

## Topilmalar tafsiloti

### 🔴 Kritik

**#1 OTP kodi javobda — akkaunt egallash.** `SMS_TEST_MODE` sukut bo'yicha `True` edi (`config/settings.py:287`); test rejimida `otp/request/` kodni javobda qaytaradi (`users/services.py:78`). Telefon raqamini bilish kifoya edi.
*Tuzatish:* sukut `False`, provayder yo'q bo'lsa 503.

**#2 Bronni PATCH bilan o'zgartirish.** `BookingViewSet` to'liq `ModelViewSet`, `BookingSerializer` da `status`, `payment_status`, `total_price`, `guest`, `property` yoziladigan edi. ✅ `PATCH` bilan bron `confirmed/paid/0.01` bo'ldi.
*Tuzatish:* faqat create/list/retrieve, serializer to'liq read-only.

**#3 Bronni DELETE bilan o'chirish.** Hard delete, inventar qaytarilmaydi. ✅
*Tuzatish:* DELETE 405.

**#4 To'lov bepul tasdiqlanadi.** `PAYMENT_TEST_MODE` sukut `True` edi (`settings.py:275`); klient `/transactions/{id}/confirm/` ni o'zi chaqiradi va bron pulsiz `confirmed` bo'ladi. Test rejimi o'chsa adapterlar `NotImplementedError` → 500 (haqiqiy integratsiya yo'q).

**#5 Webhook'lar ishlamaydi.** `webhook_endpoint` da `AllowAny` yo'q → provayder 403 oladi (✅). `WebhookProcessor` to'lov yoki bron holatini yangilamaydi (`payments/webhooks.py:95-107`).

**#6 Replay himoyasi teskari.** `WebhookEvent` imzo tekshirilishidan oldin yoziladi (`webhooks.py:58-69`) va `(provider, provider_event_id)` unikal. Soxta imzo bilan yuborilgan `id` keyingi haqiqiy webhook'ni "Replay attack" qilib rad ettiradi. ✅

**#7 Bir nechta xona.** `number_of_rooms=3` bo'lsa ham 1 xona narxi va 1 inventar (`bookings/models.py:307, 348`); bekor qilishda 3 ayriladi (`:399, :455`) → 500 yoki boshqa bronlar inventari buziladi. ✅

### 🟠 Yuqori

**#8 phone_number unikal emas.** Hujumchi profiliga qurbon raqamini yozib, uning OTP loginini buzardi (`get() returned more than one User`). ✅
*Tuzatish:* unikal + migratsiya 0006 (takrorlarda to'xtaydi), raqam o'zgarsa `phone_verified` tushadi.

**#9 OTP brute-force.** `verify_otp` da throttle yo'q; yangi kod urinishlarni nollardi; throttle kaliti xom satr; `random` ishlatilgan; bloklangan akkauntda kod tekshirilib, to'g'ri kod 403 bilan oshkor bo'lardi.
*Tuzatish:* `secrets`, constant-time solishtirish, lock oldin tekshiriladi, verify 5/min, kalit normallashtirilgan.

**#10 Throttle chetlab o'tish.** DRF `NUM_PROXIES` yo'q → `X-Forwarded-For` ni almashtirib login/register/search throttle'lari chetlab o'tiladi; `CACHES` yo'q (LocMem, har worker alohida); `get_client_ip` XFF'ga ishonadi.

**#11 Bloklash DoS, enumeration.** 5 ta xato istalgan akkauntni 30 daqiqaga bloklaydi; login 403/401 farqi va OTP "User not found" foydalanuvchi mavjudligini oshkor qiladi.

**#12 Partner moderatsiyani chetlab o'tadi.** `PartnerPropertySerializer` da `status` yoziladi. ✅

**#13 Faol bo'lmagan mulk.** Bron yaratish va `property_detail` `status='active'` ni tekshirmaydi. ✅

**#14 Webhook event'lari hammaga ochiq.** `WebhookEventViewSet` faqat `IsAuthenticated`; payload va PII ko'rinadi. ✅

**#15 Refund.** Mehmon istalgan vaqtda, istalgan summaga refund qiladi; summa berilmasa `partially_refunded` yoziladi (teskari, `payments/views.py:259`); summa tekshirilmaydi. ✅
> **Eslatma:** refund bronni avtomatik bekor qilmaydi (qaror: to'lov holati va bron holati alohida). Buning uchun **admin uchun "bekor qilish + refund" amali kerak** — hozircha mavjud emas, alohida ish sifatida qilinishi kerak.

**#16 Tranzaksiya egaligi.** `PaymentTransactionCreateSerializer` bron egasini tekshirmaydi (✅ begona bronga tranzaksiya yaratildi); tranzaksiya `PATCH`/`DELETE` ochiq (audit izi buziladi); javobda `payment_method_token`; `client_ip`/`user_agent` klientdan olinadi.

**#17 Muddati o'tgan bronlar.** Celery task yoki beat jadvali yo'q; pending bronlar inventarni cheksiz ushlaydi; to'lov boshlashda `expires_at` tekshirilmaydi.

**#18 Race condition.** `cancel_booking`, `expire_booking`, `confirm_booking` holatni bron qatorini qulflamasdan tekshiradi; `confirm` view'da `transaction.atomic` yo'q.

**#32 Idempotency ishlamaydi** (auditdan keyin topildi). `PaymentTransactionViewSet.create` mavjud kalitni qidirishdan oldin `is_valid` chaqiradi; `idempotency_key` modelda unikal bo'lgani uchun `UniqueValidator` o'sha foydalanuvchining qayta so'rovini ham 400 bilan rad etadi — "mavjud tranzaksiyani qaytarish" kodi hech qachon ishlamaydi.

### 🟡 O'rta

**#19** O'tgan sanaga bron qabul qilinadi ✅; `guest_count` xonalar soniga nisbatan tekshirilmaydi; `BookingItem.price_per_night` inventar narxini emas `base_price` ni yozadi.

**#20** Bronsiz sharh qabul qilinadi ✅ (`accounts/serializers.py:100`); `PATCH` bilan `booking`/`property` almashtiriladi; tasdiqlangan sharh tahrirlanganda `approved` qoladi.
*Tuzatish (`68ec591`):* `booking` majburiy — o'zining `completed` broni bo'lishi va `property` shu bronning mulki bo'lishi kerak. Bir bronga bitta sharh: takroriy so'rov 500 o'rniga 400 qaytaradi, o'chirilgan sharh ham hisobga olinadi. `booking`/`property` PATCH/PUT'da read-only. Har qanday tahrir sharhni `pending` ga qaytaradi (`reviewed_at=null`), shuning uchun u `property_scores` dan chiqadi. `eligible_properties` endi sharhsiz har bir tugallangan bronni `booking_id` bilan alohida ko'rsatadi; oldin bir mulkka sharh yozilsa, o'sha mulkdagi hamma bronlar yashirinardi. Migratsiya yo'q: `booking` ustuni nullable qoldi (eski bronsiz sharhlar bo'lishi mumkin), qoida serializer'da. Kontrakt: `contracts/booking.md` "Reviews", `API_CONTRACT.md`, `HANDOFF.md`.

**#21** `Role`/`Permission` modellari ishlatilmaydi — har qanday `is_staff` hamma narsaga kiradi; admin amallari audit log'ga yozilmaydi; `InternalNote` da `author`/`customer` yoziladi.
*Qisman tuzatildi:* `customer` URL'dan olinadi (`e961b9a`), `author` read-only (`6b732ac`).
*Ochiq:*
- RBAC.
- Admin audit log.
- Staff boshqa foydalanuvchining sharhini `PATCH /api/v1/me/reviews/{id}/` bilan tahrirlay oladi (`ReviewViewSet.get_queryset` staff'ga hamma sharhlarni beradi). Matn o'zgarsa sharh `pending` ga qaytadi (#20), lekin muallif nomidan yozilgan matn qoladi. Moderatsiya uchun alohida admin amali kerak, staff esa `/me/reviews/` orqali faqat o'z sharhini tahrirlashi kerak — RBAC bilan birga hal qilinadi.

**#22** Mijozlar ro'yxati barcha foydalanuvchilarni xotiraga yuklab saralaydi; `Count('bookings')` + `Sum(payment_transactions)` join sonlarni ko'paytirishi mumkin; staff ham ro'yxatda.
*Tuzatish (`f55ff3e`):* staff va super-admin ro'yxatga kirmaydi. Aggregatlar correlated subquery bilan hisoblanadi: oldin bir nechta to'lovi bor bron to'lovlar soni marta sanalardi (✅ 2 bron → 4). `customer_status` va ko'rsatiladigan ism annotate qilinadi, saralash va sahifalash DB'da (`LIMIT/OFFSET`). Bo'sh `last_booking_date` ikkala yo'nalishda ham oxirida; `full_name` registrdan qat'i nazar saralanadi.

**#23** Rasm hajmi/kengaytma tekshiruvi `model.clean()` da — DRF uni chaqirmaydi.

**#24** `str(e)` klientga qaytadi (bron yaratish/bekor qilish — ✅ SQL CHECK matni ko'rindi, OTP, search suggestions, webhook); OTP kodlari (tuzatildi) va har so'rovda foydalanuvchi email'i loglarga yoziladi (ochiq).

**#25** `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` sukut `False`.
*Tuzatish (`50a8a26`):* sukut qiymati `not DEBUG` (production'da `True`, lokal http'da `False`), env bilan o'zgartirish mumkin. `.env.example` ularni endi `False` ga qo'ymaydi.

### 🟢 Kichik

**#26** Partner bronlar ro'yxati har doim 500: `booking.guest_name` yo'q (`partner/views.py:204`). ✅

**#27** Sevimlini o'chirib qayta qo'shish 500 (soft delete + `unique_together`). ✅

**#28** `history/recent?limit=abc`, `reviews/property_scores?property_id=abc` → 500.

**#29** `process_expired_bookings` xatolarni jimgina yutadi (`bookings/models.py:490`).

**#30** `conftest.py` `django_db_setup` ni no-op bilan almashtirgan edi → testlar sozlangan bazada ishlardi.
*Tuzatish:* override olib tashlandi, testlar alohida test bazasida.

**#31** Inventar `rate_plan` bo'yicha yuritiladi — bitta xona turining ikki tarifi bitta jismoniy xonani ikki marta sotishi mumkin.

> **#31 yechim variantlari** (hali tuzatilmagan):
> - **A. Inventarni `room_type + date` ga ko'chirish,** narx esa `rate_plan + date` da qoladi. Bitta xona to'plami bitta joyda hisoblanadi, bu to'g'ri model. Lekin ma'lumot migratsiyasi (tariflar bo'yicha inventarni birlashtirish), partner inventory API va frontend o'zgarishi kerak. Eng katta ish.
> - **B. Sxemani o'zgartirmay, bron vaqtida umumiy bandlikni tekshirish:** har bir sana uchun xona turining barcha tariflari bo'yicha `sum(booked_rooms) + yangi xonalar ≤ room_type.total_rooms`. Tez qilinadi, lekin barcha tariflarning inventar qatorlarini qulflash kerak, `available_rooms` esa chalkash ma'noda qoladi (tarif limiti va jismoniy limit aralashadi).
> - **C. Bitta xona turiga faqat bitta inventarli tarif,** qolgan tariflar narx modifikatori bo'ladi. Oddiy, lekin mahsulot imkoniyatini cheklaydi.
>
> Tavsiya: **A**, alohida checkpoint sifatida, Baxram bilan (partner va frontend ta'siri) kelishilgan holda. Tezkor vaqtinchalik himoya kerak bo'lsa, B.

## Boshqa kuzatuvlar

- Test to'plami endi PostgreSQL'da ishlaydi (`82d9cb3`; SQLite faqat `ALLOW_SQLITE_TESTS=1` bilan). Bron kodi fixture'lari (`d2bc3b5`) va admin test yo'llari (`76c8044`) tuzatilgach: 790 passed, 5 failed. Qolgan 5 ta `admin_panel` xatosi: (1) InternalNote yaratish 400 — serializer body'da `customer` ni talab qiladi, view uni URL'dan oladi (**kod xatosi**, 2 test); (2) booking lookup testi mavjud bo'lmagan `Property.name` ga murojaat qiladi (test eskirgan); (3) mijozlar ro'yxati testi `total_amount_paid` ni Decimal kutadi, API string qaytaradi (test eskirgan); (4) mijoz tafsilotida izohlar tartibi testi — `created_at` bo'yicha tartibga tayanadi (test yoki tartib aniqlanishi kerak).
- `admin_panel` index nomlari migratsiyasi yetishmasdi — `7f589d1` da qo'shildi.
- To'lov qismidagi tuzatishlardan keyin (`0dce737`..`40558e8`):
  - Provayder pulni olgan-u, bron allaqachon bekor qilingan bo'lsa, tranzaksiya `completed` bo'ladi, bron o'zgarmaydi va audit log'da "manual refund required" belgisi qo'yiladi — admin refund qilishi kerak.
  - `.ai/contracts/payments.md` webhook yo'lini `webhooks/{provider}/` deb ko'rsatardi; haqiqiy yo'l `webhook/{provider}/` — kontrakt tuzatildi.
  - Haqiqiy Payme/Click/Visa integratsiyasi hali yo'q: test rejimi o'chiq bo'lsa to'lov yaratish 503 qaytaradi.
- Bron mantiqi tuzatishlaridan keyin (`c07f409`..`4fe3296`):
  - `BookingItem.price_per_night` endi bir xonaning o'rtacha kechalik narxi (inventar narxlari kechama-kecha farq qilishi mumkin).
  - O'tgan sana faqat bron yaratishda tekshiriladi; tugagan bronlar o'tmishda bo'lgani uchun `Booking.clean()` o'zgartirilmadi.
  - Holat mashinasi `confirmed → cancelled` ga ruxsat beradi, shuning uchun parallel "to'lov + bekor qilish" navbatma-navbat ikkalasi ham muvaffaqiyatli bo'lishi mumkin: natija — to'langan, lekin bekor qilingan bron (refund kerak). Bu qulflash xatosi emas, biznes oqimi; admin "bekor qilish + refund" amali (#15 eslatmasi) shu holatni ham qamrab olishi kerak.
  - Celery beat task sinovdan faqat to'g'ridan-to'g'ri chaqirish orqali o'tgan; lokal muhitda Redis ishlamaydi, shuning uchun worker/beat jonli ishga tushirilmagan.
- #10/#11/#12 tuzatishlaridan keyin (`6506d30`..`d51bd96`):
  - Production'da `NUM_PROXIES` ni haqiqiy proxy soniga moslash kerak (masalan, bitta nginx orqasida 1); aks holda barcha foydalanuvchilar proxy IP'si bilan ko'rinadi va bitta umumiy throttle'ga tushadi.
  - `USE_REDIS_CACHE` sukut bo'yicha `DEBUG=False` da yoqiladi — production'da Redis ishlamasa, throttle/lockout so'rovlari xato beradi (jimgina LocMem'ga o'tmaydi).
  - Bitta hujumchi bitta OTP kodining 3 ta urinishini yoqib yuborishi mumkin (egasi yangi kod so'raydi); `otp/request` throttle'i raqam bo'yicha 3/min.
  - `otp/request` ro'yxatdan o'tmagan raqamga ham 200 qaytaradi: frontend bunday foydalanuvchiga ham kod kiritish ekranini ko'rsatadi.
- To'liq test to'plami PostgreSQL'da: SQLite'dagi 35 ta eski xatodan tashqari yana 38 ta test yiqiladi. Hammasining sababi bitta: test fixture'lari `confirmation_code='TEST1234'`/`'TEST12345'` (8–9 belgi) beradi, maydon esa checkpoint 23 (`c63437b`) dan beri `varchar(6)`. SQLite uzunlikni tekshirmagani uchun bu yashirin qolgan. *Keyin tuzatildi — `d2bc3b5`.*
- #20/#21/#22/#25 tuzatishlaridan keyin (`68ec591`..`50a8a26`), 2026-09-24:
  - To'liq to'plam PostgreSQL'da (`--create-db`): **822 passed, 2 skipped, 0 failed**. Oldin 797 passed edi, 25 ta yangi test qo'shildi. Har bir yangi test avval eski kodda ishga tushirildi. Qoidani buzuvchi holatlar (bronsiz yoki takroriy sharh, approved sharhni tahrirlash, author almashtirish, staff ro'yxatda, join ko'paytirishi, cookie sukuti) eski kodda yiqildi. Allaqachon ishlayotgan qoidalar uchun qo'shilgan himoya testlari (begona/tugallanmagan bron, env override) eski kodda ham o'tdi. `LIMIT` testi eski kodda staff tekshiruvida oldinroq yiqiladi.
  - `booking` majburiy bo'lgani API uchun breaking change. Frontend (`ReviewsSection.tsx`) `booking_id` ni allaqachon `eligible_properties` dan `property_id` bo'yicha `find` qilib oladi. Ro'yxatda faqat sharhsiz bronlar bo'lgani uchun u o'sha mulkning sharhsiz eng yangi bronini topadi, ya'ni o'zgarishsiz ishlaydi. Tahrir `pending` ga qaytishini UI'da ko'rsatish — `HANDOFF.md` da Baxram uchun qayd qoldirildi.
  - Mavjud bazada bronsiz yoki bir bronga bir nechta sharhlar bo'lsa, ular o'zgarmay qoladi; yangi qoida faqat yangi yozuvlarga qo'llanadi.
