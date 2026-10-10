/**
 * Hotel promotions (R10) against the real local stack. Needs `seed_demo` and `seed_demo_stats`
 * (the second one creates running, unpaid and expired demo promotions).
 * Banner on home and search, the click counter, and the super-admin Advertising screen.
 */
import { test, expect, step, loginWithPassword, logout, API, DEMO } from './support'

test('J promotion banner and the admin advertising screen', async ({ page, audit }) => {
  const banner = page.getByRole('region', { name: 'Featured hotels' })

  await step(audit, 'J1 home-banner', async () => {
    await page.goto('/')
    await expect(banner).toBeVisible()
    await expect(banner.getByText('Ad', { exact: true }).first()).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Find Your Perfect Stay' })).toBeVisible()
  })

  await step(audit, 'J2 banner-rotates-with-the-arrows', async () => {
    const first = await banner.locator('.promo-slide--active .promo-slide-name').innerText()
    await banner.getByRole('button', { name: 'Next banner' }).click()
    await expect(banner.locator('.promo-slide--active .promo-slide-name')).not.toHaveText(first)
  })

  await step(audit, 'J3 search-banner-above-filters-and-two-columns', async () => {
    await page.goto('/search')
    await expect(banner).toBeVisible()
    const bannerBox = await banner.boundingBox()
    const filtersBox = await page.locator('.search-results-sidebar').boundingBox()
    expect(bannerBox && filtersBox && bannerBox.y + bannerBox.height <= filtersBox.y).toBeTruthy()
    await expect(page.locator('.search-results-grid .property-card').first()).toBeVisible()
    const columns = await page.locator('.search-results-grid').evaluate(
      (grid) => getComputedStyle(grid).gridTemplateColumns.split(' ').length,
    )
    expect(columns).toBe(2)
  })

  await step(audit, 'J4 banner-click-opens-the-hotel-and-is-counted', async () => {
    const promotionId = await page.evaluate(async (api) => {
      const home = await (await fetch(`${api}/api/v1/promotions/home/`)).json()
      return home.results[0].promotion_id as number
    }, API)
    await page.goto('/')
    const clicked = page.waitForRequest((request) => request.url().endsWith('/click/') && request.method() === 'POST')
    await banner.locator('.promo-slide--active a').click()
    expect((await clicked).url()).toContain('/api/v1/promotions/')
    await expect(page).toHaveURL(/\/property\/\d+/)
    expect(promotionId).toBeGreaterThan(0)
  })

  await step(audit, 'J5 admin-finds-a-hotel-and-sees-the-list', async () => {
    await logout(page)
    await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password)
    await page.goto('/admin')
    await page.getByRole('button', { name: 'Advertising' }).click()
    await expect(page.getByRole('heading', { name: 'Advertising' })).toBeVisible()
    await expect(page.getByRole('table').first()).toBeVisible()
    await page.getByLabel('Find a hotel by name').fill('demo old town')
    await expect(page.getByRole('button', { name: /Promote TICKBRON Demo Old Town/ })).toBeEnabled()
  })

  await step(audit, 'J6 admin-opens-statistics-of-a-running-promotion', async () => {
    // A running promotion has daily numbers (an unpaid one has none and shows an empty message)
    await page.getByRole('row').filter({ hasText: 'Shown now' }).first().getByRole('button', { name: 'Statistics' }).click()
    const dialog = page.getByRole('dialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByRole('table')).toBeVisible()
    await dialog.getByRole('button', { name: 'Close' }).click()
    await expect(dialog).toHaveCount(0)
  })
})
