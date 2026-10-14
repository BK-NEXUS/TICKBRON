/**
 * QA: admin and owner screens must not scroll sideways at phone width (390px).
 * The 12-month registrations chart pushed the Statistics page 45px wider than the screen.
 * Needs the seeded stack: python manage.py seed_demo && python manage.py seed_demo_stats
 */
import { DEMO, MOBILE, expect, loginWithPassword, test } from './support'

const LANGUAGES = ['en', 'ru', 'uz'] as const

for (const language of LANGUAGES) {
  test(`MOBILE admin Statistics fits 390px (${language})`, async ({ page }) => {
    await page.setViewportSize(MOBILE)
    await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password) // the helper uses the English labels
    await page.evaluate((lang) => localStorage.setItem('tickbron.language', lang), language)
    await page.goto('/admin')
    await page.locator('nav button.nav-item').nth(4).click() // Statistics
    await expect(page.locator('.bar-chart').first()).toBeVisible()

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow).toBeLessThanOrEqual(1)
  })
}

// The customers table has many columns; with Russian headers it was 48px wider than a 1440px screen
for (const [name, viewport] of [['desktop', { width: 1440, height: 900 }], ['phone', MOBILE]] as const) {
  test(`LAYOUT admin Customers table fits the ${name} screen (ru)`, async ({ page }) => {
    await page.setViewportSize(viewport)
    await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password)
    await page.evaluate(() => localStorage.setItem('tickbron.language', 'ru'))
    await page.goto('/admin')
    await page.locator('nav button.nav-item').nth(3).click() // Customers
    await expect(page.locator('.customers-table')).toBeVisible()

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)
    expect(overflow).toBeLessThanOrEqual(1)
  })
}
