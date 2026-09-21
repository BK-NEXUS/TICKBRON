import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AdminDashboardPage } from './AdminDashboardPage'
import { useAuth } from '../contexts/AuthContext'

// Mock useAuth
vi.mock('../contexts/AuthContext')

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
    ;(useAuth as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
    })

    render(<AdminDashboardPage />)

    expect(screen.getByText('Authentication required')).toBeInTheDocument()
    expect(screen.getByText('Please sign in to access the admin dashboard.')).toBeInTheDocument()
  })

  it('should show access denied for non-admin users', () => {
    ;(useAuth as any).mockReturnValue({
      user: { ...mockUser, is_staff: false, is_superuser: false },
      isAuthenticated: true,
    })

    render(<AdminDashboardPage />)

    expect(screen.getByText('Access Denied')).toBeInTheDocument()
    expect(screen.getByText('You do not have permission to access the admin dashboard.')).toBeInTheDocument()
  })

  it('should render dashboard for staff users', () => {
    ;(useAuth as any).mockReturnValue({
      user: { ...mockUser, is_staff: true, is_superuser: false },
      isAuthenticated: true,
    })

    render(<AdminDashboardPage />)

    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    expect(screen.getByText(/Welcome, Admin/i)).toBeInTheDocument()
    expect(screen.getByText('Staff')).toBeInTheDocument()
  })

  it('should render dashboard for super-admin users', () => {
    ;(useAuth as any).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })

    render(<AdminDashboardPage />)

    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
    expect(screen.getByText(/Welcome, Admin/i)).toBeInTheDocument()
    expect(screen.getByText('Super Admin')).toBeInTheDocument()
  })

  it('should show create owner button for super-admin only', () => {
    ;(useAuth as any).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })

    render(<AdminDashboardPage />)

    expect(screen.getByText('Create Owner')).toBeInTheDocument()
  })

  it('should not show create owner button for staff users', () => {
    ;(useAuth as any).mockReturnValue({
      user: { ...mockUser, is_staff: true, is_superuser: false },
      isAuthenticated: true,
    })

    render(<AdminDashboardPage />)

    expect(screen.queryByText('Create Owner')).not.toBeInTheDocument()
  })

  it('should render navigation tabs', () => {
    ;(useAuth as any).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    })

    render(<AdminDashboardPage />)

    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(screen.getByText('Amenities')).toBeInTheDocument()
    expect(screen.getByText('Users')).toBeInTheDocument()
  })
})
