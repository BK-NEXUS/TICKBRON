import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Header } from './Header'
import { AuthProvider } from '../contexts/AuthContext'

// Mock the auth adapter
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

describe('Header', () => {
  const renderWithAuthProvider = (component: React.ReactElement) => {
    return render(
      <AuthProvider>
        <BrowserRouter>
          {component}
        </BrowserRouter>
      </AuthProvider>
    )
  }

  it('renders the logo', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('TICKBRON')).toBeInTheDocument()
  })

  it('renders the client logo image next to the site name', () => {
    const { container } = renderWithAuthProvider(<Header />)
    const logo = container.querySelector('.header-logo img.brand-logo--header')
    expect(logo).toHaveAttribute('src', '/brand/tickbron-logo.jpg')
    // Decorative: the visible "TICKBRON" heading already names the site
    expect(logo).toHaveAttribute('alt', '')
  })

  it('shows the name from full_name instead of "User" (E2E UX 13)', async () => {
    const { authAdapter } = await import('../adapters/authAdapter')
    vi.mocked(authAdapter.getCurrentUser).mockResolvedValueOnce({
      success: true,
      user: { id: 3, email: 'guest@example.com', first_name: null, last_name: null, full_name: 'Demo Guest' },
    } as never)
    renderWithAuthProvider(<Header />)

    expect(await screen.findByText('Demo Guest')).toBeInTheDocument()
    expect(screen.queryByText('User')).not.toBeInTheDocument()
  })

  const openMenuAs = async (user: Record<string, unknown>) => {
    const { authAdapter } = await import('../adapters/authAdapter')
    vi.mocked(authAdapter.getCurrentUser).mockResolvedValueOnce({
      success: true,
      user: { id: 3, email: 'someone@example.com', full_name: 'Some One', ...user },
    } as never)
    renderWithAuthProvider(<Header />)
    fireEvent.click(await screen.findByRole('button', { name: /Some One/ }))
  }

  it('hides the partner dashboard link from regular users', async () => {
    await openMenuAs({ role: null, is_staff: false, is_superuser: false })
    expect(screen.getByText('My Profile')).toBeInTheDocument()
    expect(screen.queryByText('Partner Dashboard')).not.toBeInTheDocument()
    expect(screen.queryByText('Admin Dashboard')).not.toBeInTheDocument()
  })

  it('shows the partner dashboard link to hotel owners but not the admin link', async () => {
    await openMenuAs({ role: 'hotel-owner', is_staff: false, is_superuser: false })
    expect(screen.getByText('Partner Dashboard')).toBeInTheDocument()
    expect(screen.queryByText('Admin Dashboard')).not.toBeInTheDocument()
  })

  it('shows both dashboards to staff', async () => {
    await openMenuAs({ role: null, is_staff: true, is_superuser: false })
    expect(screen.getByText('Partner Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Admin Dashboard')).toBeInTheDocument()
  })

  it('renders navigation links', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Properties')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
    expect(screen.getByText('Help')).toBeInTheDocument()
  })

  it('renders action buttons when not authenticated', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('Login')).toBeInTheDocument()
    expect(screen.getByText('Sign Up')).toBeInTheDocument()
  })

  it('renders language selector', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('EN')).toBeInTheDocument()
  })

  it('renders currency selector', () => {
    renderWithAuthProvider(<Header />)
    expect(screen.getByText('USD')).toBeInTheDocument()
  })

  it('renders mobile menu toggle', () => {
    renderWithAuthProvider(<Header />)
    const toggle = screen.getByLabelText('Open menu')
    expect(toggle).toBeInTheDocument()
  })
})
