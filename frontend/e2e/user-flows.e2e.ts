/**
 * User flows A-H against the real local stack (seed_demo data).
 * No mocked API, with two documented exceptions:
 *  - B intercepts one /confirm/ call, because test-mode payments always succeed.
 *  - C and E fall back to the real API where the UI has no control for the step.
 * Every step takes a desktop + mobile screenshot and logs console errors / failed requests
 * to e2e/screenshots/<flow>/issues.json. expect.soft marks a finding without stopping the flow.
 */
import { Page } from '@playwright/test'
import fs from 'node:fs'
import path from 'node:path'
import { test, expect, step, loginWithPassword, logout, DEMO, localDate, API, SCREENSHOT_DIR } from './support'

// Shared between flows (A creates the booking that F looks up). Kept in a file because
// Playwright starts a new worker after a failed test, which clears module state.
const SHARED_FILE = path.join(SCREENSHOT_DIR, 'shared.json')
type SharedState = { referenceCode?: string; propertyId?: number; ratePlanId?: number }
function readShared(): SharedState {
  try { return JSON.parse(fs.readFileSync(SHARED_FILE, 'utf-8')) } catch { return {} }
}
function writeShared(update: SharedState) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true })
  fs.writeFileSync(SHARED_FILE, JSON.stringify({ ...readShared(), ...update }))
}
const shared = {
  get referenceCode() { return readShared().referenceCode },
  set referenceCode(referenceCode: string | undefined) { writeShared({ referenceCode }) },
}

const TASHKENT = 'TICKBRON Demo Hotel Tashkent'

function addDays(date: string, days: number) {
  const [y, m, d] = date.split('-').map(Number)
  const next = new Date(y, m - 1, d + days)
  return `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}-${String(next.getDate()).padStart(2, '0')}`
}

/** Friday or Saturday night (seed_demo prices them 15% higher) */
function isWeekendNight(date: string) {
  const [y, m, d] = date.split('-').map(Number)
  return [5, 6].includes(new Date(y, m - 1, d).getDay())
}

/**
 * Pick room, rate, then a check-in and check-out in the calendar. The stay is the
 * `skip`-th run of `nights` open nights in the month on screen (with a weekend night
 * when asked). Returns the dates and the "N nights, total $X" text from the page.
 */
async function pickStay(page: Page, roomName: string, rateName: string,
  { nights = 2, skip = 0, weekend = false }: { nights?: number; skip?: number; weekend?: boolean } = {}) {
  await page.getByRole('button', { name: new RegExp(`^${roomName}`) }).click()
  await page.getByText(rateName, { exact: true }).first().click()
  const open = page.locator('.availability-calendar-day[aria-disabled="false"]')
  const findStays = async () => {
    await expect(open.first()).toBeVisible()
    const openDates = new Set(await open.evaluateAll(cells => cells.map(cell => cell.getAttribute('data-date') ?? '')))
    return [...openDates].sort().filter(start => {
      const stay = Array.from({ length: nights }, (_, i) => addDays(start, i))
      return stay.every(night => openDates.has(night)) && (!weekend || stay.some(isWeekendNight))
    })
  }
  let candidates = await findStays()
  if (!candidates[skip]) {
    // Near the end of a month the stay may only fit in the next one
    await page.getByRole('button', { name: 'Next month' }).click()
    candidates = await findStays()
  }
  const checkIn = candidates[skip]
  expect(checkIn, `an open ${nights}-night stay${weekend ? ' with a weekend night' : ''} this month or next`).toBeTruthy()
  const checkOut = addDays(checkIn, nights)

  await page.locator(`.availability-calendar-day[data-date="${checkIn}"]`).click()
  const checkOutCell = page.locator(`.availability-calendar-day[data-date="${checkOut}"]`)
  if (!(await checkOutCell.count())) await page.getByRole('button', { name: 'Next month' }).click()
  await checkOutCell.click()

  const totalText = page.getByText(/^\d+ nights?, total /)
  await expect(totalText).toBeVisible()
  return { checkIn, checkOut, totalText: (await totalText.textContent()) ?? '' }
}

/** "2 nights, total $129" -> 129 */
function totalFrom(text: string) {
  const match = text.replace(/,/g, '').match(/\$\s*([\d.]+)/)
  return match ? Number(match[1]) : NaN
}

/** Dollar amount in the parent row of a label, e.g. "Total $60" -> 60 */
async function amountNextTo(page: Page, label: string | RegExp) {
  const text = await page.getByText(label).first().locator('..').innerText()
  const match = text.replace(/,/g, '').match(/\$\s*([\d.]+)/)
  return match ? Number(match[1]) : NaN
}

