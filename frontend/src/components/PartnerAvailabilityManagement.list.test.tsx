/** The date inventory list reads like a table: no "null" in the stay limits and the dates are in the page language. */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { PartnerAvailabilityManagement } from './PartnerAvailabilityManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getDateInventory: vi.fn() },
}))

const day = (id: number, minimum_stay: number | null, maximum_stay: number | null) => ({
  id, rate_plan: 11, date: '2026-10-16', available_rooms: 5, booked_rooms: 0, price: 40.5, currency: 'USD',
  is_available: true, minimum_stay, maximum_stay, created_at: '', updated_at: '',
}) as never

describe('date inventory list', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('tickbron.language', 'en')
    vi.resetAllMocks()
  })

  it('shows a dash where no stay limit is set', async () => {
    vi.mocked(partnerAdapter.getDateInventory).mockResolvedValue({ data: [day(1, null, null)], error: null })
    render(<PartnerAvailabilityManagement ratePlanId={11} ratePlanName="Standard" />)
    const row = (await screen.findAllByRole('row'))[1]
    expect(within(row).getByText('—')).toBeInTheDocument()
    expect(row).not.toHaveTextContent('null')
  })

  it('shows the limits when they are set', async () => {
    vi.mocked(partnerAdapter.getDateInventory).mockResolvedValue({ data: [day(1, 2, 14)], error: null })
    render(<PartnerAvailabilityManagement ratePlanId={11} ratePlanName="Standard" />)
    expect(await screen.findByText('2 - 14 nights')).toBeInTheDocument()
  })

  it('writes the date out with the month name', async () => {
    vi.mocked(partnerAdapter.getDateInventory).mockResolvedValue({ data: [day(1, 1, 30)], error: null })
    render(<PartnerAvailabilityManagement ratePlanId={11} ratePlanName="Standard" />)
    expect(await screen.findByText('Oct 16, 2026')).toBeInTheDocument()
  })
})
