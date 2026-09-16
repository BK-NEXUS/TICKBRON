# TICKBRON Frontend

React + TypeScript + Vite frontend application for TICKBRON short-term rental platform.

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Vitest** - Testing framework
- **Testing Library** - Component testing

## Prerequisites

- Node.js 18+ 
- npm, yarn, or pnpm

## Installation

```bash
# Install dependencies
npm install
# or
yarn install
# or
pnpm install
```

## Development

```bash
# Start development server
npm run dev
# or
yarn dev
# or
pnpm dev
```

The application will be available at `http://localhost:3000`.

## Build

```bash
# Build for production
npm run build
# or
yarn build
# or
pnpm build
```

## Testing

```bash
# Run tests
npm run test
# or
yarn test
# or
pnpm test

# Run tests with UI
npm run test:ui
# or
yarn test:ui
# or
pnpm test:ui

# Run tests with coverage
npm run test:coverage
# or
yarn test:coverage
# or
pnpm test:coverage
```

## Linting

```bash
# Run ESLint
npm run lint
# or
yarn lint
# or
pnpm lint
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable UI components
│   ├── layout/          # Layout components
│   ├── pages/           # Page components
│   ├── styles/          # Global styles and CSS
│   ├── types/           # TypeScript type definitions
│   ├── utils/           # Utility functions
│   ├── test/            # Test configuration
│   ├── App.tsx          # Root component
│   └── main.tsx         # Application entry point
├── index.html           # HTML template
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript configuration
├── vite.config.ts       # Vite configuration
└── README.md            # This file
```

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

## API Integration

The frontend is configured to proxy API requests to the backend:

- Development: `http://localhost:8000/api/v1`
- Production: Configured via `VITE_API_BASE_URL`

Note: API endpoints are not yet implemented. The frontend structure is ready for integration when backend APIs become available.

## Security Considerations

- Session-based authentication with secure cookies (HttpOnly, Secure, SameSite)
- CSRF protection enabled
- No JWT storage in localStorage
- Environment variables for sensitive configuration
- Content Security Policy headers (to be configured in production)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

This is part of the TICKBRON project. Follow the checkpoint protocol in `.ai/` for development workflow.