/** Call the backend with the page's session cookies (for steps the UI does not offer). */
async function api(page: Page, method: string, path: string, data?: unknown) {
  const csrf = await (await page.request.get(`${API}/api/v1/auth/csrf/`)).json()
  return page.request.fetch(`${API}${path}`, {
    method,
    data,
    headers: { 'X-CSRFToken': csrf.csrf_token, 'Content-Type': 'application/json' },
  })
}

async function tashkentIds(page: Page) {
  // Cached: anonymous API calls count toward the 100/hour anon throttle
  const cached = readShared()
  if (cached.propertyId && cached.ratePlanId) return { propertyId: cached.propertyId, ratePlanId: cached.ratePlanId }
  const searchResponse = await page.request.get(`${API}/api/v1/properties/search/?destination=Tashkent`)
  if (!searchResponse.ok()) throw new Error(`search API ${searchResponse.status()}: ${(await searchResponse.text()).slice(0, 200)}`)
  const search = await searchResponse.json()
  const property = search.results.find((p: { city: string }) => p.city === 'Tashkent')
  const detail = await (await page.request.get(`${API}/api/v1/properties/${property.id}/`)).json()
  const room = detail.room_types.find((r: { name: string }) => r.name === 'Standard Double')
  const rate = room.rate_plans.find((r: { name: string }) => r.name === 'Standard Rate')
  const ids = { propertyId: property.id as number, ratePlanId: rate.id as number }
  writeShared(ids)
  return ids
}

/** A date in the month the calendar opens on (the current month). */
function dateInCurrentMonth(preferredOffset: number) {
  const preferred = localDate(preferredOffset)
  return preferred.slice(0, 7) === localDate(0).slice(0, 7) ? preferred : localDate(0)
}

async function fillBookingFormAndPay(page: Page) {
  await expect(page.getByRole('heading', { name: 'Complete Your Booking' })).toBeVisible()
  const firstName = page.getByLabel(/first name/i)
  const lastName = page.getByLabel(/last name/i)
  if (!(await firstName.inputValue())) await firstName.fill('Demo')
  if (!(await lastName.inputValue())) await lastName.fill('Guest')
  await page.getByRole('button', { name: /continue to payment/i }).click()
  await expect(page.getByRole('heading', { level: 1, name: 'Payment Method' })).toBeVisible()
  await page.getByRole('radio').first().click()
  await page.getByRole('button', { name: /^Pay with/ }).click()
}

