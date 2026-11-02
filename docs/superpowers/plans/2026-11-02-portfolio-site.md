# Portfolio sayt Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Namuna profil bilan 3D va animatsiyali, sokin portfolio sayt (Hero, Haqida, Sertifikatlar, Shaxsiy sayt, Aloqa), UZ/EN/RU tillarida.

**Architecture:** `portfolio/` papkasida mustaqil Vite + React + TypeScript statik ilova. Barcha kontent `src/data/profile.ts` da, matnlar `src/i18n/` kalitlarida. 3D sahna alohida lazy chunk; xatolik yoki reduced-motion bo'lsa statik gradient fonga o'tadi.

**Tech Stack:** Vite, React 18, TypeScript (strict), three, @react-three/fiber, @react-three/drei, framer-motion, Vitest + Testing Library, ESLint, Playwright (skrinshot uchun, oldindan o'rnatilgan).

**Spec:** `docs/superpowers/specs/2026-11-02-portfolio-site-design.md`

## Global Constraints

- `portfolio/` papkasidan tashqariga (backend, frontend) tegilmaydi; backend yo'q.
- TypeScript: `any` yo'q; izoh faqat "nega" uchun; o'lik kod va debug print yo'q.
- Barcha ko'rinadigan matn i18n kalitlari orqali (UZ/EN/RU to'liq).
- Tashqi havolalar: `target="_blank"` va `rel="noopener noreferrer"`.
- Mobil <768px: 3D yengillashtirilgan; `prefers-reduced-motion`: animatsiya o'chadi.
- Ranglar `:root` CSS tokenlari; kontrast WCAG AA; 390px va 1440px da ishlaydi.
- Namuna ma'lumot haqiqiy deb e'lon qilinmaydi (`example.com` manzillar).
- Har commitdan oldin `npm test` va `npm run lint`; `.env` yoki parol commit qilinmaydi.
- Commit xabari oxirida: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` va `Claude-Session: https://claude.ai/code/session_01CqZ8RUCS39Ukg2zAi9hCZW`. Faqat `claude/portfolio-website-design-54ilwc` branchiga push.

## Review Focus

- Juda uzun ism yoki sertifikat nomi: karta buzilmasdan o'raladi (wrap), 390px da gorizontal skroll yo'q.
- Sertifikatlar bo'sh ro'yxat: Sertifikatlar bo'limi bo'sh holat matnini ko'rsatadi, xato bermaydi.
- `localStorage` o'qib/yozib bo'lmaydi (private rejim): til tanlovi xatosiz, standart til bilan ishlaydi.
- WebGL yo'q yoki sahna xato beradi: kontent ko'rinadi, statik fon chiziladi.
- Noma'lum til kodi saqlangan bo'lsa: standart tilga qaytadi.

---

### Task 1: Loyiha skeleti va profil ma'lumoti

**Files:**
- Create: `portfolio/` (Vite react-ts shabloni), `portfolio/vitest.config.ts`, `portfolio/src/test/setup.ts`
- Create: `portfolio/src/data/profile.ts`, `portfolio/src/data/profile.test.ts`

**Interfaces:**
- Produces: `type Certificate = { id: string; name: string; score: string; year: number; issuer: string }`, `type SocialLink = { id: 'telegram' | 'instagram' | 'linkedin' | 'email'; label: string; href: string }`, `type Profile = { firstName: string; lastName: string; website: { url: string; label: string }; certificates: Certificate[]; socials: SocialLink[]; stats: { id: string; value: number }[] }`, `export const profile: Profile`.

