/** The owner's list of rate plans shows the type as a readable label, not the code the server stores. */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PartnerRatesManagement } from './PartnerRatesManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getRatePlans: vi.fn(), updateRatePlan: vi.fn(), createRatePlan: vi.fn(), deleteRatePlan: vi.fn() },
}))

const plan = (rate_type: string) => ({
  id: 1, room_type: 7, name: 'Plan', slug: 'plan', rate_type, description: '', base_price: 40, currency: 'USD',
  prices: { USD: '40.00', UZS: '1.00', KZT: '1.00', RUB: '1.00' }, min_nights: 1, max_nights: 30, is_active: true,
  cancellation_policy: 'flexible', deposit_required: false,
}) as never

describe('rate plan list', () => {
  beforeEach(() => {
    localStorage.clear()
    localStorage.setItem('tickbron.language', 'en')
    vi.resetAllMocks()
  })

  it('shows a known type translated', async () => {
    vi.mocked(partnerAdapter.getRatePlans).mockResolvedValue({ data: [plan('non_refundable')], error: null })
    render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe" />)
    expect(await screen.findByText('Non-Refundable')).toBeInTheDocument()
    expect(screen.queryByText('non_refundable')).not.toBeInTheDocument()
  })

  it('shows an unknown type as readable words', async () => {
    vi.mocked(partnerAdapter.getRatePlans).mockResolvedValue({ data: [plan('weekend_special')], error: null })
    render(<PartnerRatesManagement roomTypeId={7} roomTypeName="Deluxe" />)
    expect(await screen.findByText('Weekend Special')).toBeInTheDocument()
  })
})
