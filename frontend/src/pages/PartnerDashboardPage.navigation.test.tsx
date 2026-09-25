/**
 * E2E BUG 3: a hotel owner could not get from a room type to its rate plans,
 * or from a rate plan to its availability (the selection was never set).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PartnerDashboardPage } from './PartnerDashboardPage'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({
    user: { id: 2, email: 'owner@example.com', first_name: 'Olim' },
    isAuthenticated: true,
  }),
}))

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getProperties: vi.fn() },
}))

// Child views are replaced by stubs that call the callbacks the dashboard passes in
vi.mock('../components/PartnerRoomsManagement', () => ({
  PartnerRoomsManagement: ({ onManageRates }: { onManageRates?: (room: { id: number; name: string }) => void }) => (
    <div data-testid="rooms-management">
      <button onClick={() => onManageRates?.({ id: 7, name: 'Deluxe King' })}>stub: open rates</button>
    </div>
  ),
}))
vi.mock('../components/PartnerRatesManagement', () => ({
  PartnerRatesManagement: ({ roomTypeId, onManageAvailability }: {
    roomTypeId: number
    onManageAvailability?: (plan: { id: number; name: string }) => void
  }) => (
    <div data-testid="rates-management">
      rates for room {roomTypeId}
      <button onClick={() => onManageAvailability?.({ id: 11, name: 'Standard Rate' })}>stub: open availability</button>
    </div>
  ),
}))
vi.mock('../components/PartnerAvailabilityManagement', () => ({
  PartnerAvailabilityManagement: ({ ratePlanId }: { ratePlanId: number }) => (
    <div data-testid="availability-management">availability for rate plan {ratePlanId}</div>
  ),
}))
vi.mock('../components/PartnerPropertyWizard', () => ({ PartnerPropertyWizard: () => null }))
vi.mock('../components/PartnerBookingsView', () => ({ PartnerBookingsView: () => null }))

describe('PartnerDashboardPage navigation', () => {
  beforeEach(() => {
    vi.mocked(partnerAdapter.getProperties).mockResolvedValue({
      data: [{ id: 3, city: 'Tashkent', address_line1: '15 Amir Temur Avenue', status: 'active' } as never],
      error: null,
    })
  })

  it('goes property -> room type rates -> rate plan availability', async () => {
    render(<PartnerDashboardPage />)

    fireEvent.click(await screen.findByRole('button', { name: 'Manage Tashkent' }))
    expect(screen.getByTestId('rooms-management')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'stub: open rates' }))
    expect(screen.getByTestId('rates-management')).toHaveTextContent('rates for room 7')
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('Deluxe King')

    fireEvent.click(screen.getByRole('button', { name: 'stub: open availability' }))
    expect(screen.getByTestId('availability-management')).toHaveTextContent('availability for rate plan 11')
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('Standard Rate')
  })
})