test('A guest books a room and pays in test mode', async ({ page, audit }) => {
  await step(audit, 'A0 login-as-guest', async () => {
    await loginWithPassword(page, DEMO.guest.email, DEMO.guest.password)
  })

  await step(audit, 'A1 home', async () => {
    await page.goto('/')
    await expect(page.getByRole('heading', { name: 'Find Your Perfect Stay' })).toBeVisible()
  })

  await step(audit, 'A2 search-tashkent', async () => {
    await page.getByRole('textbox', { name: 'Destination' }).fill('Tashkent')
    await page.getByRole('button', { name: 'Search', exact: true }).click()
    // UX check: a city-only search should work; record if dates are forced
    await expect.soft(page, 'city-only search should open results').toHaveURL(/\/search/, { timeout: 3_000 })
    if (!page.url().includes('/search')) {
      await audit.shot('A2-city-only-search-blocked')
      await page.getByLabel('Check-in').fill(localDate(3))
      await page.getByLabel('Check-out').fill(localDate(5))
      await page.getByRole('button', { name: 'Search', exact: true }).click()
    }
    await expect(page).toHaveURL(/\/search/)
    // The home page also lists this hotel (twice): look only inside the search results
    const hotel = page.locator('.search-results-grid').getByRole('heading', { name: TASHKENT })
    await expect.soft(hotel, 'search with dates should list the Tashkent hotel').toBeVisible()
    if (!(await hotel.isVisible())) {
      // Continue with a date-less search so the later steps can still be checked
      await audit.shot('A2-search-with-dates-failed')
      await page.goto('/search?destination=Tashkent')
    }
    await expect(hotel).toBeVisible()
    await expect.soft(page.getByRole('heading', { name: 'TICKBRON Demo Registan Inn' }),
      'a Tashkent search should not list Samarkand').toHaveCount(0)
  })

  await step(audit, 'A3 open-property', async () => {
    await page.locator('.search-results-grid').getByRole('button', { name: new RegExp(`${TASHKENT} in Tashkent`) }).click()
    await expect(page).toHaveURL(/\/property\/\d+/)
    await expect(page.getByRole('heading', { level: 1, name: TASHKENT })).toBeVisible()
  })

  let selectionTotal = NaN
  await step(audit, 'A4 pick-room-rate-and-stay-with-weekend-night', async () => {
    // A weekend night costs more than the base price: the case that used to show $60 and charge $69
    const stay = await pickStay(page, 'Standard Double', 'Standard Rate', { nights: 2, weekend: true })
    selectionTotal = totalFrom(stay.totalText)
    await expect(page.getByRole('heading', { name: 'Your Selection' })).toBeVisible()
    await page.getByRole('button', { name: 'Proceed to booking' }).click()
    await expect(page).toHaveURL(/\/booking/)
  })

  let summaryTotal = NaN
  await step(audit, 'A5 booking-form-prefilled', async () => {
    await expect(page.getByRole('heading', { name: 'Complete Your Booking' })).toBeVisible()
    // Guest data comes from the logged-in profile (checkpoint 22)
    await expect.soft(page.getByLabel(/email/i).first()).toHaveValue(DEMO.guest.email)
    // PhoneInput shows the E.164 number grouped: +998900000003 -> +998 90 000 00 03
    await expect.soft(page.getByLabel(/phone/i).first()).toHaveValue('+998 90 000 00 03')
    // The profile has full_name "Demo Guest"; first/last name should be filled from it
    const firstName = page.getByLabel(/first name/i)
    const lastName = page.getByLabel(/last name/i)
    await expect.soft(firstName, 'first name pre-filled from profile').not.toHaveValue('')
    await expect.soft(lastName, 'last name pre-filled from profile').not.toHaveValue('')
    await expect(page.locator('.booking-summary-total-value').first()).toBeVisible()
    summaryTotal = await amountNextTo(page, /^Total$/)
    expect(summaryTotal, 'booking form total = total shown when the dates were picked').toBe(selectionTotal)
    if (!(await firstName.inputValue())) await firstName.fill('Demo')
    if (!(await lastName.inputValue())) await lastName.fill('Guest')
    await page.getByRole('button', { name: /continue to payment/i }).click()
  })

  await step(audit, 'A6 pay-test-mode', async () => {
    await expect(page.getByRole('heading', { level: 1, name: 'Payment Method' })).toBeVisible()
    await page.getByRole('radio').first().click()
    await page.getByRole('button', { name: /^Pay with/ }).click()
    await expect(page.getByRole('heading', { name: /Payment Successful|Booking Confirmed/ })).toBeVisible({ timeout: 20_000 })
  })

  await step(audit, 'A7 confirmation-reference-code', async () => {
    const code = page.getByText(/^[A-Z2-9]{6}$/).first()
    await expect(code).toBeVisible()
    shared.referenceCode = (await code.textContent())?.trim()
    expect(shared.referenceCode).toMatch(/^[A-Z2-9]{6}$/)
    // Money is charged in so'm: what the guest was shown as paid is the booking's stored charge
    const paidText = await page.getByText('Amount Paid:').first().locator('..').innerText()
    const paid = Number(paidText.replace(/^Amount Paid:/, '').replace(/\D/g, ''))
    const bookings = await (await page.request.get(`${API}/api/v1/bookings/`)).json()
    const rows = Array.isArray(bookings) ? bookings : bookings.results
    const stored = rows.find((b: { confirmation_code: string }) => b.confirmation_code === shared.referenceCode)
    expect(Number(stored.total_price), 'backend booking total = hotel price shown before payment').toBe(summaryTotal)
    expect(stored.charge_currency).toBe('UZS')
    expect(paid, `amount paid (${paidText}) should equal the stored charge (${stored.charge_amount})`)
      .toBe(Math.round(Number(stored.charge_amount)))
  })

  await step(audit, 'A8 my-bookings', async () => {
    await page.goto('/bookings')
    await expect(page.getByText(shared.referenceCode ?? 'NO-CODE').first()).toBeVisible()
  })
})

