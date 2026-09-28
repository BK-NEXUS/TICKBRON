/**
 * E2E BUG 3: a hotel owner could not get from a room type to its rate plans,
 * or from a rate plan to its availability (the selection was never set).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PartnerDashboardPage } from './PartnerDashboardPage'
import { BreadcrumbProvider, Breadcrumbs } from '../components/Breadcrumbs'
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

// The breadcrumb trail is shown by the layout (MainLayout)
const renderDashboard = () =>
  render(
    <MemoryRouter initialEntries={['/partner']}>
      <BreadcrumbProvider>
        <Breadcrumbs />
        <PartnerDashboardPage />
      </BreadcrumbProvider>
    </MemoryRouter>
  )

describe('PartnerDashboardPage navigation', () => {
  beforeEach(() => {
    vi.mocked(partnerAdapter.getProperties).mockResolvedValue({
      data: [{ id: 3, city: 'Tashkent', address_line1: '15 Amir Temur Avenue', status: 'active' } as never],
      error: null,
    })
  })

  it('goes property -> room type rates -> rate plan availability', async () => {
    renderDashboard()

    fireEvent.click(await screen.findByRole('button', { name: 'Manage Tashkent' }))
    expect(screen.getByTestId('rooms-management')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'stub: open rates' }))
    expect(screen.getByTestId('rates-management')).toHaveTextContent('rates for room 7')
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('Deluxe King')

    fireEvent.click(screen.getByRole('button', { name: 'stub: open availability' }))
    expect(screen.getByTestId('availability-management')).toHaveTextContent('availability for rate plan 11')
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('Standard Rate')
  })

  it('cards show the hotel name, not only the city (E2E flow E)', async () => {
    vi.mocked(partnerAdapter.getProperties).mockResolvedValue({
      data: [{ id: 3, name: 'TICKBRON Demo Hotel Tashkent', city: 'Tashkent', address_line1: '15 Amir Temur Avenue', status: 'active' } as never],
      error: null,
    })
    renderDashboard()

    expect(await screen.findByRole('heading', { level: 3, name: 'TICKBRON Demo Hotel Tashkent' })).toBeInTheDocument()
    expect(screen.getByText('Tashkent, 15 Amir Temur Avenue')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Manage TICKBRON Demo Hotel Tashkent' }))
    const trail = screen.getByRole('navigation', { name: 'Breadcrumb' })
    expect(trail).toHaveTextContent('Partner Dashboard')
    expect(trail).toHaveTextContent('TICKBRON Demo Hotel Tashkent')
  })

  it('Back steps up one level inside the dashboard', async () => {
    renderDashboard()
    fireEvent.click(await screen.findByRole('button', { name: 'Manage Tashkent' }))
    fireEvent.click(screen.getByRole('button', { name: 'stub: open rates' }))
    expect(screen.getByTestId('rates-management')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByTestId('rooms-management')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByRole('heading', { name: 'My Properties' })).toBeInTheDocument()
  })
})
