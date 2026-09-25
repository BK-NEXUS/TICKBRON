import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { AuthProvider } from '../contexts/AuthContext'

// Mock the auth adapter
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    login: vi.fn(),
    requestOTP: vi.fn(),
    verifyOTP: vi.fn(),
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route path="/login" element={component} />
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders login form with tabs', () => {
      renderWithRouter(<LoginPage />)

      expect(screen.getByText('Email & Password')).toBeInTheDocument()
      expect(screen.getByText('Phone & SMS Code')).toBeInTheDocument()
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
    })

    it('renders title and subtitle', () => {
      renderWithRouter(<LoginPage />)

      expect(screen.getByText('Welcome Back')).toBeInTheDocument()
      expect(screen.getByText('Sign in to your TICKBRON account')).toBeInTheDocument()
    })

    it('renders the client logo above the form', () => {
      renderWithRouter(<LoginPage />)

      const logo = screen.getByRole('img', { name: 'TICKBRON — Online Booking' })
      expect(logo).toHaveAttribute('src', '/brand/tickbron-logo.jpg')
      expect(logo).toHaveClass('brand-logo--auth')
    })

    it('renders link to register page', () => {
      renderWithRouter(<LoginPage />)

      expect(screen.getByText('Don\'t have an account?')).toBeInTheDocument()
      expect(screen.getByText('Sign up')).toBeInTheDocument()
    })

    it('shows password login form by default', () => {
      renderWithRouter(<LoginPage />)

      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.queryByLabelText('Phone Number')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Enter 6-digit Code')).not.toBeInTheDocument()
    })
  })

  describe('login method switching', () => {
    it('switches to phone login when clicking phone tab', () => {
      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument()
      expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
      expect(screen.queryByLabelText('Password')).not.toBeInTheDocument()
    })

    it('switches back to password login when clicking email tab', () => {
      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const emailTab = screen.getByText('Email & Password')
      fireEvent.click(emailTab)

      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.queryByLabelText('Phone Number')).not.toBeInTheDocument()
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

      renderWithRouter(<LoginPage />)

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

      renderWithRouter(<LoginPage />)

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
      vi.mocked(authAdapter.login).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      )

      renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const submitButton = screen.getByRole('button', { name: /sign in/i })

      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'password123' } })
      fireEvent.click(submitButton)

      expect(submitButton).toBeDisabled()
      expect(screen.getByText('Signing in...')).toBeInTheDocument()
    })
  })

  describe('phone/SMS-code login flow', () => {
    it('requests OTP code when phone number submitted', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: true,
        otp_code: '123456',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(authAdapter.requestOTP).toHaveBeenCalledWith({
          phone_number: '+1234567890',
        })
      })

      expect(screen.getByLabelText('Enter 6-digit Code')).toBeInTheDocument()
    })

    it('shows OTP input after code is requested', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: true,
        otp_code: '123456',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByLabelText('Enter 6-digit Code')).toBeInTheDocument()
      })

      expect(screen.getByRole('button', { name: /verify & sign in/i })).toBeInTheDocument()
      expect(screen.getByText('Resend Code')).toBeInTheDocument()
    })

    it('displays test code when OTP response includes it and not in production', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: true,
        otp_code: '123456',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByText(/test mode code:/i)).toBeInTheDocument()
        expect(screen.getByText('123456')).toBeInTheDocument()
      })
    })

    it('verifies OTP and logs in user', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: true,
        otp_code: '123456',
      })
      vi.mocked(authAdapter.verifyOTP).mockResolvedValue({
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

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByLabelText('Enter 6-digit Code')).toBeInTheDocument()
      })

      const otpInput = screen.getByLabelText('Enter 6-digit Code')
      const verifyButton = screen.getByRole('button', { name: /verify & sign in/i })

      fireEvent.change(otpInput, { target: { value: '123456' } })
      fireEvent.click(verifyButton)

      await waitFor(() => {
        expect(authAdapter.verifyOTP).toHaveBeenCalledWith({
          phone_number: '+1234567890',
          otp_code: '123456',
        })
      })
    })

    it('displays error on OTP request failure', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: false,
        error: 'Invalid phone number',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: 'invalid' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByText('Invalid phone number')).toBeInTheDocument()
      })
    })

    it('displays error on OTP verification failure', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: true,
        otp_code: '123456',
      })
      vi.mocked(authAdapter.verifyOTP).mockResolvedValue({
        success: false,
        error: 'Invalid code',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByLabelText('Enter 6-digit Code')).toBeInTheDocument()
      })

      const otpInput = screen.getByLabelText('Enter 6-digit Code')
      const verifyButton = screen.getByRole('button', { name: /verify & sign in/i })

      fireEvent.change(otpInput, { target: { value: '000000' } })
      fireEvent.click(verifyButton)

      await waitFor(() => {
        expect(screen.getByText('Invalid code')).toBeInTheDocument()
      })
    })

    it('allows resending OTP code', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: true,
        otp_code: '123456',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByLabelText('Enter 6-digit Code')).toBeInTheDocument()
      })

      const resendButton = screen.getByText('Resend Code')
      fireEvent.click(resendButton)

      await waitFor(() => {
        expect(authAdapter.requestOTP).toHaveBeenCalledWith({
          phone_number: '+1234567890',
        })
      })
    })

    it('disables phone input after OTP requested', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: true,
        otp_code: '123456',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        expect(screen.getByLabelText('Enter 6-digit Code')).toBeInTheDocument()
      })

      expect(phoneInput).toBeDisabled()
    })
  })

  describe('form validation', () => {
    it('requires email field', () => {
      renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      expect(emailInput).toHaveAttribute('required')
    })

    it('requires password field', () => {
      renderWithRouter(<LoginPage />)

      const passwordInput = screen.getByLabelText('Password')
      expect(passwordInput).toHaveAttribute('required')
    })

    it('has correct autocomplete attributes', () => {
      renderWithRouter(<LoginPage />)

      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')

      expect(emailInput).toHaveAttribute('autocomplete', 'email')
      expect(passwordInput).toHaveAttribute('autocomplete', 'current-password')
    })
  })

  describe('accessibility', () => {
    it('has proper form labels for password login', () => {
      renderWithRouter(<LoginPage />)

      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
    })

    it('has proper form labels for phone login', () => {
      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument()
    })

    it('displays error with role="alert" for password login', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.login).mockResolvedValue({
        success: false,
        error: 'Invalid credentials',
      })

      renderWithRouter(<LoginPage />)

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

    it('displays error with role="alert" for phone login', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.requestOTP).mockResolvedValue({
        success: false,
        error: 'Invalid phone number',
      })

      renderWithRouter(<LoginPage />)

      const phoneTab = screen.getByText('Phone & SMS Code')
      fireEvent.click(phoneTab)

      const phoneInput = screen.getByLabelText('Phone Number')
      const sendButton = screen.getByRole('button', { name: /send code/i })

      fireEvent.change(phoneInput, { target: { value: 'invalid' } })
      fireEvent.click(sendButton)

      await waitFor(() => {
        const errorElement = screen.getByText('Invalid phone number')
        expect(errorElement).toHaveAttribute('role', 'alert')
      })
    })
  })
})
