/**
 * Back button and breadcrumbs (Phase 2 item 4) against the real local stack (seed_demo data):
 * Home › Tashkent › Hotel, and going back to the results keeps the search filters.
 */
import { test, expect, step } from './support'

const TASHKENT = 'TICKBRON Demo Hotel Tashkent'

test('I breadcrumbs and back keep the search filters', async ({ page, audit }) => {
  const trail = page.getByRole('navigation', { name: 'Breadcrumb' })

  await step(audit, 'I1 home-has-no-breadcrumbs', async () => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Find Your Perfect Stay' })).toBeVisible()
    await expect(trail).toHaveCount(0)
  })

  await step(audit, 'I2 search-with-a-filter', async () => {
    await page.goto('/search?destination=Tashkent')
    // The filter lives in the URL: the box is ticked a moment after the click, so wait for it instead of reading it at once
    await page.getByLabel('WiFi').click()
    await expect(page.getByLabel('WiFi')).toBeChecked()
    await page.getByLabel('Sort search results').selectOption('price_asc')
    await expect(page).toHaveURL(/features=wifi/)
    await expect(page).toHaveURL(/sort=price_asc/)
    await expect(trail).toContainText('Tashkent')
  })

  await step(audit, 'I3 property-trail', async () => {
    await page.getByRole('button', { name: new RegExp(`${TASHKENT} in Tashkent`) }).click()
    await expect(page.getByRole('heading', { level: 1, name: TASHKENT })).toBeVisible()
    await expect(trail.getByRole('link', { name: 'Home' })).toBeVisible()
    await expect(trail.getByRole('link', { name: 'Tashkent' })).toBeVisible()
    await expect(trail.getByText(TASHKENT)).toHaveAttribute('aria-current', 'page')
  })

  await step(audit, 'I4 city-crumb-keeps-filters', async () => {
    await trail.getByRole('link', { name: 'Tashkent' }).click()
    await expect(page).toHaveURL(/\/search\?.*features=wifi/)
    await expect(page).toHaveURL(/sort=price_asc/)
    await expect(page.getByLabel('WiFi')).toBeChecked()
    await expect(page.getByLabel('Sort search results')).toHaveValue('price_asc')
  })

  await step(audit, 'I5 back-button-keeps-filters', async () => {
    await page.getByRole('button', { name: new RegExp(`${TASHKENT} in Tashkent`) }).click()
    await expect(page.getByRole('heading', { level: 1, name: TASHKENT })).toBeVisible()
    await page.getByRole('button', { name: 'Back' }).click()
    await expect(page).toHaveURL(/\/search\?.*features=wifi/)
    await expect(page.getByLabel('WiFi')).toBeChecked()
  })
})
