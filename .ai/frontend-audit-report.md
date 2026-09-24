# Frontend auditi

- Audit sanasi: 2026-09-24
- Qamrov: `frontend/` (React 18 + TypeScript + Vite). Kod o'zgartirilmadi, faqat o'qish va tekshiruv.
- Solishtirilgan manbalar: `.ai/audit-report.md`, `.ai/contracts/{auth,booking,payments}.md`, `.ai/HANDOFF.md`, `.ai/API_CONTRACT.md` va backend kodining o'zi (kontrakt bilan kod farq qilgan joyda kod asos qilib olindi)
- Belgilar: ✅ = ishga tushirib tasdiqlangan (skript, tsc, build chiqishi), belgisiz = kodni o'qib topilgan
- Topilmalarning ko'pi frontend'ga tegishli (Baxram). Backend yoki kontrakt o'zgarishi kerak bo'lgan joylar **[backend]** deb belgilangan (Kolya).

## Holat jadvali

| # | Topilma | Jiddiylik | Kim |
|---|---|---|---|
| F1 | Birorta sahifada `default` export yo'q, `React.lazy` hamma marshrutda yiqiladi, ilova ochilmaydi | Kritik | frontend — **tuzatildi** `3b17b25` |
| F2 | CSRF token yuborilmaydi: login'dan keyin barcha POST/PATCH/DELETE 403 qaytaradi (logout ham) | Kritik | frontend + [backend] — **tuzatildi** backend `668e91b`, frontend `37ddad8` |
| F3 | Yagona xato formatidagi `error` obyekt sifatida JSX'ga tushadi, sahifa ErrorBoundary'ga yiqiladi | Kritik | frontend — **tuzatildi** `3eeb9c3` |
| F4 | Sharh yaratish har doim 400: maydon nomlari backend bilan mos emas | Kritik | frontend — **tuzatildi** `d043043` ([backend] kontrakt matni hali ochiq) |
| F5 | To'lov oqimi `/confirm/` ni chaqiradi, production'da doim "to'lov muvaffaqiyatsiz" bo'ladi | Yuqori | frontend (+ provayder integratsiyasi) |
| F6 | `/auth/me` `is_staff`/`is_superuser` qaytarmaydi, admin panel va support lookup haqiqiy staff'ga "access denied" ko'rsatadi | Yuqori | [backend] + frontend — backend qismi **tuzatildi** `668e91b` (`is_staff`), `is_superuser` qaytarilmaydi |
| F7 | Narx xulosasi xonalar sonini va kechalik inventar narxini hisobga olmaydi | Yuqori | frontend |
| F8 | Bron validatsiya xatolari (o'tgan sana, sig'im, inventar) foydalanuvchiga ko'rsatilmaydi | Yuqori | frontend |
| F9 | OTP oqimi: noto'g'ri kodda "HTTP 400: Bad Request", ro'yxatdan o'tmagan raqamga tushuntirish yo'q | O'rta | frontend |
| F10 | Har to'lovda foydalanuvchi IP'si uchinchi tomonga (api.ipify.org) yuboriladi | O'rta | frontend |
| F11 | Hotel owner paroli `Math.random()` bilan yaratiladi | O'rta | frontend |
| F12 | Mehmon (login qilmagan) mulk sahifasida sharhlar bloki xato ko'rsatadi | O'rta | frontend + [backend] kontrakt |
| F13 | `.env.example` bilan `/api/v1` ikki marta qo'shiladi | O'rta | frontend |
| F14 | Login'dan keyin bronga qaytmaydi; render paytida `navigate()` | O'rta | frontend |
| F15 | Idempotency kaliti har urinishda yangi, tarmoq xatosidan keyin takroriy tranzaksiya | O'rta | frontend |
| F16 | CSP zaif (`unsafe-inline`, `unsafe-eval`, istalgan `connect-src`), meta'dagi `frame-ancestors`/`X-Frame-Options` ishlamaydi | O'rta | frontend / deploy |
| F17 | `react-router` 6.x: 2 ta moderate zaiflik (npm audit) | Kichik | frontend |
| F18 | Bron formasi `first_name`/`last_name` talab qiladi, checkpoint 21'dan keyin bular ixtiyoriy | Kichik | frontend |
| F19 | Tiplar backend'dan uzoqlashgan, ishlatilmaydigan kod, `console.log` | Kichik | frontend |
| — | Tekshiruv natijalari: tsc 18 xato, lint 267 xato, build o'tadi, testlar 19/825 yiqiladi | — | frontend |

## Topilmalar tafsiloti

### 🔴 Kritik

