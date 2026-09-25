import { defineConfig, devices } from '@playwright/test'

/**
 * Browser E2E tests against the real local stack (no mocked API):
 *   backend:  cd backend && venv\Scripts\python.exe manage.py seed_demo && venv\Scripts\python.exe manage.py runserver 8000
 *   frontend: npm run dev            (http://localhost:3000)
 *   tests:    npm run test:e2e
 * Screenshots (desktop 1440px + mobile 390px per step) and console/network logs go to e2e/screenshots/ (gitignored).
 */
export default defineConfig({
  testDir: './e2e',
  testMatch: '**/*.e2e.ts',
  globalSetup: './e2e/global-setup.ts',
  // The flows share one database and some depend on each other (e.g. F looks up A's booking)
  workers: 1,
  fullyParallel: false,
  timeout: 120_000,
  expect: { timeout: 10_000 },
  outputDir: 'e2e/test-results',
  reporter: [['list'], ['json', { outputFile: 'e2e/test-results/results.json' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:3000',
    viewport: { width: 1440, height: 900 },
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    actionTimeout: 15_000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } } }],
})
