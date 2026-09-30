/**
 * Status sections (Status plan S8), against the real local stack with demo data:
 *   backend: python manage.py seed_demo && python manage.py seed_demo_stats
 *
 * - the admin drills down Countries > Uzbekistan > Tashkent > a hotel, and the numbers match the API
 * - the admin searches a guest in Users and opens the customer profile
 * - a hotel owner sees only their own hotel's numbers
 */
import type { Page } from '@playwright/test'
import { API, DEMO, expect, loginWithPassword, logout, step, test } from './support'

// Accounts and hotel created by `python manage.py seed_demo_stats`
const STATS_OWNER = { email: 'stats-owner-01@tickbron.demo', password: 'DemoStats#2026' }
const STATS_GUEST_EMAIL = 'stats-guest-01@tickbron.demo'
const OWN_HOTEL = 'Silk Road Plaza Hotel' // stats-owner-01's hotel (Uzbekistan, Tashkent)
const OTHER_HOTEL = 'Chorsu Garden Inn' // another owner's hotel in the same region

const count = (value: number) => value.toLocaleString('en-US')
// The layout's trail (the admin dashboard also has its own older one-level breadcrumb)
const TRAIL = '.page-breadcrumbs'

/** Value of the summary card with exactly this label */
const cardValue = (page: Page, label: string) => page.locator('.status-card')
  .filter({ has: page.locator('.status-card-label', { hasText: new RegExp(`^${label}$`) }) })
  .locator('.status-card-value')

test('STATUS admin drill-down, users search, owner sees only own numbers', async ({ page, audit }) => {
  await step(audit, 'S1 admin-status-countries', async () => {
    await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password)
    await page.goto('/admin')
    await page.getByRole('button', { name: 'Status', exact: true }).click()
    await expect(page.getByRole('heading', { name: 'Status', exact: true })).toBeVisible()
    await page.getByRole('button', { name: /^Countries/ }).click()
    await expect(page.getByRole('button', { name: 'Uzbekistan', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Kazakhstan', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Turkey', exact: true })).toBeVisible()
  })

  await step(audit, 'S2 admin-status-regions', async () => {
    await page.getByRole('button', { name: 'Uzbekistan', exact: true }).click()
    await expect(page.getByRole('button', { name: 'Tashkent', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Samarkand', exact: true })).toBeVisible()
  })

  await step(audit, 'S3 admin-status-hotels', async () => {
    await page.getByRole('button', { name: 'Tashkent', exact: true }).click()
    await expect(page.getByRole('button', { name: OWN_HOTEL })).toBeVisible()
    // The search box searches this list only
    await page.getByLabel('Search hotels').fill('Silk')
    await expect(page.getByRole('button', { name: OTHER_HOTEL })).toHaveCount(0)
    await expect(page.getByRole('button', { name: OWN_HOTEL })).toBeVisible()
  })

  await step(audit, 'S4 admin-status-hotel-detail', async () => {
    await page.getByRole('button', { name: OWN_HOTEL }).click()
    await expect(page.getByRole('heading', { name: OWN_HOTEL })).toBeVisible()
    await expect(page.locator(TRAIL))
      .toContainText(`Status›Countries›Uzbekistan›Tashkent›${OWN_HOTEL}`)
    await expect(page.getByRole('img', { name: /Revenue \(USD\) per month in \d{4}/ })).toBeVisible()
    await expect(page.getByRole('img', { name: /Guests per month in \d{4}/ })).toBeVisible()
    await expect(page.getByText('Akmal Karimov')).toBeVisible()

    // The numbers on screen are the API's numbers
    const hotels = await (await page.request.get(
      `${API}/api/v1/admin-panel/status/countries/Uzbekistan/regions/Tashkent/hotels/?search=Silk`)).json()
    const detail = await (await page.request.get(
      `${API}/api/v1/admin-panel/status/hotels/${hotels.results[0].id}/`)).json()
    expect(detail.totals.bookings).toBeGreaterThan(0)
    const bookingsCard = cardValue(page, 'Bookings')
    await expect(bookingsCard).toHaveText(count(detail.totals.bookings))
  })

  await step(audit, 'S5 back-steps-up', async () => {
    await page.getByRole('button', { name: 'Back' }).click()
    await expect(page.getByRole('button', { name: OWN_HOTEL })).toBeVisible()
    await page.getByRole('button', { name: 'Back' }).click()
    await expect(page.getByRole('button', { name: 'Tashkent', exact: true })).toBeVisible()
  })

  await step(audit, 'S6 admin-status-users-search', async () => {
    await page.locator(TRAIL).getByRole('button', { name: 'Status', exact: true }).click()
    await page.getByRole('button', { name: /^Users/ }).click()
    await expect(page.getByRole('table')).toBeVisible()
    await page.getByLabel('Search users').fill('stats-guest-01@')
    const row = page.getByRole('row').filter({ hasText: STATS_GUEST_EMAIL })
    await expect(row).toHaveCount(1)
    await expect(page.getByRole('row')).toHaveCount(2) // header + the one guest
    await row.click()
    await expect(page).toHaveURL(/\/admin\/customers\/\d+$/)
    await expect(page.getByText(STATS_GUEST_EMAIL).first()).toBeVisible()
  })

  await step(audit, 'S7 owner-sees-only-own-numbers', async () => {
    await logout(page)
    await loginWithPassword(page, STATS_OWNER.email, STATS_OWNER.password)
    await page.goto('/partner')
    await page.getByRole('button', { name: 'Status', exact: true }).click()
    const table = page.getByRole('table', { name: 'Your properties' })
    await expect(table).toBeVisible()
    await expect(table.getByRole('row')).toHaveCount(2) // header + the owner's one hotel
    await expect(table.getByText(OWN_HOTEL)).toBeVisible()
    await expect(page.getByText(OTHER_HOTEL)).toHaveCount(0)
    await expect(page.getByText('On TICKBRON since')).toBeVisible()
    await expect(page.getByRole('img', { name: /Guests per month in \d{4}/ })).toBeVisible()

    const own = await (await page.request.get(`${API}/api/v1/partner/status/`)).json()
    expect(own.properties.map((p: { name: string }) => p.name)).toEqual([OWN_HOTEL])
    const bookingsCard = cardValue(page, 'Bookings')
    await expect(bookingsCard).toHaveText(count(own.totals.bookings))

    // The admin Status API is closed to hotel owners
    const adminApi = await page.request.get(`${API}/api/v1/admin-panel/status/countries/`)
    expect(adminApi.status()).toBe(403)
  })
})
