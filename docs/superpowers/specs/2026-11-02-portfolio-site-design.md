# Portfolio sayt: dizayn spetsifikatsiyasi

Sana: 2026-11-02. Holat: foydalanuvchi dizaynni suhbatda tasdiqlagan, yozma spec ko'rib chiqilishi kutilmoqda.

## Maqsad
Bitta shaxs uchun (mijoz buyurtmasi, 1 mln so'm) 3D va animatsiyali, sokin va "relax" kayfiyatdagi portfolio sayt. Ko'rsatiladi: ism-familiya, til sertifikatlari, shaxsiy veb-sayt havolasi, ijtimoiy tarmoqlar (Telegram va boshqalar).

## Faktlar va taxminlar
- Haqiqiy shaxs ma'lumotlari hali yo'q. Namuna profil ishlatiladi: Aziza Karimova, ingliz tili o'qituvchisi va tarjimon. Ma'lumot kelganda faqat `src/data/profile.ts` almashtiriladi.
- Sayt TICKBRON backend/frontend'dan mustaqil: `portfolio/` papkasida. Backend yo'q, statik build.
- Taxmin: namuna sertifikatlar (IELTS 8.0, CEFR C2, TOEFL, Cambridge CAE, TORFL) va havolalar soxta, bosilganda `example.com` kabi namuna manzillar ishlatiladi. Haqiqiy ma'lumot kelguncha bularni haqiqiy deb e'lon qilmaymiz.

## Texnologiya
Vite + React + TypeScript, three + @react-three/fiber + @react-three/drei, Framer Motion (matn va kartalar animatsiyasi), Vitest + Testing Library, ESLint. `any` ishlatilmaydi.

## Arxitektura
- `src/data/profile.ts`: yagona tipli ma'lumot manbai (ism, kasb, bio, statistika, sertifikatlar, sayt, ijtimoiy havolalar).
- `src/i18n/`: UZ/EN/RU lug'atlar va `useT()` hook; barcha matnlar kalit orqali. Til tanlovi `localStorage`'da (xatoga chidamli).
- `src/scene/`: 3D sahna. `Scene.tsx` (Canvas, yorug'lik), `Shapes.tsx` (suzuvchi shaffof shakllar), `Globe.tsx`, `useScrollCamera.ts` (scroll bilan kamera). Sahna `React.lazy` bilan alohida chunk.
- `src/sections/`: `Hero`, `About`, `Certificates`, `Website`, `Contact`; har biri bitta vazifa.
- `src/components/`: `TiltCard` (sichqoncha/qiyshayish bilan 3D burilish), `Counter`, `LanguageSwitch`, `SocialButton`.
- `src/hooks/useReducedMotion.ts`, `useIsMobile.ts`: soddalashtirish qarorlari bitta joyda.

## Dizayn
- To'q ko'k-binafsha gradient fon, yumshoq neon yorug'lik, glassmorphism kartalar. Ranglar `:root` tokenlari sifatida.
- Harakat sekin va silliq (3-8 s sikllar). Tovush yo'q.
- Bo'limlar (bitta uzun sahifa): Hero, Haqida (statistika hisoblagich), Sertifikatlar (TiltCard'lar: nomi, ball, yil, tashkilot), Shaxsiy sayt (katta karta, `target="_blank"` va `rel="noopener noreferrer"`), Aloqa (Telegram, Instagram, LinkedIn, email).
- Sertifikatlarda rasm bo'lmasa, toza tipografik karta ko'rsatiladi (empty holat).

## Ishlash va murakkablik
- Mobil (<768px): obyektlar soni kamaytiriladi, `dpr` cheklanadi. `prefers-reduced-motion`: 3D harakat va animatsiyalar o'chiriladi, statik gradient qoladi.
- WebGL mavjud bo'lmasa yoki sahna xato bersa: `ErrorBoundary` statik gradient fonga o'tadi, kontent baribir ko'rinadi.
- 3D sahna yuklanguncha yengil loading holat (skeleton fon).

## Qulaylik
Klaviatura bilan barcha havolalar fokuslanadi (ko'rinadigan fokus), kontrast WCAG AA, havola/tugmalarda `aria-label`, 3D kanvas `aria-hidden`. Sarlavhalar tartibli (h1 bitta).

## Test
- Birlik: profil ma'lumoti tuzilishi, i18n kalitlari UZ/EN/RU'da to'liq, `Counter`, `LanguageSwitch`.
- Komponent: har bo'lim profil ma'lumotini ko'rsatadi; sayt havolasi to'g'ri `href`, `target`, `rel` bilan; ijtimoiy tugmalar to'g'ri manzilga; sertifikat rasmsiz ham chiziladi.
- Xatolik: `ErrorBoundary` fallback; reduced-motion holatida 3D chiziladi/o'chadi.
- Qo'lda tekshiruv: 390px va 1440px skrinshotlar (Playwright), build o'lchami hisoboti.

## Chegaralar (qilinmaydi)
Backend, CMS, admin panel, forma yuborish, analitika, tovush. Bular alohida buyurtma bo'lishi mumkin.

## Joylashtirish
`npm run build` statik `dist/` beradi; Vercel/Netlify/Cloudflare Pages'ga yuklanadi. Joylashtirish mijoz tasdiqidan keyin, foydalanuvchi bilan kelishib.

## Ochiq masalalar
Haqiqiy ma'lumot, rasm, domen nomi, UZ/EN/RU dan qaysi biri asosiy til ekanligi mijozdan kutiladi.