test('B payment failure shows the failure screen and retry works', async ({ page, audit }) => {
  await step(audit, 'B0 login-and-open-property', async () => {
    await loginWithPassword(page, DEMO.guest.email, DEMO.guest.password)
    await page.goto('/search?destination=Tashkent')
    await page.locator('.search-results-grid').getByRole('button', { name: new RegExp(`${TASHKENT} in Tashkent`) }).click()
    await pickStay(page, 'Standard Double', 'Standard Rate', { nights: 1, skip: 1 })
    await page.getByRole('button', { name: 'Proceed to booking' }).click()
  })

  await step(audit, 'B1 pay-with-simulated-provider-failure', async () => {
    // Test-mode payments always succeed, so one confirm call is failed here to reach the failure screen
    await page.route('**/api/v1/payments/transactions/*/confirm/', (route) =>
      route.fulfill({ status: 502, json: { error: { code: 'provider_error', message: 'Provider declined the payment', details: {} } } }),
    { times: 1 })
    await fillBookingFormAndPay(page)
    await expect(page.getByRole('button', { name: 'Retry payment' })).toBeVisible({ timeout: 20_000 })
  })

  await step(audit, 'B2 retry-succeeds', async () => {
    await page.getByRole('button', { name: 'Retry payment' }).click()
    const payAgain = page.getByRole('button', { name: /^Pay with/ })
    if (await payAgain.isVisible().catch(() => false)) {
      await page.getByRole('radio').first().click()
      await payAgain.click()
    }
    await expect(page.getByRole('heading', { name: /Payment Successful|Booking Confirmed/ })).toBeVisible({ timeout: 20_000 })
  })
})

test('C favorites: add, list, remove', async ({ page, audit }) => {
  let propertyId = 0
  await step(audit, 'C1 add-from-property-page', async () => {
    await loginWithPassword(page, DEMO.guest.email, DEMO.guest.password)
    ;({ propertyId } = await tashkentIds(page))
    await page.goto(`/property/${propertyId}`)
    await expect(page.getByRole('heading', { level: 1, name: TASHKENT })).toBeVisible()
    const favoriteButton = page.getByRole('button', { name: /favou?rite|save/i })
    await expect.soft(favoriteButton, 'property page should have an add-to-favorites button').not.toHaveCount(0)
    if (await favoriteButton.count()) {
      await favoriteButton.first().click()
    } else {
      // No UI control: add through the API so listing and removal can still be checked
      const response = await api(page, 'POST', '/api/v1/me/favorites/', { property: propertyId })
      expect([201, 400]).toContain(response.status())
    }
  })

  await step(audit, 'C2 favorites-page-lists-it', async () => {
    await page.goto('/favorites')
    await expect(page.getByRole('heading', { name: 'My Favorites' })).toBeVisible()
    await expect(page.getByText('1 properties saved')).toBeVisible()
    await expect.soft(page.getByRole('link', { name: TASHKENT }), 'favorite card shows the property name').toBeVisible()
    await expect.soft(page.getByText('$60'), 'favorite card shows the price').not.toHaveCount(0)
  })

  await step(audit, 'C3 remove', async () => {
    await page.getByRole('button', { name: /^Remove/ }).first().click()
    await expect(page.getByRole('button', { name: /^Remove/ })).toHaveCount(0)
    await page.reload()
    await expect(page.getByRole('heading', { name: 'No favorites yet' })).toBeVisible()
    await expect(page.getByRole('button', { name: /^Remove/ })).toHaveCount(0)
  })
})

test('D phone and OTP login', async ({ page, audit }) => {
  await step(audit, 'D1 request-code', async () => {
    await page.goto('/login')
    await page.getByRole('button', { name: 'Phone & SMS Code' }).click()
    await page.getByLabel('Phone Number').fill(DEMO.guest.phone)
    await page.getByRole('button', { name: 'Send Code', exact: true }).click()
    await expect(page.locator('.auth-test-mode')).toBeVisible()
  })

  await step(audit, 'D2 enter-code-and-log-in', async () => {
    const code = (await page.locator('.auth-test-mode').innerText()).match(/\d{6}/)?.[0]
    expect(code, 'test mode shows the 6-digit code').toBeTruthy()
    await page.locator('#otp_code').fill(code ?? '')
    await page.locator('.auth-submit').click()
    await page.waitForURL((url) => !url.pathname.startsWith('/login'))
    await expect(page.getByRole('link', { name: 'Login' })).toHaveCount(0)
  })
})

