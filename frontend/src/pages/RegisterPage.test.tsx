import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { RegisterPage } from './RegisterPage'
import { AuthProvider } from '../contexts/AuthContext'

// Mock the auth adapter
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    register: vi.fn(),
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

const renderWithRouter = async (component: React.ReactElement) => {
  const result = render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/register']}>
        <Routes>
          <Route path="/register" element={component} />
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  )
  // Let what the page loads on mount (e.g. the auth check) finish inside act
  await act(async () => {})
  return result
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders registration form', async () => {
      await renderWithRouter(<RegisterPage />)

      expect(screen.getByLabelText('Full Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
    })

    it('renders title and subtitle', async () => {
      await renderWithRouter(<RegisterPage />)

      expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument()
      expect(screen.getByText('Join TICKBRON to book amazing properties')).toBeInTheDocument()
    })

    it('renders the client logo above the form', async () => {
      await renderWithRouter(<RegisterPage />)

      const logo = screen.getByRole('img', { name: 'TICKBRON — Online Booking' })
      expect(logo).toHaveAttribute('src', '/brand/tickbron-logo.jpg')
      expect(logo).toHaveClass('brand-logo--auth')
    })

    it('renders link to login page', async () => {
      await renderWithRouter(<RegisterPage />)

      expect(screen.getByText('Already have an account?')).toBeInTheDocument()
      expect(screen.getByText('Sign in')).toBeInTheDocument()
    })

    it('shows password hint', async () => {
      await renderWithRouter(<RegisterPage />)

      expect(screen.getByText('Must be at least 12 characters')).toBeInTheDocument()
    })
  })

  describe('phone number field', () => {
    const fillAllBut = (phone: string) => {
      fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'John Doe' } })
      fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'test@example.com' } })
      fireEvent.change(screen.getByLabelText('Phone Number'), { target: { value: phone } })
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'SecurePassword123!' } })
      fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'SecurePassword123!' } })
    }

    it('formats the number and stops at a complete +998 number', async () => {
      await renderWithRouter(<RegisterPage />)
      const phoneInput = screen.getByLabelText('Phone Number')
      fireEvent.change(phoneInput, { target: { value: '+998 90 123 45 6789' } })
      expect(phoneInput).toHaveValue('+998 90 123 45 67')
    })

    it('does not submit an incomplete number', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      await renderWithRouter(<RegisterPage />)
      fillAllBut('90 123 45')
      fireEvent.click(screen.getByRole('button', { name: /create account/i }))

      expect(await screen.findByText(/valid phone number/i)).toBeInTheDocument()
      expect(authAdapter.register).not.toHaveBeenCalled()
    })

    it('sends the number in E.164', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.register).mockResolvedValue({ success: false, error: 'stop here' })
      await renderWithRouter(<RegisterPage />)
      fillAllBut('90 123 45 67')
      fireEvent.click(screen.getByRole('button', { name: /create account/i }))

      await waitFor(() => expect(authAdapter.register).toHaveBeenCalledWith(
        expect.objectContaining({ phone_number: '+998901234567' }),
      ))
    })
  })

  describe('form submission', () => {
    it('submits registration with required fields', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.register).mockResolvedValue({
        success: true,
        user: {
          id: 1,
          email: 'test@example.com',
          first_name: '',
          last_name: '',
          full_name: 'John Doe',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: false,
          two_factor_enabled: false,
        },
      })

      await renderWithRouter(<RegisterPage />)

      const fullNameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(phoneInput, { target: { value: '+998901234567' } })
      fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(authAdapter.register).toHaveBeenCalledWith({
          email: 'test@example.com',
          full_name: 'John Doe',
          phone_number: '+998901234567',
          password: 'SecurePassword123!',
          password_confirm: 'SecurePassword123!',
        })
      })
    })

    it('displays error on password mismatch', async () => {
      await renderWithRouter(<RegisterPage />)

      const fullNameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(phoneInput, { target: { value: '+998901234567' } })
      fireEvent.change(passwordInput, { target: { value: 'Password123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'DifferentPassword123!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
      })
    })

    it('displays error on short password', async () => {
      await renderWithRouter(<RegisterPage />)

      const fullNameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(phoneInput, { target: { value: '+998901234567' } })
      fireEvent.change(passwordInput, { target: { value: 'Short1!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'Short1!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Password must be at least 12 characters')).toBeInTheDocument()
      })
    })

    it('displays error message on registration failure', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.register).mockResolvedValue({
        success: false,
        error: 'Email already exists',
      })

      await renderWithRouter(<RegisterPage />)

      const fullNameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(phoneInput, { target: { value: '+998901234567' } })
      fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument()
      })
    })

    it('disables submit button while loading', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      // The test decides when registration finishes (no real timer racing the assertions)
      let finishRegister: (value: { success: boolean }) => void = () => {}
      vi.mocked(authAdapter.register).mockImplementation(
        () => new Promise(resolve => { finishRegister = resolve })
      )

      await renderWithRouter(<RegisterPage />)

      const fullNameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(phoneInput, { target: { value: '+998901234567' } })
      fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.click(submitButton)

      expect(submitButton).toBeDisabled()
      expect(screen.getByText('Creating Account...')).toBeInTheDocument()

      // Finish inside the test so no state update lands after it ends
      await act(async () => finishRegister({ success: true }))
    })
  })

  describe('form validation', () => {
    it('requires required fields', async () => {
      await renderWithRouter(<RegisterPage />)

      expect(screen.getByLabelText('Full Name')).toHaveAttribute('required')
      expect(screen.getByLabelText('Email')).toHaveAttribute('required')
      expect(screen.getByLabelText('Phone Number')).toHaveAttribute('required')
      expect(screen.getByLabelText('Password')).toHaveAttribute('required')
      expect(screen.getByLabelText('Confirm Password')).toHaveAttribute('required')
    })

    it('has correct autocomplete attributes', async () => {
      await renderWithRouter(<RegisterPage />)

      const fullNameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')

      expect(fullNameInput).toHaveAttribute('autocomplete', 'name')
      expect(emailInput).toHaveAttribute('autocomplete', 'email')
      expect(phoneInput).toHaveAttribute('autocomplete', 'tel')
      expect(passwordInput).toHaveAttribute('autocomplete', 'new-password')
      expect(confirmPasswordInput).toHaveAttribute('autocomplete', 'new-password')
    })
  })

  describe('accessibility', () => {
    it('has proper form labels', async () => {
      await renderWithRouter(<RegisterPage />)

      expect(screen.getByLabelText('Full Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
    })

    it('displays error with role="alert"', async () => {
      await renderWithRouter(<RegisterPage />)

      const fullNameInput = screen.getByLabelText('Full Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(phoneInput, { target: { value: '+998901234567' } })
      fireEvent.change(passwordInput, { target: { value: 'Password123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'DifferentPassword123!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        const errorElement = screen.getByText('Passwords do not match')
        expect(errorElement).toHaveAttribute('role', 'alert')
      })
    })
  })
})
