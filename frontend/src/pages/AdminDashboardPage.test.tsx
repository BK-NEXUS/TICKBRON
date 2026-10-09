import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminDashboardPage } from './AdminDashboardPage'
import { useAuth } from '../contexts/AuthContext'
import { MemoryRouter } from 'react-router-dom'
import { BreadcrumbProvider, Breadcrumbs } from '../components/Breadcrumbs'
import { promotionAdapter } from '../adapters/promotionAdapter'

// Mock useAuth
vi.mock('../contexts/AuthContext')
// Only the Advertising screen uses this adapter
vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { listPromotions: vi.fn(), searchHotels: vi.fn() },
}))

describe('AdminDashboardPage', () => {
  const mockUser = {
    id: 1,
    email: 'admin@example.com',
    first_name: 'Admin',
    last_name: 'User',
    full_name: 'Admin User',
    is_staff: true,
    is_superuser: true,
    is_active: true,
    date_joined: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should show authentication required when not authenticated', () => {
    (useAuth as never).mockReturnValue({
      user: null,
      isAuthenticated: false,
    })

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Authentication required')).toBeInTheDocument()
    expect(screen.getByText('Please sign in to access the admin dashboard.')).toBeInTheDocument()
  })

  it('should show access denied for non-admin users', () => {
    (useAuth as never).mockReturnValue({
      user: { ...mockUser, is_staff: false, is_superuser: false },
      isAuthenticated: true,
    })

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('You do not have permission to access the admin dashboard.')).toBeInTheDocument()
  })

  it('should render dashboard for staff users', () => {
    (useAuth as never).mockReturnValue({
      user: { ...mockUser, is_staff: true, is_superuser: false },
      isAuthenticated: true,
    })

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    expect(screen.getByText(/Welcome, Admin/i)).toBeInTheDocument()
    expect(screen.getByText('Staff')).toBeInTheDocument()
  })

  it('should render dashboard for super-admin users', () => {
    (useAuth as never).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    expect(screen.getByText(/Welcome, Admin/i)).toBeInTheDocument()
    expect(screen.getByText('Super Admin')).toBeInTheDocument()
  })

  it('should show create owner button for super-admin only', () => {
    (useAuth as never).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Create Owner')).toBeInTheDocument()
  })

  it('should not show create owner button for staff users', () => {
    (useAuth as never).mockReturnValue({
      user: { ...mockUser, is_staff: true, is_superuser: false },
      isAuthenticated: true,
    })

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    )

    expect(screen.queryByText('Create Owner')).not.toBeInTheDocument()
  })

  it('should render navigation tabs', () => {
    (useAuth as never).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })

    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>
    )

    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(screen.getByText('Amenities')).toBeInTheDocument()
    expect(screen.getByText('Users')).toBeInTheDocument()
  })

  it('opens the Status section from the navigation, and its breadcrumb returns', () => {
    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    } as unknown as ReturnType<typeof useAuth>)

    render(
      <MemoryRouter initialEntries={['/admin']}>
        <BreadcrumbProvider>
          <Breadcrumbs />
          <AdminDashboardPage />
        </BreadcrumbProvider>
      </MemoryRouter>
    )

    const statusNav = screen.getByRole('button', { name: 'Status' })
    // No emoji icons on the new navigation item
    expect(statusNav.textContent).toBe('Status')
    fireEvent.click(statusNav)

    expect(screen.getByRole('heading', { name: 'Status' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Countries/ })).toBeInTheDocument()
    expect(statusNav).toHaveAttribute('aria-current', 'page')

    // "Admin Dashboard" in the page breadcrumbs leaves the Status section
    fireEvent.click(screen.getByRole('button', { name: 'Admin Dashboard' }))
    expect(screen.queryByRole('heading', { name: 'Status' })).not.toBeInTheDocument()
  })

  describe('Advertising section', () => {
    function openAdvertising(user: typeof mockUser) {
      vi.mocked(useAuth).mockReturnValue({ user, isAuthenticated: true } as unknown as ReturnType<typeof useAuth>)
      vi.mocked(promotionAdapter.listPromotions).mockResolvedValue({
        data: { count: 0, next: null, previous: null, results: [] }, error: null, code: null,
      })
      render(
        <MemoryRouter>
          <AdminDashboardPage />
        </MemoryRouter>
      )
      const nav = screen.getByRole('button', { name: 'Advertising' })
      fireEvent.click(nav)
      return nav
    }

    it('is in the navigation without an emoji and opens the screen', async () => {
      const nav = openAdvertising(mockUser)
      expect(nav.textContent).toBe('Advertising')
      expect(nav).toHaveAttribute('aria-current', 'page')
      expect(await screen.findByText('No promotions yet.')).toBeInTheDocument()
    })

    it('a super-admin can find hotels to promote', async () => {
      openAdvertising(mockUser)
      await screen.findByText('No promotions yet.')
      expect(screen.getByLabelText('Find a hotel by name')).toBeInTheDocument()
    })

    it('staff see the screen read-only', async () => {
      openAdvertising({ ...mockUser, is_superuser: false })
      await waitFor(() => expect(screen.getByText('No promotions yet.')).toBeInTheDocument())
      expect(screen.queryByLabelText('Find a hotel by name')).toBeNull()
      expect(screen.getByText(/Only a super-admin can change them/)).toBeInTheDocument()
    })
  })
})
