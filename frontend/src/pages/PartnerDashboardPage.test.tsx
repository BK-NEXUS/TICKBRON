import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { PartnerDashboardPage } from './PartnerDashboardPage'
import { AuthProvider } from '../contexts/AuthContext'

// Mock the partner adapter
vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    getProperties: vi.fn(),
  },
}))

// Mock the components
vi.mock('../components/PartnerPropertyWizard', () => ({
  PartnerPropertyWizard: () => <div data-testid="property-wizard">Property Wizard</div>,
}))

vi.mock('../components/PartnerRoomsManagement', () => ({
  PartnerRoomsManagement: () => <div data-testid="rooms-management">Rooms Management</div>,
}))

vi.mock('../components/PartnerRatesManagement', () => ({
  PartnerRatesManagement: () => <div data-testid="rates-management">Rates Management</div>,
}))

vi.mock('../components/PartnerAvailabilityManagement', () => ({
  PartnerAvailabilityManagement: () => <div data-testid="availability-management">Availability Management</div>,
}))

vi.mock('../components/PartnerBookingsView', () => ({
  PartnerBookingsView: () => <div data-testid="bookings-view">Bookings View</div>,
}))

vi.mock('../components/EmptyState', () => ({
  EmptyState: ({ icon, title, message, ctaText, onClick }: any) => (
    <div data-testid="empty-state">
      <span>{icon}</span>
      <h2>{title}</h2>
      <p>{message}</p>
      {ctaText && <button onClick={onClick}>{ctaText}</button>}
    </div>
  ),
}))

describe('PartnerDashboardPage', () => {
  it('should show authentication required when not authenticated', () => {
    render(
      <AuthProvider>
        <PartnerDashboardPage />
      </AuthProvider>
    )

    expect(screen.getByText('Authentication required')).toBeInTheDocument()
    expect(screen.getByText('Please sign in to access the partner dashboard.')).toBeInTheDocument()
  })
})