**F1. Ilova runtime'da ochilmaydi (`React.lazy` + named export).** ✅
`src/App.tsx:8-21` barcha sahifalarni `lazy(() => import('./pages/HomePage'))` bilan yuklaydi. `React.lazy` modulning `default` eksportini kutadi, lekin birorta sahifada ham (va `components/AdminCustomerProfile.tsx`da ham) `export default` yo'q. Hammasi `export function HomePage()` ko'rinishida.
- `tsc --noEmit` shu 14 joyda TS2322 beradi ("Property 'default' is missing").
- `npm run build` baribir o'tadi, chunki `vite build` tip tekshirmaydi (`build:check` esa yiqiladi). Yig'ilgan `dist/assets/HomePage-*.js` oxiri `export{d as HomePage}`, ya'ni `default` yo'q.
- Natija: har qanday marshrutga kirilganda React "Element type is invalid… lazy: Expected the result of a dynamic import() call" xatosini beradi va butun ilova `ErrorBoundary` fallback'iga tushadi. Birorta test `App`ni render qilmaydi, shuning uchun testlar buni ushlamaydi.
*Tuzatish:* `lazy(() => import('./pages/HomePage').then(m => ({ default: m.HomePage })))` yoki har sahifaga `export default`. CI'da `build:check` (yoki `tsc --noEmit`) majburiy bo'lishi kerak.

**F2. CSRF: login'dan keyin barcha o'zgartiruvchi so'rovlar 403.** ✅ (Django test client, `enforce_csrf_checks=True`)
Backend DRF `SessionAuthentication` ishlatadi. U login qilgan foydalanuvchining har bir POST/PUT/PATCH/DELETE so'rovida CSRF token talab qiladi. Frontend hech qayerda `X-CSRFToken` header yubormaydi (`grep` bo'yicha 0 ta). Bundan tashqari:
- backend `CSRF_COOKIE_HTTPONLY = True` (`backend/config/settings.py:189`), ya'ni JS `csrftoken` cookie'ni o'qiy olmaydi;
- backend'da tokenni qaytaradigan endpoint yo'q (`get_token`/`ensure_csrf_cookie` ishlatilmagan).

Tekshiruv: login 200 qaytardi, keyin header'siz `POST /api/v1/bookings/`, `POST /api/v1/auth/logout/` va `POST /api/v1/auth/otp/verify/` → hammasi **403 `{"error":{"code":"error","message":"CSRF Failed: CSRF token missing.",…}}`**.
Ta'siri: bron yaratish/bekor qilish, to'lov, sharh, sevimlilar, profilni yangilash, partner va admin amallari, hatto **logout** ham ishlamaydi. Anonim so'rovlar (login, register, OTP) o'tadi, chunki DRF CSRF'ni faqat autentifikatsiya qilingan sessiyada tekshiradi.
*Tuzatish (ikki tomonlama, kontrakt kerak):* **[backend]** tokenni berish yo'li. Masalan `GET /api/v1/auth/csrf/` (`ensure_csrf_cookie`, tokenni JSON'da qaytaradi) yoki `CSRF_COOKIE_HTTPONLY=False`. **[frontend]** barcha adapterlar uchun umumiy `fetch` wrapper: xavfsiz bo'lmagan metodlarga `X-CSRFToken` qo'shadi va login'dan keyin tokenni yangilaydi (Django login'da tokenni almashtiradi). Kontrakt kelishilmaguncha frontend bu yerda BLOCKED.

