/**
 * The owner reaches the photo manager of the managed hotel from the side menu.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { PartnerDashboardPage } from './PartnerDashboardPage'
import { BreadcrumbProvider, Breadcrumbs } from '../components/Breadcrumbs'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { id: 2, email: 'owner@example.com', first_name: 'Olim' }, isAuthenticated: true }),
}))
vi.mock('../adapters/partnerAdapter', () => ({ partnerAdapter: { getProperties: vi.fn() } }))
vi.mock('../components/PartnerRoomsManagement', () => ({
  PartnerRoomsManagement: () => <div data-testid="rooms-management" />,
}))
vi.mock('../components/PartnerPhotosManagement', () => ({
  PartnerPhotosManagement: ({ propertyId }: { propertyId: number }) => (
    <div data-testid="photos-management">photos of property {propertyId}</div>
  ),
}))
vi.mock('../components/PartnerPropertyEdit', () => ({
  PartnerPropertyEdit: ({ property }: { property: { id: number } }) => <div data-testid="property-edit">edit of property {property.id}</div>,
}))
vi.mock('../components/PartnerPropertyWizard', () => ({ PartnerPropertyWizard: () => null }))
vi.mock('../components/PartnerBookingsView', () => ({ PartnerBookingsView: () => null }))
vi.mock('../components/PartnerStatusTab', () => ({ PartnerStatusTab: () => null }))

const renderDashboard = () =>
  render(
    <MemoryRouter initialEntries={['/partner']}>
      <BreadcrumbProvider>
        <Breadcrumbs />
        <PartnerDashboardPage />
      </BreadcrumbProvider>
    </MemoryRouter>
  )

describe('PartnerDashboardPage photos', () => {
  beforeEach(() => {
    vi.mocked(partnerAdapter.getProperties).mockResolvedValue({
      data: [{ id: 3, city: 'Tashkent', address_line1: '15 Amir Temur Avenue', status: 'active' } as never],
      error: null,
    })
  })

  it('has no Photos menu item until a hotel is selected', async () => {
    renderDashboard()
    await screen.findByRole('button', { name: /Manage/ })
    expect(screen.queryByRole('button', { name: 'Photos' })).not.toBeInTheDocument()
  })

  it('opens the photo manager of the selected hotel and shows it in the breadcrumb', async () => {
    renderDashboard()
    fireEvent.click(await screen.findByRole('button', { name: /Manage/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Photos' }))
    expect(screen.getByTestId('photos-management')).toHaveTextContent('photos of property 3')
    expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent('Photos')
  })

  it('opens the hotel details screen of the selected hotel and shows it in the breadcrumb', async () => {
    renderDashboard()
    expect(screen.queryByRole('button', { name: 'Hotel details' })).not.toBeInTheDocument()
    fireEvent.click(await screen.findByRole('button', { name: /Manage/ }))
    fireEvent.click(await screen.findByRole('button', { name: 'Hotel details' }))
    expect(screen.getByTestId('property-edit')).toHaveTextContent('edit of property 3')
    expect(screen.getByRole('navigation', { name: /breadcrumb/i })).toHaveTextContent('Hotel details')
  })
})
