import { test as base, expect, Page, TestInfo } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const API = process.env.E2E_API_URL || 'http://localhost:8000'
export const SCREENSHOT_DIR = path.join(path.dirname(fileURLToPath(import.meta.url)), 'screenshots')

export const DESKTOP = { width: 1440, height: 900 }
export const MOBILE = { width: 390, height: 844 }

// Accounts created by `python manage.py seed_demo`
export const DEMO = {
  admin: { email: 'admin@tickbron.demo', password: 'DemoAdmin#2026', phone: '+998900000001' },
  owner: { email: 'owner@tickbron.demo', password: 'DemoOwner#2026', phone: '+998900000002' },
  guest: { email: 'guest@tickbron.demo', password: 'DemoGuest#2026', phone: '+998900000003' },
}

export interface Issue {
  step: string
  kind: 'console' | 'http' | 'requestfailed' | 'pageerror'
  message: string
  url?: string
  status?: number
}

/** Collects console errors and failed requests per step and takes desktop + mobile screenshots. */
export class Audit {
  readonly issues: Issue[] = []
  readonly screenshots: string[] = []
  private currentStep = 'setup'
  private shotIndex = 0
  private readonly dir: string

  constructor(private readonly page: Page, testInfo: TestInfo) {
    const flow = testInfo.title.split(' ')[0].replace(/[^A-Za-z0-9-]/g, '')
    this.dir = path.join(SCREENSHOT_DIR, flow)
    // Start each run with an empty folder so old screenshots do not mix in
    fs.rmSync(this.dir, { recursive: true, force: true })
    fs.mkdirSync(this.dir, { recursive: true })

    page.on('console', (msg) => {
      if (msg.type() === 'error') this.issues.push({ step: this.currentStep, kind: 'console', message: msg.text() })
    })
    page.on('pageerror', (err) => {
      this.issues.push({ step: this.currentStep, kind: 'pageerror', message: err.message })
    })
    page.on('response', (response) => {
      if (response.status() >= 400) {
        this.issues.push({
          step: this.currentStep, kind: 'http', status: response.status(),
          url: response.url(), message: `${response.request().method()} ${response.status()}`,
        })
      }
    })
    page.on('requestfailed', (request) => {
      this.issues.push({
        step: this.currentStep, kind: 'requestfailed', url: request.url(),
        message: `${request.method()} ${request.failure()?.errorText ?? 'failed'}`,
      })
    })
  }

  /** Name the step that following console/network events belong to. */
  step(name: string) {
    this.currentStep = name
  }

  /** Full-page screenshot at 1440px and 390px, then back to desktop. */
  async shot(name: string) {
    this.shotIndex += 1
    const base = `${String(this.shotIndex).padStart(2, '0')}-${name.replace(/[^A-Za-z0-9-]+/g, '-')}`
    await this.page.waitForLoadState('networkidle').catch(() => undefined)
    const desktop = path.join(this.dir, `${base}-desktop.png`)
    await this.page.screenshot({ path: desktop, fullPage: true })
    await this.page.setViewportSize(MOBILE)
    await this.page.waitForTimeout(400)
    const mobile = path.join(this.dir, `${base}-mobile.png`)
    await this.page.screenshot({ path: mobile, fullPage: true })
    await this.page.setViewportSize(DESKTOP)
    await this.page.waitForTimeout(200)
    this.screenshots.push(desktop, mobile)
  }

  write() {
    fs.writeFileSync(
      path.join(this.dir, 'issues.json'),
      JSON.stringify({ issues: this.issues, screenshots: this.screenshots }, null, 2),
    )
  }
}

export const test = base.extend<{ audit: Audit }>({
  audit: async ({ page }, use, testInfo) => {
    const audit = new Audit(page, testInfo)
    await use(audit)
    audit.write()
  },
})

export { expect }

/** Run a named step: events are tagged with its name and a screenshot pair is taken at the end. */
export async function step(audit: Audit, name: string, body: () => Promise<void>) {
  await test.step(name, async () => {
    audit.step(name)
    try {
      await body()
    } finally {
      await audit.shot(name.split(' ')[0] + '-' + name.split(' ').slice(1).join('-'))
    }
  })
}

/** Log in through the login page with email and password. */
export async function loginWithPassword(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Email', { exact: true }).fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: /sign in/i }).click()
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15_000 })
}

/** Log out through the API with the page's cookies (keeps the flows independent). */
export async function logout(page: Page) {
  await page.context().clearCookies()
}

/** YYYY-MM-DD in local time. */
export function localDate(offsetDays = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