test('E hotel owner changes availability and the public page shows it', async ({ page, audit }) => {
  const targetDate = dateInCurrentMonth(3)
  let ids = { propertyId: 0, ratePlanId: 0 }
  let inventoryId: number | null = null

  await step(audit, 'E1 login-partner-panel', async () => {
    await loginWithPassword(page, DEMO.owner.email, DEMO.owner.password)
    await page.goto('/partner')
    await expect(page.getByRole('heading', { name: 'My Properties' })).toBeVisible()
    // Only the owner's three demo properties
    await expect(page.getByRole('button', { name: /^Manage / })).toHaveCount(3)
    // Cards and their Manage buttons name the hotel, not only the city (phase 2 item 4)
    for (const hotel of [TASHKENT, 'TICKBRON Demo Registan Inn', 'TICKBRON Demo Old Town Guesthouse']) {
      await expect(page.getByRole('button', { name: `Manage ${hotel}` })).toBeVisible()
      await expect(page.getByRole('heading', { level: 3, name: hotel })).toBeVisible()
    }
  })

  await step(audit, 'E2 open-availability-in-ui', async () => {
    await page.getByRole('button', { name: `Manage ${TASHKENT}` }).click()
    await expect(page.getByRole('heading', { name: `Room Types for ${TASHKENT}` })).toBeVisible()
    const toRates = page.getByRole('button', { name: /rates|rate plans|availability|inventory/i })
    await expect.soft(toRates, 'a room type should lead to its rate plans / availability').not.toHaveCount(0)
  })

  await step(audit, 'E3 close-a-date', async () => {
    // The UI cannot reach the availability view, so the owner's own API session is used
    ids = await tashkentIds(page)
    const list = await (await page.request.get(
      `${API}/api/v1/partner/inventory/?rate_plan=${ids.ratePlanId}&date_from=${targetDate}&date_to=${targetDate}`,
    )).json()
    inventoryId = list.results[0].id
    const response = await api(page, 'PATCH', `/api/v1/partner/inventory/${inventoryId}/`, { is_available: false })
    expect(response.status()).toBe(200)
  })

  try {
    await step(audit, 'E4 public-page-shows-closed-date', async () => {
      await logout(page)
      await page.goto(`/property/${ids.propertyId}`)
      await page.getByRole('button', { name: /^Standard Double/ }).click()
      await page.getByText('Standard Rate', { exact: true }).first().click()
      const day = page.locator(`.availability-calendar-day[data-date="${targetDate}"]`)
      await expect(day).toHaveAttribute('aria-disabled', 'true')
    })
  } finally {
    // Reopen the date so reruns and other flows see the seeded availability
    if (inventoryId) {
      await loginWithPassword(page, DEMO.owner.email, DEMO.owner.password)
      await api(page, 'PATCH', `/api/v1/partner/inventory/${inventoryId}/`, { is_available: true })
    }
  }
})