**F3. Yagona xato formati `{error: {code, message, details}}` UI'ni yiqitadi.**
Barcha adapterlar xatoni `errorData.detail || errorData.error || \`HTTP …\`` qilib o'qiydi (`authAdapter.ts:104,177`, `bookingAdapter.ts:108-111`, `paymentAdapter.ts:78-81`, `propertyAdapter.ts:243-246`, `partnerAdapter.ts:309-312,542-545`, `adminAdapter.ts:374-377`). Backend `custom_exception_handler` o'rab qaytargan javobda top-level `detail` yo'q, `error` esa **obyekt**. Adapter shu obyektni `error: string` sifatida qaytaradi (TS buni ushlamaydi, chunki `errorData` — `any`), sahifa esa `{error}` ni JSX'da render qiladi. Natijada React "Objects are not valid as a React child" xatosini beradi va sahifa `ErrorBoundary`ga tushadi.
Qaysi javoblar o'raladi (exception handler orqali o'tadiganlar):
- 429 throttle: login, register, `otp/request`, `otp/verify` (5/min), search;
- 503 `ExternalServiceException`: SMS provayder yo'q bo'lsa `otp/request`;
- 403 CSRF (F2) va `PermissionDenied`, 401 `NotAuthenticated`;
- ViewSet'larda `raise`/`is_valid(raise_exception=True)` orqali qaytadigan 400/404: sharhlar, sevimlilar, to'lov yaratish validatsiyasi (muddati o'tgan bron, summa), `get_object` 404.

Backend aslida bitta formatda emas. Kod bo'yicha kamida 4 xil shakl bor: (a) o'ralgan `{error:{code,message,details}}`; (b) tekis `{error: "matn", details}` (bron yaratish, mulk 404, to'lov confirm 403/503); (c) `{detail}` (login 401); (d) `{success:false, message}` va xom `serializer.errors` (OTP, register, profil). Frontend faqat (b) va (c)ni to'g'ri o'qiydi.
`src/utils/errorHandler.ts` (`parseApiError`, `getUserErrorMessage`) mavjud, lekin hech qayerda ishlatilmaydi va u ham `error.message`ni o'qimaydi.
*Tuzatish:* bitta umumiy parser: `error` obyekt bo'lsa `error.message`, satr bo'lsa o'zi, keyin `detail`, `message`, `details`/field xatolari, oxirida status bo'yicha umumiy matn. Hamma adapter shu parserdan foydalansin. **[backend]** uchun tavsiya: (b)–(d) shakllarni ham handler formatiga keltirish, aks holda frontend barcha shakllarni qo'llab-quvvatlashi kerak.

**F4. Sharh yaratish har doim 400 bilan tugaydi.**
`ReviewForm.tsx:61-66` → `accountAdapter.createReview` quyidagini yuboradi: `{ property_id, booking_id, overall_rating, category_ratings: {…}, title, comment }`. Backend `ReviewCreateSerializer` (`backend/accounts/serializers.py:99-140`) esa `property`, `booking` va tekis `cleanliness_rating`, `location_rating`, … maydonlarini kutadi. DRF noma'lum maydonlarni tashlab yuboradi. Shuning uchun `booking` va `property` yo'q bo'ladi va har doim 400 qaytadi, kategoriya baholari esa jimgina yo'qoladi. UI faqat "Invalid review data" deydi (`detail` yo'q, F3).
`.ai/audit-report.md`dagi "#20 — frontend o'zgarishsiz ishlaydi" degan xulosa noto'g'ri. `booking_id`ni tanlash mantig'i to'g'ri, lekin so'rov maydon nomlari hech qachon mos bo'lmagan.
Kontraktning o'zi ham noaniq: `HANDOFF.md:880` `{ property, booking, …, category_ratings (optional) }` deydi, serializer esa `category_ratings`ni qabul qilmaydi. **[backend]** kontraktni kodga moslashi kerak.
*Tuzatish:* `{ property, booking, overall_rating, cleanliness_rating?, …, title, comment }` yuborish.

### 🟠 Yuqori

**F5. To'lov oqimi production'da ishlamaydi.**
`BookingPage.tsx:278-344`: `createPayment` → darhol `confirmPayment`. Kontraktga ko'ra `/confirm/` faqat `PAYMENT_TEST_MODE=True` **va** `DEBUG=True` bo'lganda ishlaydi, aks holda `403 {"error":"Payments are confirmed by the payment provider, not by the client."}`. Hozir provayder integratsiyasi yo'qligi uchun production'da `createPayment` o'zi 503 qaytaradi. Integratsiya qilinganidan keyin ham UI provayderga yo'naltirmaydi va webhook natijasini kutmaydi (`GET /transactions/{id}/` polling yo'q), shuning uchun har to'lov "failure" ekraniga tushadi. "Retry" yangi idempotency kaliti bilan yangi tranzaksiya yaratadi.
*Tuzatish:* `confirm`ni faqat dev mock rejimida chaqirish (masalan `import.meta.env.DEV` + aniq flag bilan). Production uchun create → provayder sahifasi/instruksiyasi → tranzaksiya holatini polling qilish. Oxirgi qism provayder integratsiyasiga bog'liq (BLOCKED).
`payment_method_token`: backend endi uni javobda qaytarmaydi, frontend esa uni ishlatmaydi. Faqat tip noto'g'ri (F19).

**F6. Admin panel va Support lookup haqiqiy staff uchun yopiq.**
`AdminDashboardPage.tsx:23,57` va `SupportLookupPage.tsx:90` `user.is_staff || user.is_superuser` ni tekshiradi. Backend `UserSerializer` (`backend/users/serializers.py:34-37`) bu maydonlarni qaytarmaydi, shuning uchun ular doim `undefined` va har qanday foydalanuvchi, jumladan admin ham, "access denied" ko'radi. Xavfsizlik muammosi emas (backend baribir tekshiradi), lekin admin UI umuman ishlamaydi.
*Tuzatish:* **[backend]** `/auth/me` ga read-only `is_staff`, `is_superuser` (yoki `role`) qo'shish va kontraktda qayd etish. Undan keyin frontend o'zgarishsiz ishlaydi.

**F7. Narx xulosasi haqiqiy narxdan farq qiladi.**
`BookingPage.tsx:66-74,145` `totalPrice = kechalar × pricePerNight` deb hisoblaydi, bu yerda `pricePerNight` — tarifning `base_price`. Backend (#7, #19) `total_price = har kecha inventar narxlari yig'indisi × number_of_rooms` qiladi. Foydalanuvchi 3 xona tanlasa, sidebar 1 xona narxini ko'rsatadi. Kechalik narxlar `base_price`dan farq qilsa, xulosa ham noto'g'ri bo'ladi. To'lov bosqichi sidebar'i (`:558, :571`) va depozit (`:995`) ham shu mijoz hisobidan foydalanadi. To'lov summasi esa to'g'ri `booking.total_price`dan olinadi, ya'ni foydalanuvchi ko'rgan narx bilan to'laydigan narx farq qiladi.
*Tuzatish:* bron yaratilgandan keyin hamma joyda `booking.total_price`. Yaratishdan oldin `GET /properties/{id}/availability/` narx preview'i × `number_of_rooms`.

**F8. Bron validatsiya xatolarining sababi ko'rsatilmaydi.**
Bron yaratish `400 {error: 'Invalid booking parameters' | 'Booking validation failed', details: {check_in: [...], guest_count: [...], ...}}` qaytaradi. Frontend faqat `error` satrini ko'rsatadi (`BookingPage.tsx:263-265`), `details` o'qilmaydi. O'tgan sana, `guest_count > max_occupancy × number_of_rooms` yoki inventar yetmasligi bir xil umumiy matn bilan chiqadi. Frontend sig'imni oldindan ham tekshirmaydi: `number_of_rooms` o'zgarganda `guestCount` bilan solishtirilmaydi.
Faol bo'lmagan mulk: `GET /properties/{id}/` 404 tekis `{error: 'Property not found'}` qaytaradi va bu to'g'ri ko'rsatiladi. Bron yaratishda 400 "Property not found or not available" ham ko'rsatiladi.
*Tuzatish:* `details`dagi field xatolarini formaning tegishli maydonlariga chiqarish. Sig'imni mijozda ham tekshirish (`room_type.max_occupancy`).

### 🟡 O'rta

**F9. OTP oqimi kontrakt bilan to'liq mos emas.** Holatlar bo'yicha:
- `otp/request` ro'yxatdan o'tmagan raqamga 200 qaytaradi. UI kod kiritish ekraniga o'tadi, lekin backend `message`ini ("If this phone number is registered, a verification code has been sent.") ko'rsatmaydi (`authAdapter.ts:183-186` faqat `otp_code`ni oladi). Kod kelmagan foydalanuvchiga tushuntirish ham, "ro'yxatdan o'tish" havolasi ham yo'q. Enumeration'dan himoya to'g'ri saqlanadi, faqat UX yetishmaydi.
- `otp/verify` noto'g'ri, eskirgan yoki bloklangan kod → 400 `{success:false, message:"Invalid or expired OTP code"}`. Adapter `message`ni o'qimaydi va UI "HTTP 400: Bad Request" ko'rsatadi. Bloklangan va noto'g'ri kodni bir xil ko'rsatish to'g'ri, faqat matn o'qilmayapti.
- `otp/verify` 429, `otp/request` 429 va 503 (SMS provayder yo'q) → F3 bo'yicha sahifa yiqiladi.
- Bloklangan login → 401 `{detail: "Invalid credentials…"}`, to'g'ri ko'rsatiladi ✓.
- Noto'g'ri telefon formati → xom `serializer.errors` → "HTTP 400: Bad Request".
- Test kodi faqat `MODE !== 'production'` bo'lganda ko'rsatiladi ✓.

**F10. Foydalanuvchi IP'si uchinchi tomonga yuboriladi.** `paymentAdapter.getClientIp()` (`paymentAdapter.ts:170-178`) har to'lovda `https://api.ipify.org`ga so'rov yuboradi. Backend `client_ip`/`user_agent`ni endi e'tiborsiz qoldiradi va o'zi yozadi (#16), shuning uchun bu so'rov foydasiz. U foydalanuvchi IP'si va to'lov vaqtini tashqi servisga oshkor qiladi va CSP'da `connect-src https:` ochiq bo'lishiga sabab bo'ladi.
*Tuzatish:* `getClientIp` va `client_ip`/`user_agent` maydonlarini olib tashlash.

**F11. Hotel owner paroli kriptografik bo'lmagan RNG bilan yaratiladi.** `CreateHotelOwnerAccount.tsx:23-32` `Math.random()` ishlatadi. Bundan tashqari, tasodifiy 16 belgi backend murakkablik talabini (katta/kichik harf, raqam, belgi) har doim ham qondirmaydi, shuning uchun ba'zan 400 qaytadi.
*Tuzatish:* `crypto.getRandomValues` va har bir belgi turidan kamida bittasini kafolatlash.

**F12. Anonim foydalanuvchi mulk sahifasida sharhlar o'rniga xato ko'radi.** `ReviewsSection` `property_scores`ni har doim chaqiradi. Bu endpoint `IsAuthenticated` (`backend/accounts/views.py:105`), shuning uchun login qilmagan mehmon "Error Loading Reviews / Authentication required" blokini ko'radi. Login qilgan foydalanuvchi ham faqat o'z sharhlarini ko'radi, boshqalarning tasdiqlangan sharhlari ro'yxati yo'q.
*Tuzatish:* frontend'da anonim uchun `property_scores`ni chaqirmaslik yoki 401'ni jim o'tkazish. **[backend]**: ommaviy sharhlar va ballar kerakmi, kontraktda hal qilinsin.

**F13. `/api/v1` ikki marta qo'shiladi.** Adapterlar `${VITE_API_BASE_URL}/api/v1/...` quradi (sukut `http://localhost:8000`), `frontend/.env.example` esa `VITE_API_BASE_URL=http://localhost:8000/api/v1` beradi. Namunani nusxalagan dasturchida barcha so'rovlar `/api/v1/api/v1/...` bo'lib 404 qaytaradi. `utils/api.ts` (ishlatilmaydi) esa aksincha `/api/v1`ni kutadi.
*Tuzatish:* `.env.example`ni `http://localhost:8000` (yoki bo'sh qiymat bilan Vite proxy) ga o'zgartirish.

**F14. Login'dan keyin bronga qaytmaydi; render paytida navigate.** `BookingPage.tsx:152` `navigate('/login', { state: { from: location.pathname, state: location.state } })`, ya'ni `from` — satr. `LoginPage.tsx:24,39,73` esa `from.pathname`ni o'qiydi. Natijada foydalanuvchi `/`ga tushadi va tanlangan xona/sana yo'qoladi. `LoginPage.tsx:23-27` (va `RegisterPage`) `navigate()`ni render ichida chaqiradi. Bu React ogohlantirishi va StrictMode'da ikki marta navigatsiyaga olib keladi. `BookingPage` redirect effekti AuthContext `isLoading`ni kutmaydi, shuning uchun sessiya tekshiruvi sekin bo'lsa, login qilgan foydalanuvchi ham login sahifasiga otilishi mumkin.

**F15. Idempotency kaliti har urinishda yangi.** `generateIdempotencyKey()` har "Confirm" bosilganda yangi kalit yaratadi. Agar `createPayment` serverda muvaffaqiyatli bo'lib, javob tarmoqda yo'qolsa, qayta urinish ikkinchi tranzaksiya yaratadi. Backend idempotency'si (#32) shu holat uchun qilingan, lekin frontend undan foydalanmaydi.
*Tuzatish:* kalitni bron + provayder uchun bir marta yaratib, shu bron bo'yicha qayta urinishlarda qayta ishlatish.

**F16. CSP zaif.** `index.html` meta CSP: `script-src 'self' 'unsafe-inline' 'unsafe-eval'` XSS himoyasini deyarli yo'qqa chiqaradi; `connect-src 'self' https: http:` va `img-src … http:` istalgan domen. `frame-ancestors` va `X-Frame-Options`ni brauzerlar `<meta>`da e'tiborsiz qoldiradi, shuning uchun clickjacking himoyasi faqat server header'lari orqali bo'lishi mumkin.
*Tuzatish:* CSP'ni deploy server header'iga ko'chirish, `unsafe-eval`/`unsafe-inline`ni olib tashlash, `connect-src`ni API domeni bilan cheklash.

### 🟢 Kichik

**F17. `react-router-dom` 6.x — 2 ta moderate advisory** (`npm audit --omit=dev`): `<Link>`/`useNavigate`da backslash orqali open redirect (GHSA-wrjc-x8rr-h8h6) va SSR hydration (GHSA-337j-9hxr-rhxg, SSR ishlatilmaydi). Hozirgi kodda `navigate(from)` faqat ichki `location.state`dan olinadi. Tuzatish 7.x'ga o'tishni talab qiladi (breaking).

**F18. Bron formasi ism-familiya majburiy.** `BookingPage.tsx:196-206` `first_name` va `last_name`ni kamida 2 belgidan talab qiladi va ularni profildan to'ldiradi. Checkpoint 21'dan keyin ular ixtiyoriy, asosiy maydon esa `full_name`. Faqat `full_name` bilan ro'yxatdan o'tgan foydalanuvchi qayta yozishi kerak, bir so'zli ism esa umuman o'tmaydi. Backend baribir `guest_full_name` kutadi.

**F19. Mayda nomuvofiqliklar.**
- `PaymentTransaction` tipida `payment_method_token`, `client_ip`, `user_agent` bor, lekin backend birinchisini qaytarmaydi, qolganlarini mijozdan qabul qilmaydi. `User` tipida `is_staff`/`is_superuser` bor, lekin ular kelmaydi (F6).
- `number_of_rooms` input qiymati `handleInputChange` orqali satr sifatida saqlanadi (tipda `number`).
- Sharhni tahrirlash UI'i yo'q, shuning uchun "tahrir moderatsiyaga qaytadi" xabari hozircha kerak emas. `ReviewCard`da `pending` belgisi bor ✓.
- `eligible_properties` bo'yicha `find(property_id)` sharhsiz eng yangi bronni tanlaydi. Bu to'g'ri ishlaydi, lekin foydalanuvchi qaysi turar joyiga sharh yozayotganini tanlay olmaydi.
- `utils/api.ts` va `utils/errorHandler.ts` ishlatilmaydi. `console.log`lar: `Header.tsx:32,38`, `SearchResultsPage.tsx:125`. `SearchResultsPage`dagi `currentPage`/`totalPages` ishlatilmaydi (paginatsiya ulanmagan).
- `authAdapter.ts:209` tiplarni ikki marta eksport qiladi (TS2484).

## Tekshiruv natijalari (✅)

`npm ci`dan keyin, `frontend/`da:

| Tekshiruv | Natija |
|---|---|
| `tsc --noEmit` | **18 xato**: 14 × TS2322 (`App.tsx` lazy, F1), 3 × TS2484 (`authAdapter.ts:209`), 1 × TS2865 (`AdminCustomerProfile` import) |
| `npm run lint` | **277 muammo (267 xato, 10 ogohlantirish)**: 167 `no-explicit-any`, 11 `no-unused-vars`, 9 `react-hooks/exhaustive-deps`, `no-extra-semi` va boshqalar |
| `npm run build` | O'tadi (tip tekshirmaydi). `npm run build:check` tsc sababli yiqiladi |
| `npm test` | **806 passed, 19 failed** (825), 4 fayl: `AdminCustomerProfile`, `AdminCustomersList`, `AdminStatisticsDashboard`, `SupportLookupPage`. Asosiy sabab: komponentlar `<Link>`ni Router'siz render qiladi ("Cannot destructure property 'basename'…"). Qolganlari eskirgan matn tanlovchilari |
| `npm audit --omit=dev` | 2 moderate (`react-router`, F17) |

## Joyida bo'lgan narsalar

- `dangerouslySetInnerHTML`, `innerHTML`, `eval` yo'q. Backend ma'lumotlari React orqali escape qilinadi.
- Token yoki maxfiy ma'lumot `localStorage`/`sessionStorage`da saqlanmaydi. Faqat `CoachMark` ko'rsatilgan-ko'rsatilmaganlik bayrog'i saqlanadi.
- Repoda faqat `.env.example` bor va unda kalitlar yo'q. Kodda API kalit yoki secret topilmadi.
- Barcha so'rovlarda `credentials: 'include'` bor. Sessiya cookie HttpOnly, JS unga tegmaydi.
- Tashqi havolalarda `rel="noopener noreferrer"`. WhatsApp/Telegram havolalari `https://` bilan boshlanadi (`javascript:` sxemasini kiritib bo'lmaydi).
- Test OTP kodi production build'da ko'rsatilmaydi.

## Tavsiya etilgan tartib

1. F1 (ilova ochilishi) va F3 (umumiy xato parseri) — faqat frontend, tez.
2. F2 — avval Kolya bilan CSRF kontraktini kelishish, keyin umumiy `fetch` wrapper (F3 parseri bilan birga).
3. F4, F6 — maydon nomlari va `/me` kontrakti (F6 backend tarafda).
4. F5, F7, F8, F9 — bron/to'lov/OTP UX.
5. Qolganlari, keyin tsc, lint va testlarni tozalash hamda CI'ga `build:check` qo'shish.

## Audit muhiti haqida

- Hech bir kuzatiladigan fayl o'zgartirilmadi. Faqat shu hisobot qo'shildi.
- Tekshiruvlar uchun `frontend/node_modules/` (`npm ci`) va `frontend/dist/` (`npm run build`) yaratildi. Ikkalasi ham `.gitignore`da.
- F2 tekshiruvi backend'da in-memory SQLite bilan alohida skript orqali qilindi (dev bazaga tegilmadi). Skript repodan tashqarida saqlangan.

---

## 2-bosqich: tuzatishlar, API solishtiruvi va e2e (2026-09-24)

Branch: `fix/frontend-audit`. Baxram ruxsati bilan frontend o'zgartirildi. Faqat F1–F4 tuzatildi. Quyidagi F20–F32 **faqat hisobot**, ular uchun kod o'zgarmagan.

### Tuzatilganlar

| # | Nima qilindi | Commit | Test |
|---|---|---|---|
| F2 [backend] | `GET /api/v1/auth/csrf/` (`{"csrf_token"}`), `/auth/me` ga read-only `is_staff`. Kontrakt: `contracts/auth.md`, `API_CONTRACT.md` | `668e91b` (master) | `users/tests/test_csrf.py` (7). Backend to'liq to'plami PostgreSQL'da: 855 passed, 2 skipped |
| F1 | 13 sahifa + `AdminCustomerProfile`ga `export default` | `3b17b25` | `App.test.tsx`: har bir lazy modul + 3 marshrut render. Tuzatishsiz 17/17 yiqiladi |
| F3 | `errorHandler.readApiError`: 4 xil backend shakli, field xatolari o'qiladigan matnga aylanadi, 400/401/403/404/429 (Retry-After)/503 va CSRF uchun alohida xabar. Hamma adapterlar shundan foydalanadi | `3eeb9c3` | `errorHandler.test.ts` (+19), adapter testlari |
| F2 | `utils/api.ts` `apiFetch`: token `/auth/csrf/`dan olinadi va keshlanadi, POST/PUT/PATCH/DELETE'da `X-CSRFToken`, CSRF 403'da bir marta yangi token bilan qayta urinadi; login/OTP/register/logout'dan keyin kesh tozalanadi. Hamma adapterlar `apiFetch` ishlatadi | `37ddad8` | `utils/api.test.ts` (15) |
| 4-band | `build` = `tsc && vite build` (`build:check` olib tashlandi). Qolgan 4 ta tsc xatosi tuzatildi, `App.tsx` tsconfig exclude'dan chiqarildi | `b9edde1` | `build.test.ts`; ataylab kiritilgan tip xatosida build exit 2 bilan to'xtashi tekshirildi |
| F4 | `CreateReviewRequest` = `{property, booking, overall_rating, *_rating?, title?, comment?}`; bronsiz forma yuborilmaydi | `d043043` | `ReviewForm.test.tsx`, `accountAdapter.test.ts` |

Yakuniy holat: `tsc` 0 xato, `npm run build` o'tadi, `npm test` 863 passed / 19 failed. 19 tasi avvaldan bor, o'sha 4 faylda (Router'siz render). Lint 276 (avval 277), yangi muammo yo'q.

### E2E (✅, haqiqiy backend + brauzer)

Muhit: alohida PostgreSQL `tickbron_e2e` (dev bazaga tegilmadi), `runserver` `DEBUG/SMS_TEST_MODE/PAYMENT_TEST_MODE=True` bilan, `vite` dev :3000, Chrome.

| Oqim | Natija |
|---|---|
| Ilova ochilishi (F1) | ✅ `/login`, `/`, `/property/1` ochiladi |
| OTP login (UI) | ✅ kod so'rash → test kodi → verify 200 → bosh sahifa, sessiya bor |
| Bron (UI) | ❌ **F21** tufayli: "Proceed to booking" → `GET /properties/undefined/` 404. Xato endi o'qiladigan matn sifatida chiqadi ("The requested resource was not found."), sahifa yiqilmaydi (F3 ✓) |
| Bron (ilovaning o'z adapteri orqali, sessiya + CSRF) | ✅ `POST /bookings/` 201 (2 kecha, 220.00; F7 tasdiqlandi, UI 100 × kecha hisoblaydi). O'tgan sana → "Invalid booking parameters. Check in: Check-in date cannot be in the past". To'lov yaratish 201, confirm → `completed` |
| Sharh (UI) | ❌ **F20** tufayli: `ReviewsSection` "Failed to load reviews" ko'rsatadi, forma chiqmaydi |
| Sharh (adapter orqali) | ✅ 201, kategoriya baholari saqlandi (bazada tekshirildi). Pending bronga → "Booking: You can only review completed bookings.", takroriy → "Booking: This booking has already been reviewed." |
| Logout | ✅ 200, keyin `/auth/me` → "Authentication required. Please log in." |
| CSRF | ✅ butun sessiya davomida backend logida 0 ta 403 |

### Frontend ↔ backend nomuvofiqliklari (yangi, tuzatilmagan)

Usul: har bir adapter chaqiruvi backend URL, serializer va view bilan solishtirildi. E2e bazada rol bo'yicha (guest/staff/owner) haqiqiy javoblar olindi (✅).

| # | Topilma | Jiddiylik | Kim |
|---|---|---|---|
| F20 | Global `PageNumberPagination` (PAGE_SIZE 20): ViewSet ro'yxatlari `{count,next,previous,results}` qaytaradi, frontend massiv kutadi | Kritik | frontend (+[backend] kontrakt) |
| F21 | Mulk javobidagi `room_types[]`da `property_id` yo'q, shuning uchun bron UI'da `propertyId` undefined | Kritik | frontend |
| F22 | Sevimlilarga qo'shish har doim 400 qaytaradi (`property_id` yuboriladi, `property` kerak); ro'yxat maydonlari boshqa nomda | Kritik | frontend + [backend] |
| F23 | Qidiruv natijalarida `translations` yo'q, `PropertyCard` `translations[0]`da yiqiladi | Kritik | frontend + [backend] |
| F24 | Support lookup javobi ichma-ich (`booking`/`customer`/`property`), frontend tekis + `room` kutadi, sahifa yiqiladi | Yuqori | frontend |
| F25 | Admin statistika: registrations `statistics` qaytaradi (frontend `data` kutadi), top-bookers `{period,limit,leaderboard}` (frontend massiv kutadi) | Yuqori | frontend |
| F26 | `AdminUser`: backend `role_name` qaytaradi, `is_superuser` yo'q; frontend `role`, `is_superuser` kutadi | O'rta | frontend |
| F27 | Admin to'lovlar: backend `booking_id` (frontend `booking`), `provider_response`/`payment_method_token`/`client_ip` yo'q | O'rta | frontend |
| F28 | `AdminAmenity`: `category_name`, `created_at`, `updated_at` qaytmaydi; kategoriyada ham sanalar yo'q | Kichik | frontend |
| F29 | Partner tiplari: `owner`, `approved_*`, `created_at/updated_at` qaytmaydi; inventardagi `remaining_rooms` tipda yo'q; bronlarda `guest`, `property`, `special_requests` yo'q; foto javobida `photo_url` bor. Partner mulkka nom (translation) berolmaydi | O'rta | frontend + [backend] |
| F30 | Sharh yaratish javobida faqat kiritilgan maydonlar bor (`id`, `status` yo'q); `Review` tipidagi `updated_at` qaytmaydi | Kichik | [backend] + frontend |
| F31 | Decimal maydonlar satr bo'lib keladi (`"100.00"`), tiplarda esa `number` (`base_price`, `total_price`, `amount`, `price`, `total_amount_paid`) | Kichik | frontend |
| F32 | Header `first_name`ni ko'rsatadi; checkpoint 21'dan beri u ko'pincha `null`, shuning uchun "User" chiqadi | Kichik | frontend |

**F20 tafsiloti.** Paginatsiyalangan (✅): `me/favorites/`, `me/reviews/`, `me/history/`, `admin-panel/properties/`, `admin-panel/amenities/`, `admin-panel/amenities/categories/`, `partner/properties/`, `partner/rooms/`, `partner/rates/`, `partner/inventory/`, `payments/transactions/`. Massiv qaytaradiganlar (✅): `bookings/`, `admin-panel/users/`, `admin-panel/payments/transactions/`, `partner/bookings/`, `me/history/recent/`. Ta'siri: `FavoritesPage` obyektni `setFavorites`ga beradi va `.map`da yiqiladi; `ReviewsSection` `.filter`da xato beradi va "Failed to load reviews" ko'rsatadi (✅ e2e); `AdminPropertyModeration`, `AdminAmenityManagement`, `PartnerRoomsManagement`, `PartnerRatesManagement` `[...data]`/`.filter`da TypeError beradi; `PartnerDashboardPage` `setProperties(obj)` qiladi. Inventar 20 yozuvdan keyin kesiladi (`next` bor). *Tuzatish:* adapterlarda `results`ni ochish va `next` bo'yicha yurish, yoki [backend] bu endpointlar uchun paginatsiyani o'chirib, kontraktda yozish.

**F21.** `RoomSelection.tsx:100` `propertyId: selectedRoom.property_id` qiladi, lekin `PropertySerializer.room_types` elementlarida `property_id` ham, `property` ham yo'q (✅). `rate_plans` elementlarida `room_type_id` va `is_active` ham yo'q. *Tuzatish:* `propertyId`ni sahifadagi `property.id`dan olish.

**F22.** `accountAdapter.addFavorite` `{property_id}` yuboradi → 400 `{"property":["This field is required."]}` (✅). `{property}` bilan 201 qaytadi, lekin javob faqat `{"property":1,"notes":null}` (`id` yo'q, [backend]). Ro'yxat maydonlari: backend `property_city`, `property_country`, `property_base_price`, `property_currency`, `property_primary_photo` qaytaradi; frontend `city`, `country`, `base_price`, `currency`, `primary_photo`, `property_name` kutadi (nom umuman qaytmaydi).

**F23.** `PropertySearchResultSerializer` natijalarida `translations`, `rating`, `review_count` yo'q (✅). `PropertyCard.tsx:15` `property.translations[0]`ni o'qiydi, shuning uchun natija bo'lsa qidiruv sahifasi ErrorBoundary'ga tushadi (koddan). *Tuzatish:* [backend] nom/translation qo'shish yoki frontend'da himoya.

**F24.** `admin_booking_lookup_by_reference` `{booking:{id, reference_code, status, …, booking_items}, customer:{…}, property:{…}}` qaytaradi. `SupportLookupPage.tsx` `booking.reference_code`, `booking.status` (yuqori darajada) va `booking.room.name`ni o'qiydi; `room` yo'q, TypeError.

**F25.** `AdminStatisticsDashboard.tsx:90` `statistics.data.length`ni o'qiydi, backend esa `statistics` qaytaradi, `data` undefined, sahifa yiqiladi. `TopBookersLeaderboard` obyektni massiv sifatida saqlaydi.

### Keyingi qadam uchun tavsiya
F20–F23 bron, sharh, sevimlilar va qidiruv oqimlarini UI'da to'sib turibdi. Keyingi checkpoint'da avval shu to'rttasi, keyin F24–F25 (admin sahifalari yiqiladi).
