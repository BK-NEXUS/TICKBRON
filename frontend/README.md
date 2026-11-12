# TICKBRON Frontend

TICKBRON mehmanxana bronlaw platforması ushın React + TypeScript + Vite frontend ilovası.

## Tech Stack

- **React 19** - UI kitapxanası
- **TypeScript** - Tip qáwipsizligi
- **Vite** - Build quralı hám dev server
- **React Router** - Client tárepindegi routing
- **Vitest** - Testlew framework'i
- **Testing Library** - Komponentlerdi testlew
- **Leaflet** - Kartalar

## Aldın ala talaplar (Prerequisites)

- Node.js 22 (18+ de isleydi)
- npm

## Ornatıw (Installation)

```bash
npm ci
```

## Development

```bash
# Development server'di iske túsiriw
npm run dev
```

Ilova `http://localhost:3000` mánzilinde ashıladı. `/api` sorawları backend'ke (`http://localhost:8000`) proxy arqalı jiberiledi, sonıń ushın `VITE_API_BASE_URL` bos qaldırıladı (cookie hám CSRF bir domen menen isleydi).

## Build

```bash
npm run build
```
Build aldın `tsc` penen tip tekseredi.

## Testlew

```bash
# Testlerdi isletiw
npm run test

# UI menen
npm run test:ui

# Coverage menen
npm run test:coverage
```
Windows'ta test worker'ler qulap qalsa: `npx vitest run --maxWorkers=6`.

## Lint

```bash
npm run lint
```

## Proekt dúzilisi (Project Structure)

```
frontend/
├── public/              # Statik fayllar (logo, manifest, service worker, assetlinks)
├── src/
│   ├── adapters/        # Backend API menen baylanıs
│   ├── components/      # Qayta paydalanılatuǵın UI komponentler
│   ├── i18n/            # Awdarmalar (uz, ru, en)
│   ├── layout/          # Layout komponentler
│   ├── pages/           # Bet komponentler
│   ├── styles/          # Global stiller hám CSS
│   ├── types/           # TypeScript tip anıqlamaları
│   ├── utils/           # Járdemshi funkciyalar
│   ├── test/            # Test sazlamaları
│   ├── App.tsx          # Root komponent
│   └── main.tsx         # Ilovanıń kirisiw noqatı
├── index.html           # HTML úlgisi
├── package.json         # Dependency'ler hám script'ler
├── tsconfig.json        # TypeScript sazlamaları
├── vite.config.ts       # Vite sazlamaları
└── README.md            # Usı fayl
```

## Environment variable'lar

`.env.example` tiykarında `.env` jaratıń (kóbinese kerek emes):

```bash
cp .env.example .env
```

## API menen integraciya

Frontend API sorawların backend'ke proxy etedi:

- Development: Vite proxy arqalı `http://localhost:8000/api/v1`
- Production: `VITE_API_BASE_URL` arqalı sazlanadı (Docker build'te saytıń óz domeni)

Barlıq API contract `.ai/API_CONTRACT.md` faylında jazılǵan.

## Qáwipsizlik (Security Considerations)

- Session tiykarındaǵı authentication, qáwipsiz cookie'ler menen (HttpOnly, Secure, SameSite)
- CSRF qorǵawı qosılǵan
- localStorage'de JWT saqlanbaydı
- Sezimtal sazlamalar environment variable'larda
- Content Security Policy header'leri server tárepinen beriledi (`deploy/Caddyfile`, `deploy/nginx.conf.example`)

## Brauzerlerdi qollap-quwatlaw (Browser Support)

- Chrome (sońǵı)
- Firefox (sońǵı)
- Safari (sońǵı)
- Edge (sońǵı)

Ilova Android'te Chrome arqalı ornatılatuǵın PWA retinde de isleydi (`public/manifest.webmanifest`).

## Qatnasıw (Contributing)

Bul TICKBRON proektiniń bir bólegi. Jumıs tártibi ushın `.ai/` papkasındaǵı `README.md` faylın oqıń.
