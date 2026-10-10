/**
 * Owner calendar against the real local stack (seed_demo): open a room type's calendar, close and
 * reopen a range, change the price of a range, and take rooms out of sale with an external booking.
 * Every step is checked against the API as well as on screen.
 */
import { test, expect, step, loginWithPassword, API, DEMO } from './support'

/** The 10th to the 12th of next month: always in the future, and the same month in the grid and the API. */
function nextMonthDays() {
  const now = new Date()
  const first = new Date(now.getFullYear(), now.getMonth() + 1, 1)
  const month = `${first.getFullYear()}-${String(first.getMonth() + 1).padStart(2, '0')}`
  return { from: `${month}-10`, to: `${month}-13`, last: `${month}-12` }
}

test('K owner calendar: close, price and external booking', async ({ page, audit }) => {
  const { from, to, last } = nextMonthDays()
  const cell = (date: string) => page.locator(`[data-date="${date}"]`)
  let roomTypeId = 0

  async function inventory(date: string) {
    const response = await page.request.get(`${API}/api/v1/partner/room-inventory/?room_type=${roomTypeId}&date_from=${date}&date_to=${date}`)
    expect(response.ok()).toBeTruthy()
    const body = await response.json()
    return (body.results ?? body)[0] as { is_available: boolean; remaining_rooms: number; available_rooms: number } | undefined
  }

  async function pickRange() {
    await cell(from).click()
    await cell(to).click()
  }

  await step(audit, 'K1 open-the-calendar', async () => {
    await loginWithPassword(page, DEMO.owner.email, DEMO.owner.password)
    await page.goto('/partner')
    await page.getByRole('button', { name: /^Manage .*Tashkent/i }).first().click()
    await page.getByRole('button', { name: /^Manage calendar for Deluxe King/ }).first().click()
    await expect(page.getByRole('heading', { name: 'Calendar for Deluxe King' })).toBeVisible()
    const rooms = await page.request.get(`${API}/api/v1/partner/rooms/`)
    const list = await rooms.json()
    roomTypeId = (list.results ?? list).find((room: { name: string }) => room.name === 'Deluxe King').id
    await expect(page.locator('.partner-calendar-summary')).toContainText('room-nights free this month')
  })

  await step(audit, 'K2 next-month-loads-its-own-days', async () => {
    await page.getByRole('button', { name: 'Next month' }).click()
    await expect(cell(from)).toBeVisible()
    await expect(page.locator('.partner-calendar-summary')).toContainText('room-nights free this month')
  })

  await step(audit, 'K3 close-a-range', async () => {
    await pickRange()
    await page.getByRole('button', { name: 'Close these days' }).click()
    await expect(page.getByText(/^Saved /)).toBeVisible()
    await expect(page.locator('.partner-calendar-summary')).toContainText('3 closed days')
    expect((await inventory(from))?.is_available).toBe(false)
    expect((await inventory(last))?.is_available).toBe(false)
    expect((await inventory(to))?.is_available ?? true).toBe(true)
  })

  await step(audit, 'K4 open-the-range-again', async () => {
    await pickRange()
    await page.getByRole('button', { name: 'Open these days' }).click()
    await expect(page.getByText(/^Saved /)).toBeVisible()
    await expect(page.locator('.partner-calendar-summary')).not.toContainText('closed day')
    expect((await inventory(from))?.is_available).toBe(true)
  })

  await step(audit, 'K5 change-the-price-of-a-range', async () => {
    await expect(page.getByLabel('Prices for')).toBeVisible()
    await pickRange()
    await page.getByLabel(/^Price per night for these days/).fill('123')
    await page.getByRole('button', { name: 'Set price' }).click()
    await expect(page.getByText(/^Price updated for /)).toBeVisible()
    await expect(cell(from).locator('.partner-calendar-day-price')).toContainText('123')
    await expect(cell(last).locator('.partner-calendar-day-price')).toContainText('123')
    await expect(cell(to).locator('.partner-calendar-day-price')).not.toContainText('123')
  })

  await step(audit, 'K6 external-booking-takes-a-room-out-and-can-be-removed', async () => {
    const before = (await inventory(from))?.remaining_rooms ?? 0
    await page.getByRole('button', { name: 'External booking for Deluxe King' }).click()
    const dialog = page.getByRole('dialog')
    await dialog.getByLabel('From *').fill(from)
    await dialog.getByLabel('To (exclusive) *').fill(to)
    await dialog.getByLabel('Rooms *').fill('1')
    await dialog.getByLabel('Note *').fill('Booking.com test')
    await dialog.getByRole('button', { name: 'Create block' }).click()
    await expect(page.getByText('Booking.com test').first()).toBeVisible()
    expect((await inventory(from))?.remaining_rooms).toBe(before - 1)

    page.once('dialog', (confirm) => confirm.accept())
    await page.getByRole('button', { name: /Remove block Booking\.com test/ }).click()
    await expect(page.getByRole('button', { name: /Remove block Booking\.com test/ })).toHaveCount(0)
    expect((await inventory(from))?.remaining_rooms).toBe(before)
  })
})