test('F super-admin: create owner, customers, note, support lookup, statistics', async ({ page, audit }) => {
  const stamp = Date.now()
  const newOwner = { email: `e2e-owner-${stamp}@tickbron.demo`, password: `E2eOwnerPass#${stamp}` }

  await step(audit, 'F1 create-hotel-owner', async () => {
    await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password)
    await page.goto('/admin')
    await page.getByRole('button', { name: /Create Owner/ }).click()
    await page.getByLabel('Email Address:').fill(newOwner.email)
    await page.getByLabel('First Name:').fill('E2E')
    await page.getByLabel('Last Name:').fill('Owner')
    await page.getByLabel('Password:', { exact: true }).fill(newOwner.password)
    await page.getByLabel('Confirm Password:').fill(newOwner.password)
    await page.getByRole('button', { name: 'Create Account' }).click()
    await expect(page.getByText(newOwner.email).first()).toBeVisible()
    await expect(page.getByRole('alert').filter({ hasText: /error|fail/i })).toHaveCount(0)
  })

  await step(audit, 'F2 new-owner-logs-in', async () => {
    await logout(page)
    await loginWithPassword(page, newOwner.email, newOwner.password)
    await page.goto('/partner')
    await expect(page.getByRole('heading', { name: 'Partner Dashboard' })).toBeVisible()
    await expect(page.getByRole('button', { name: /^Manage / })).toHaveCount(0)
  })

  await step(audit, 'F3 customers-list', async () => {
    await logout(page)
    await loginWithPassword(page, DEMO.admin.email, DEMO.admin.password)
    await page.goto('/admin')
    await page.getByRole('button', { name: /Customers/ }).click()
    await expect(page.getByRole('table', { name: 'Customers directory' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Demo Guest' })).toBeVisible()
    // Hotel owners are not customers
    await expect.soft(page.getByRole('link', { name: 'Demo Hotel Owner' }), 'owners should not be listed as customers')
      .toHaveCount(0)
  })

  await step(audit, 'F4 customer-profile-add-note', async () => {
    await page.getByRole('link', { name: 'Demo Guest' }).click()
    await expect(page).toHaveURL(/\/admin\/customers\/\d+/)
    await expect(page.getByText('guest@tickbron.demo').first()).toBeVisible()
    await page.getByRole('tab', { name: /Internal Notes/ }).click()
    const note = `E2E note ${stamp}`
    await page.getByLabel('New internal note').fill(note)
    await page.getByLabel('Add note').click()
    await expect(page.getByText(note)).toBeVisible()
  })

  await step(audit, 'F5 support-lookup', async () => {
    expect(shared.referenceCode, 'flow A must run first and create a booking').toBeTruthy()
    await page.goto('/admin/support')
    await page.getByLabel('Reference Code').fill(shared.referenceCode ?? '')
    await page.getByRole('button', { name: 'Look Up Booking' }).click()
    await expect(page.getByRole('heading', { level: 2, name: 'Booking Details' })).toBeVisible()
    await expect(page.getByText(shared.referenceCode ?? '').first()).toBeVisible()
    await expect(page.getByText(/Tashkent/).first()).toBeVisible()
    await expect.soft(page.getByText(TASHKENT), 'support lookup shows the hotel name').not.toHaveCount(0)
  })

  await step(audit, 'F6 statistics', async () => {
    await page.goto('/admin')
    await page.getByRole('button', { name: /Statistics/ }).click()
    await expect(page.getByRole('heading', { name: /New Registrations/ })).toBeVisible()
    await expect(page.getByRole('img', { name: /Registration chart/ })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Top Bookers Leaderboard' })).toBeVisible()
  })
})

test('G access control for admin pages', async ({ page, audit }) => {
  const denied = page.getByText(/Access Denied/i)

  await step(audit, 'G1 guest-admin-dashboard', async () => {
    await loginWithPassword(page, DEMO.guest.email, DEMO.guest.password)
    await page.goto('/admin')
    await expect(denied.first()).toBeVisible()
  })

  await step(audit, 'G2 guest-admin-customer-profile', async () => {
    await page.goto('/admin/customers/1')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText('guest@tickbron.demo')).toHaveCount(0)
    await expect.soft(denied.first(), 'customer profile should say access denied, not a generic error').toBeVisible()
  })

  await step(audit, 'G3 guest-admin-support', async () => {
    await page.goto('/admin/support')
    await expect(denied.first()).toBeVisible()
  })

  await step(audit, 'G4 guest-partner-panel', async () => {
    await page.goto('/partner')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('button', { name: /^Manage / })).toHaveCount(0)
    await expect.soft(denied.first(), 'partner panel should say access denied for guests').toBeVisible()
  })

  await step(audit, 'G5 owner-admin-dashboard', async () => {
    await logout(page)
    await loginWithPassword(page, DEMO.owner.email, DEMO.owner.password)
    await page.goto('/admin')
    await expect(denied.first()).toBeVisible()
  })
})

test('H language switch uz / ru / en', async ({ page, audit }) => {
  await step(audit, 'H1 language-menu', async () => {
    await page.goto('/')
    await page.locator('.language-selector-button').first().click()
    await expect.soft(page.getByText(/O['‘’]zbek|Uzbek/i), 'Uzbek should be offered').not.toHaveCount(0)
    await expect.soft(page.getByText('Русский'), 'Russian should be offered').not.toHaveCount(0)
  })

  await step(audit, 'H2 switch-to-russian-home', async () => {
    const russian = page.getByText('Русский').first()
    if (await russian.isVisible()) await russian.click()
    await expect.soft(page.getByRole('heading', { name: 'Find Your Perfect Stay' }),
      'home page text should change after choosing Russian').toHaveCount(0)
  })

  await step(audit, 'H3 property-page-in-russian', async () => {
    const { propertyId } = await tashkentIds(page)
    await page.goto(`/property/${propertyId}`)
    await expect(page.getByRole('heading', { level: 1, name: TASHKENT })).toBeVisible()
    await page.waitForLoadState('networkidle')
    await expect.soft(page.getByRole('heading', { name: 'Select Your Room' }),
      'property page text should be translated').toHaveCount(0)
  })

  await step(audit, 'H4 back-to-english', async () => {
    await page.goto('/')
    await page.locator('.language-selector-button').first().click()
    const english = page.getByText('English').first()
    if (await english.isVisible()) await english.click()
    await expect(page.getByRole('heading', { name: 'Find Your Perfect Stay' })).toBeVisible()
  })
})
