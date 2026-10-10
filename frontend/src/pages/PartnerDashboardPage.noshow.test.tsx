import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PartnerDashboardPage } from './PartnerDashboardPage'
import { BreadcrumbProvider, Breadcrumbs } from '../components/Breadcrumbs'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { id: 2, email: 'owner@example.com', first_name: 'Olim' }, isAuthenticated: true }),
}))
vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getProperties: vi.fn() },
}))
vi.mock('../components/PartnerNoShowReports', () => ({
  PartnerNoShowReports: ({ properties }: { properties: Array<{ id: number; name: string }> }) => (
    <div data-testid="no-show-reports">hotels: {properties.map(p => p.name).join(', ')}</div>
  ),
}))

describe('PartnerDashboardPage no-show reports', () => {
  beforeEach(() => {
    vi.mocked(partnerAdapter.getProperties).mockResolvedValue({
      data: [{ id: 3, name: 'Silk Road Plaza', city: 'Samarkand', address_line1: '1 Street', status: 'active' } as never],
      error: null,
    })
  })

  it('opens My reports from the navigation with the owner hotels and a breadcrumb', async () => {
    render(
      <MemoryRouter initialEntries={['/partner']}>
        <BreadcrumbProvider>
          <Breadcrumbs />
          <PartnerDashboardPage />
        </BreadcrumbProvider>
      </MemoryRouter>,
    )
    const nav = await screen.findByRole('button', { name: 'My reports' })
    expect(nav.textContent).toBe('My reports')
    fireEvent.click(nav)
    expect(screen.getByTestId('no-show-reports')).toHaveTextContent('hotels: Silk Road Plaza')
    expect(nav).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('navigation', { name: 'Breadcrumb' })).toHaveTextContent('My reports')
  })
})
