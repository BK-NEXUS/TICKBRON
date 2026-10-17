import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { AuthProvider } from '../contexts/AuthContext'

// Mock the auth adapter
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    login: vi.fn(),
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

const renderWithRouter = async (component: React.ReactElement) => {
  const result = render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={component} />
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  )
  // Let what the page loads on mount (e.g. the auth check) finish inside act
  await act(async () => {})
  return result
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('offers only e-mail sign-in: no phone or SMS option', async () => {
      await renderWithRouter(<LoginPage />)

      expect(screen.queryByText('Phone & SMS Code')).not.toBeInTheDocument()
      expect(screen.queryByText('Email & Password')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Phone Number')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Enter 6-digit Code')).not.toBeInTheDocument()
    })

    it('renders the e-mail login form', async () => {
      await renderWithRouter(<LoginPage />)

      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('links to the password reset from the password form', async () => {
      await renderWithRouter(<LoginPage />)

      expect(screen.getByRole('link', { name: 'Forgot password?' })).toHaveAttribute('href', '/forgot-password')
    })

    it('renders title and subtitle', async () => {
      await renderWithRouter(<LoginPage />)

      expect(screen.getByText('Welcome Back')).toBeInTheDocument()
      expect(screen.getByText('Sign in to your TICKBRON account')).toBeInTheDocument()
    })

    it('renders the client logo above the form', async () => {
      await renderWithRouter(<LoginPage />)

      const logo = screen.getByRole('img', { name: 'TICKBRON — Online Booking' })
      expect(logo).toHaveAttribute('src', '/brand/tickbron-logo.webp')
      expect(logo).toHaveClass('brand-logo--auth')
    })

    it('renders link to register page', async () => {
      await renderWithRouter(<LoginPage />)

      expect(screen.getByText('Don\'t have an account?')).toBeInTheDocument()
      expect(screen.getByText('Sign up')).toBeInTheDocument()
    })

    it('shows password login form by default', async () => {
      await renderWithRouter(<LoginPage />)

      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.queryByLabelText('Phone Number')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Enter 6-digit Code')).not.toBeInTheDocument()
    })
  })

  describe('form submission', () => {
    it('submits login with email and password', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.login).mockResolvedValue({
        success: true,
        user: {
          id: 1,
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: true,
          two_factor_enabled: false,
        },
      })

      await renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(authAdapter.login).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'password123',
        })
      })
    })

    it('displays error message on login failure', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.login).mockResolvedValue({
        success: false,
        error: 'Invalid credentials',
      })

      await renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
      })
    })

    it('disables submit button while loading', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      // The test decides when login finishes (no real timer racing the assertions)
      let finishLogin: (value: { success: boolean }) => void = () => {}
      vi.mocked(authAdapter.login).mockImplementation(
        () => new Promise(resolve => { finishLogin = resolve })
      )

      await renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      expect(submitButton).toBeDisabled()
      expect(screen.getByText('Signing in...')).toBeInTheDocument()

      // Finish inside the test so no state update lands after it ends
      await act(async () => finishLogin({ success: true }))
    })
  })

  describe('form validation', () => {
    it('requires email field', async () => {
      await renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      expect(emailInput).toHaveAttribute('required')
    })

    it('requires password field', async () => {
      await renderWithRouter(<LoginPage />)

      const passwordInput = screen.getByLabelText('Password')
      expect(passwordInput).toHaveAttribute('required')
    })

    it('has correct autocomplete attributes', async () => {
      await renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')

      expect(emailInput).toHaveAttribute('autocomplete', 'email')
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
    })
  })

  describe('accessibility', () => {
    it('has proper form labels for password login', async () => {
      await renderWithRouter(<LoginPage />)

      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
    })

    it('displays error with role="alert" for password login', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.login).mockResolvedValue({
        success: false,
        error: 'Invalid credentials',
      })

      await renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        const errorElement = screen.getByText('Invalid credentials')
        expect(errorElement).toHaveAttribute('role', 'alert')
      })
    })
  })
})
