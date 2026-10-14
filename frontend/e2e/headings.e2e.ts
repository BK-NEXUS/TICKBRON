/**
 * QA (accessibility): every screen has exactly one h1. The brand in the header, the dashboard
 * tabs and the "sign in required" screens broke this (2-3 h1 on most pages, 0 on two).
 * Needs the seeded stack: python manage.py seed_demo
 */
import type { Page } from '@playwright/test'
import { DEMO, expect, loginWithPassword, logout, test } from './support'

const h1Count = (page: Page) => page.locator('h1').count()

async function expectOneH1(page: Page, where: string) {
  await page.waitForTimeout(800)
  expect(await h1Count(page), `${where} must have exactly one h1`).toBe(1)
}

test('HEADINGS public pages and sign-in-required screens have one h1', async ({ page }) => {
  for (const route of ['/', '/search', '/destinations', '/about', '/help', '/login', '/register', '/profile', '/bookings', '/favorites', '/admin', '/partner', '/no-such-page']) {
    await page.goto(route)
    await expectOneH1(page, `anonymous ${route}`)
  }
})

test('HEADINGS owner dashboard tabs have one h1', async ({ page }) => {
  await loginWithPassword(page, DEMO.owner.email, DEMO.owner.password)
  await page.goto('/partner')
  await expectOneH1(page, 'owner /partner')
  const tabs = page.locator('nav button.nav-item, [role=tab]')
  const count = Math.min(await tabs.count(), 4)
  for (let i = 0; i < count; i++) {
    await tabs.nth(i).click()
    await expectOneH1(page, `owner /partner tab ${i}`)
  }
  await logout(page)
})

test('HEADINGS admin dashboard views have one h1', async ({ page }) => {
  await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password)
  await page.goto('/admin')
  const nav = page.locator('nav button.nav-item')
  // 0-7: moderation, amenities, users, customers, statistics, status, advertising, no-show (8 and 9 leave or open a form)
  for (let i = 0; i < 8; i++) {
    await page.goto('/admin')
    await nav.nth(i).click()
    await expectOneH1(page, `admin view ${i}`)
  }
  await logout(page)
})