- [ ] **Step 1:** `npm create vite@latest portfolio -- --template react-ts`, so'ng `npm i three @react-three/fiber @react-three/drei framer-motion` va `npm i -D vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @types/three`. `vitest.config.ts` da `environment: 'jsdom'`, `setupFiles: ['src/test/setup.ts']`; `package.json` da `"test": "vitest run"`.
- [ ] **Step 2:** Test yozing `profile.test.ts`: `profile.certificates.length` 5, har birining `id` noyob, har bir `socials[].href` `https://` yoki `mailto:` bilan boshlanadi, `profile.website.url` `https://` bilan boshlanadi. Ishga tushiring: FAIL (modul yo'q).
- [ ] **Step 3:** `profile.ts` da tiplar va `profile` (Aziza Karimova; IELTS 8.0 2024, CEFR C2 2023, TOEFL iBT 112 2023, Cambridge CAE 2022, TORFL C1 2022; stats: yillar tajriba, o'quvchilar soni, sertifikatlar soni; havollar `example.com`/`t.me/example` namuna).
- [ ] **Step 4:** `npm test` (PASS), `npm run lint`, `npm run build` (PASS).
- [ ] **Step 5:** Commit: `feat(portfolio): scaffold app and sample profile data`.

### Task 2: i18n (UZ/EN/RU)

**Files:**
- Create: `portfolio/src/i18n/dictionaries.ts`, `portfolio/src/i18n/I18nProvider.tsx`, `portfolio/src/i18n/i18n.test.tsx`

**Interfaces:**
- Produces: `type Lang = 'uz' | 'en' | 'ru'`; `export const dictionaries: Record<Lang, Record<string, string>>`; `export function I18nProvider({children}: {children: ReactNode}): JSX.Element`; `export function useI18n(): { lang: Lang; setLang(l: Lang): void; t(key: string): string }`. Kalitlar: `nav.*`, `hero.role`, `hero.cta`, `about.*`, `stats.<id>`, `certs.title`, `certs.empty`, `website.*`, `contact.*`, `lang.*`, `a11y.*`.

- [ ] **Step 1:** Testlar: uchala lug'atda kalitlar to'plami bir xil; `t('hero.role')` standart tilda (`uz`) to'g'ri; `setLang('en')` matnni almashtiradi va `localStorage`ga yozadi; `localStorage` xato (getItem/setItem throw) bo'lsa ham render xatosiz; saqlangan `'xx'` noma'lum kod bo'lsa `uz`ga qaytadi; noma'lum kalit kalitning o'zini qaytaradi. FAIL.
- [ ] **Step 2:** Lug'at va Provider'ni yozing; `localStorage` chaqiruvlari try/catch ichida (xatoga chidamli).
- [ ] **Step 3:** `npm test` PASS; commit: `feat(portfolio): add UZ/EN/RU i18n`.

### Task 3: Hooklar va ErrorBoundary

**Files:**
- Create: `portfolio/src/hooks/useReducedMotion.ts`, `portfolio/src/hooks/useIsMobile.ts`, `portfolio/src/components/ErrorBoundary.tsx`, `portfolio/src/hooks/hooks.test.tsx`, `portfolio/src/components/ErrorBoundary.test.tsx`

**Interfaces:**
- Produces: `useReducedMotion(): boolean` (`prefers-reduced-motion: reduce`), `useIsMobile(): boolean` (`max-width: 767px`), `ErrorBoundary({ fallback: ReactNode; children })`.

- [ ] **Step 1:** Testlar: `matchMedia` mock bilan ikkala hook to'g'ri qiymat qaytaradi va o'zgarishga javob beradi; bola xato tashlasa ErrorBoundary `fallback`ni ko'rsatadi. FAIL.
- [ ] **Step 2:** Implementatsiya (`matchMedia` change listener, unmount'da tozalash). PASS; commit: `feat(portfolio): add motion hooks and error boundary`.

### Task 4: Umumiy komponentlar

**Files:**
- Create: `portfolio/src/components/{Counter,LanguageSwitch,SocialButton,TiltCard}.tsx` va yonida `*.test.tsx`

**Interfaces:**
- Consumes: `useI18n`, `useReducedMotion`.
- Produces: `Counter({ value: number })` (reduced-motion bo'lsa to'g'ridan-to'g'ri qiymat), `LanguageSwitch()` (3 tugma, `aria-pressed`), `SocialButton({ link: SocialLink })` (`<a>`, tashqi havolada `target`/`rel`; `mailto:` uchun `target` yo'q), `TiltCard({ children })` (pointer bilan 3D burilish; reduced-motion yoki touch'da burilmaydi).

- [ ] **Step 1:** Testlar: `Counter` reduced-motion'da darhol `value` ko'rsatadi; `LanguageSwitch` bosilganda til o'zgaradi va faol tugmada `aria-pressed="true"`; `SocialButton` `https` havolada `target="_blank"` va `rel="noopener noreferrer"`, `mailto:` da `target` yo'q va `aria-label` bor; `TiltCard` bolalarni chizadi va reduced-motion'da `transform` stil qo'shmaydi. FAIL.
- [ ] **Step 2:** Implementatsiya; `TiltCard` pointer pozitsiyasini `rotateX/Y` ga (max ±8°) aylantiradi. PASS; commit: `feat(portfolio): add shared components`.

### Task 5: Bo'limlar va App

**Files:**
- Create: `portfolio/src/sections/{Hero,About,Certificates,Website,Contact}.tsx`, `portfolio/src/sections/sections.test.tsx`; Modify: `portfolio/src/App.tsx`, `portfolio/src/main.tsx`

**Interfaces:**
- Consumes: `profile`, `useI18n`, `Counter`, `TiltCard`, `SocialButton`, `LanguageSwitch`.
- Produces: `App()` — `I18nProvider` ichida bo'limlar; bitta `<h1>` (Hero), qolgan bo'limlar `<h2>`, `id` angorlari bilan.

- [ ] **Step 1:** Testlar (`App` render): sahifada `Aziza Karimova` bitta `h1` ichida; 5 ta sertifikat kartasi nomi va ball bilan; sayt kartasi `href=profile.website.url`, `target="_blank"`, `rel` to'g'ri; kontaktda 4 ta ijtimoiy havola; sertifikatlar bo'sh (modul mock) bo'lsa `certs.empty` matni; juda uzun sertifikat nomi (200 belgi) bilan render xatosiz va kartada `overflow-wrap: anywhere` sinfi bor. FAIL.
- [ ] **Step 2:** Bo'limlarni yozing: Hero (ism, kasb, CTA angor), About (bio + `Counter` statistikalar), Certificates (TiltCard ro'yxat), Website (katta karta), Contact (SocialButton'lar). Til almashtirgich yuqori panelda.
- [ ] **Step 3:** PASS; lint; commit: `feat(portfolio): add page sections`.

### Task 6: 3D sahna

**Files:**
- Create: `portfolio/src/scene/{Scene,Shapes,Globe,useScrollCamera}.tsx|ts`, `portfolio/src/scene/SceneLayer.tsx`, `portfolio/src/scene/SceneLayer.test.tsx`; Modify: `portfolio/src/App.tsx`

**Interfaces:**
- Consumes: `useIsMobile`, `useReducedMotion`, `ErrorBoundary`.
- Produces: `SceneLayer()` — `React.lazy(() => import('./Scene'))` ni `Suspense` (skeleton fon) va `ErrorBoundary` (statik gradient fallback) ichida chizadi; `reduced-motion` bo'lsa sahnani umuman yuklamaydi; `Scene({ shapeCount, dpr })`: `Shapes` (suzuvchi shaffof ikosaedr/torus, `MeshTransmissionMaterial` yoki yengil `meshPhysicalMaterial`), `Globe` (sekin aylanuvchi), `useScrollCamera` (scroll → kamera Y/Z). Kanvas `aria-hidden`, `position: fixed`, `pointer-events: none`. Mobilda `shapeCount` 6, kompyuterda 14; `dpr` ≤ 1.5.

- [ ] **Step 1:** Testlar: reduced-motion'da `SceneLayer` canvas chizmaydi va fallback fon bor; `Scene` import xatosi (mock) bo'lsa ErrorBoundary fallback ko'rsatadi va `App` kontenti ko'rinib turadi; mobil/desktop uchun `shapeCount` qiymatlari (6/14) `SceneLayer` yordamchisidan to'g'ri qaytadi. FAIL.
- [ ] **Step 2:** Sahnani yozing (R3F testlarda mock; WebGL jsdom'da yo'q). Silliq harakat: `useFrame` + `lerp`, sikl 3-8 s.
- [ ] **Step 3:** PASS; `npm run build`, chunk o'lchamini yozib oling; commit: `feat(portfolio): add 3D scene with fallbacks`.

### Task 7: Uslub, qulaylik, tekshiruv va hujjat

**Files:**
- Create: `portfolio/src/styles/{tokens,global}.css`, `portfolio/README.md`, `portfolio/scripts/screenshots.mjs`; Modify: komponentlar `className`lari

- [ ] **Step 1:** CSS tokenlar (`--bg`, `--glass`, `--accent`, `--text` va dark gradient), glassmorphism kartalar, `:focus-visible` halqa, `overflow-wrap: anywhere`, 390px da `overflow-x: hidden` emas — gorizontal skroll chiqmasligi layout orqali ta'minlanadi. Kontrast AA (matn/fon ≥ 4.5:1).
- [ ] **Step 2:** `screenshots.mjs`: Playwright (`require('playwright')`) `vite preview` ustida 390×844 va 1440×900 skrinshotlar oladi va `document.documentElement.scrollWidth <= innerWidth` ni tekshiradi (390px da). Ishga tushiring; skrinshotlarni ko'rib chiqib dizaynni tuzating.
- [ ] **Step 3:** `README.md`: ishga tushirish, `profile.ts`ni almashtirish, joylashtirish (Vercel/Netlify/Cloudflare Pages).
- [ ] **Step 4:** To'liq tekshiruv: `npm test`, `npm run lint`, `npm run build` (oxirgi 15 qator); commit: `feat(portfolio): style, a11y checks and docs`; push.
