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
| 4 | To'lovni klient bepul tasdiqlaydi (/confirm/, PAYMENT_TEST_MODE) | Kritik | Ochiq (sukut qiymati `d6ff853` da False qilingan, endpoint hali ochiq) |
| 5 | Webhook'lar ishlamaydi (auth talab qilinadi, holat yangilanmaydi) | Kritik | Ochiq |
| 6 | Webhook event imzodan oldin yoziladi — haqiqiy event bloklanadi | Kritik | Ochiq |
| 7 | number_of_rooms: 1 xona narxi/inventari, bekor qilishda N | Kritik | Ochiq |
| 8 | phone_number unikal emas | Yuqori | ✅ Tuzatildi — `f050dcd` |
| 9 | OTP brute-force (throttle yo'q, random, lock tekshiruvi keyin) | Yuqori | ✅ Tuzatildi — `73b0247` |
| 10 | X-Forwarded-For orqali throttle chetlab o'tiladi, LocMem cache | Yuqori | Ochiq |
| 11 | Akkaunt bloklash DoS, user enumeration | Yuqori | Ochiq |
| 12 | Partner mulk statusini o'zi `active` qiladi | Yuqori | Ochiq |
| 13 | Suspended/rejected mulk bronlanadi va ommaga ko'rinadi | Yuqori | Ochiq |
| 14 | Har qanday foydalanuvchi barcha webhook event'larini ko'radi | Yuqori | Ochiq |
| 15 | Refund: mehmon o'zi qiladi, mantiq teskari, summa tekshirilmaydi | Yuqori | Ochiq |
| 16 | Begona bronga to'lov tranzaksiyasi; tranzaksiya PATCH/DELETE ochiq | Yuqori | Ochiq |
| 17 | Muddati o'tgan bronlar avtomatik bekor qilinmaydi (Celery yo'q) | Yuqori | Ochiq |
| 18 | Race condition: cancel/expire/confirm bron qatorini qulflamaydi | Yuqori | Ochiq |
| 19 | O'tgan sanaga bron, guest_count/xona tekshiruvi, narx yozuvi | O'rta | Ochiq |
| 20 | Bronsiz sharh; sharhda booking/property almashtirish | O'rta | Ochiq |
| 21 | Admin RBAC ishlatilmaydi, audit log yo'q, InternalNote author yoziladi | O'rta | Ochiq |
| 22 | Mijozlar ro'yxati xotirada saralanadi, aggregat join xatosi | O'rta | Ochiq |
| 23 | Rasm yuklash validatsiyasi DRF orqali chaqirilmaydi | O'rta | Ochiq |
| 24 | Ichki xatolar (`str(e)`) klientga, OTP va email loglarda | O'rta | Qisman — OTP kodi logdan olib tashlandi (`73b0247`), qolgani ochiq |
| 25 | SESSION/CSRF cookie secure sukut bo'yicha False | O'rta | Ochiq |
| 26 | Partner bronlar ro'yxati 500 (`booking.guest_name`) | Kichik | Ochiq |
| 27 | Sevimlini o'chirib qayta qo'shish 500 | Kichik | Ochiq |
| 28 | Noto'g'ri query parametrlarida 500 | Kichik | Ochiq |
| 29 | `process_expired_bookings` xatolarni yutadi | Kichik | Ochiq |
| 30 | `conftest.py` testlarni sozlangan (dev) bazada ishlatadi | Kichik | ✅ Tuzatildi — `c98a48f` |
| 31 | Inventar rate_plan bo'yicha, room_type bo'yicha emas | Kichik | Ochiq |
| 32 | To'lov idempotency ishlamaydi (auditdan keyin topildi) | Yuqori | Ochiq |

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

**#21** `Role`/`Permission` modellari ishlatilmaydi — har qanday `is_staff` hamma narsaga kiradi; admin amallari audit log'ga yozilmaydi; `InternalNote` da `author`/`customer` yoziladi.

**#22** Mijozlar ro'yxati barcha foydalanuvchilarni xotiraga yuklab saralaydi; `Count('bookings')` + `Sum(payment_transactions)` join sonlarni ko'paytirishi mumkin; staff ham ro'yxatda.

**#23** Rasm hajmi/kengaytma tekshiruvi `model.clean()` da — DRF uni chaqirmaydi.

**#24** `str(e)` klientga qaytadi (bron yaratish/bekor qilish — ✅ SQL CHECK matni ko'rindi, OTP, search suggestions, webhook); OTP kodlari (tuzatildi) va har so'rovda foydalanuvchi email'i loglarga yoziladi (ochiq).

**#25** `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` sukut `False`.

### 🟢 Kichik

**#26** Partner bronlar ro'yxati har doim 500: `booking.guest_name` yo'q (`partner/views.py:204`). ✅

**#27** Sevimlini o'chirib qayta qo'shish 500 (soft delete + `unique_together`). ✅

**#28** `history/recent?limit=abc`, `reviews/property_scores?property_id=abc` → 500.

**#29** `process_expired_bookings` xatolarni jimgina yutadi (`bookings/models.py:490`).

**#30** `conftest.py` `django_db_setup` ni no-op bilan almashtirgan edi → testlar sozlangan bazada ishlardi.
*Tuzatish:* override olib tashlandi, testlar alohida test bazasida.

**#31** Inventar `rate_plan` bo'yicha yuritiladi — bitta xona turining ikki tarifi bitta jismoniy xonani ikki marta sotishi mumkin.

## Boshqa kuzatuvlar

- Test to'plami (izolyatsiyalangan bazada): 35 ta eski muvaffaqiyatsiz test — 27 tasi `/api/v1/admin/` yo'li (haqiqiy yo'l `/api/v1/admin-panel/`), 2 tasi InternalNote yaratishda body'da `customer` talab qilinishi (kod xatosi), qolganlari eskirgan test kutishlari (reference code uzunligi, Decimal/string, `Property.name`).
- `admin_panel` index nomlari migratsiyasi yetishmasdi — `7f589d1` da qo'shildi.
