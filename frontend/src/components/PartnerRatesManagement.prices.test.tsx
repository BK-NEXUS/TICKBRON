/**
 * R16: the owner enters the price of a rate plan in every currency (USD, UZS, KZT, RUB) himself.
 * One of them is the main price (the currency of the hotel); the backend checks everything again.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerRatesManagement } from './PartnerRatesManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getRatePlans: vi.fn(), updateRatePlan: vi.fn(), createRatePlan: vi.fn(), deleteRatePlan: vi.fn() },
}))

const api = vi.mocked(partnerAdapter)
const FULL = { USD: '65.00', UZS: '800000.00', KZT: '29000.00', RUB: '5800.00' }

const plan = (patch = {}) => ({
  id: 11, room_type: 7, name: 'Standard Rate', slug: 'standard', rate_type: 'standard', description: '', base_price: 65,
  currency: 'USD', prices: FULL, min_nights: 1, max_nights: 30, is_active: true, cancellation_policy: 'flexible',
  deposit_required: false, ...patch,
}) as never

const box = (code: string) => screen.getByLabelText(new RegExp(`\\(${code}\\)`)) as HTMLInputElement
const type = (code: string, value: string) => fireEvent.change(box(code), { target: { value } })

async function openCreate(currency?: string) {
  api.getRatePlans.mockResolvedValue({ data: [], error: null })
  render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe King" currency={currency} />)
  fireEvent.click(await screen.findByRole('button', { name: 'Add new rate plan' }))
  fireEvent.change(screen.getByLabelText(/Rate Plan Name/), { target: { value: 'Flex' } })
  fireEvent.change(screen.getByLabelText(/Slug/), { target: { value: 'flex' } })
}

async function openEdit(ratePlan = plan()) {
  api.getRatePlans.mockResolvedValue({ data: [ratePlan], error: null })
  render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe King" />)
  fireEvent.click(await screen.findByRole('button', { name: 'Edit Standard Rate' }))
  await screen.findByLabelText(/Rate Plan Name/)
}

const fillAll = () => Object.entries(FULL).forEach(([code, value]) => type(code, value))
const create = () => fireEvent.click(screen.getByRole('button', { name: 'Create Rate Plan' }))
const update = () => fireEvent.click(screen.getByRole('button', { name: 'Update Rate Plan' }))

describe('prices of a rate plan in every currency', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('tickbron.language', 'en')
    vi.resetAllMocks()
    api.createRatePlan.mockResolvedValue({ data: plan(), error: null })
    api.updateRatePlan.mockResolvedValue({ data: plan(), error: null })
  })

  it('has one box per currency, empty for a new plan, and marks the main one', async () => {
    await openCreate('UZS')
    for (const code of ['USD', 'UZS', 'KZT', 'RUB']) expect(box(code)).toHaveValue(null)
    expect(screen.getByText(/main price \(the currency of your hotel\)/)).toBeInTheDocument()
    expect(box('UZS').closest('.form-group')).toHaveTextContent('main price')
    expect(box('USD').closest('.form-group')).not.toHaveTextContent('main price')
  })

  it('refuses a new plan with a missing price and names the currency', async () => {
    await openCreate('USD')
    type('USD', '65'); type('UZS', '800000'); type('KZT', '29000')
    create()
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the price in RUB.')
    expect(api.createRatePlan).not.toHaveBeenCalled()
  })

  it('sends the four prices and no separate base price or currency', async () => {
    await openCreate('USD')
    fillAll()
    create()
    await waitFor(() => expect(api.createRatePlan).toHaveBeenCalled())
    const sent = JSON.parse(JSON.stringify(api.createRatePlan.mock.calls[0][0]))
    expect(sent.prices).toEqual({ USD: '65.00', UZS: '800000.00', KZT: '29000.00', RUB: '5800.00' })
    expect(sent).not.toHaveProperty('base_price')
    expect(sent).not.toHaveProperty('currency')
  })

  it.each([
    ['UZS', '800000.5', 'UZS: whole amounts only (no decimals).'],
    ['KZT', '29000.5', 'KZT: whole amounts only (no decimals).'],
    ['RUB', '12.3', 'RUB: whole amounts only (no decimals).'],
    ['USD', '65.001', 'USD: at most two decimals.'],
    ['USD', '-1', 'USD: enter a number of zero or more.'],
  ])('refuses %s = %s before sending anything', async (code, value, message) => {
    await openCreate('USD')
    fillAll()
    type(code, value)
    create()
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(api.createRatePlan).not.toHaveBeenCalled()
  })

  it('shows what the owner entered when editing and sends the prices with the update', async () => {
    await openEdit()
    expect(box('USD')).toHaveValue(65)
    expect(box('UZS')).toHaveValue(800000)
    type('UZS', '850000')
    update()
    await waitFor(() => expect(api.updateRatePlan).toHaveBeenCalled())
    const [id, sent] = api.updateRatePlan.mock.calls[0]
    expect(id).toBe(11)
    expect(JSON.parse(JSON.stringify(sent)).prices).toEqual({ ...FULL, UZS: '850000' })
    expect(sent).not.toHaveProperty('base_price')
  })

  it('a plan with a price in one currency only says so and cannot be saved until the others are entered', async () => {
    await openEdit(plan({ prices: { USD: '60.00' }, base_price: 60 }))
    expect(screen.getByText(/only one currency/)).toBeInTheDocument()
    expect(box('USD')).toHaveValue(60)
    expect(box('UZS')).toHaveValue(null)
    update()
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the price in UZS.')
    expect(api.updateRatePlan).not.toHaveBeenCalled()
    type('UZS', '750000'); type('KZT', '27000'); type('RUB', '5400')
    update()
    await waitFor(() => expect(api.updateRatePlan).toHaveBeenCalled())
  })

  it('flags an incomplete plan in the list and lists the prices of a complete one', async () => {
    api.getRatePlans.mockResolvedValue({
      data: [plan(), plan({ id: 12, name: 'Old Rate', slug: 'old', prices: { USD: '60.00' } })], error: null,
    })
    render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe King" />)
    const complete = (await screen.findByText('Standard Rate')).closest('.rate-plan-card') as HTMLElement
    const old = screen.getByText('Old Rate').closest('.rate-plan-card') as HTMLElement
    expect(within(complete).queryByText('Set prices in other currencies')).toBeNull()
    expect(complete).toHaveTextContent('UZS 800000.00')
    expect(complete).toHaveTextContent('RUB 5800.00')
    expect(within(old).getByText('Set prices in other currencies')).toBeInTheDocument()
  })
})
