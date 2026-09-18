import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
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

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      <MemoryRouter initialEntries={['/register']}>
        <Routes>
          <Route path="/register" element={component} />
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  )
}

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('rendering', () => {
    it('renders registration form', () => {
      renderWithRouter(<RegisterPage />)

      expect(screen.getByLabelText('First Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Phone Number (Optional)')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument()
    })

    it('renders title and subtitle', () => {
      renderWithRouter(<RegisterPage />)

      expect(screen.getByRole('heading', { name: 'Create Account' })).toBeInTheDocument()
      expect(screen.getByText('Join TICKBRON to book amazing properties')).toBeInTheDocument()
    })

    it('renders link to login page', () => {
      renderWithRouter(<RegisterPage />)

      expect(screen.getByText('Already have an account?')).toBeInTheDocument()
      expect(screen.getByText('Sign in')).toBeInTheDocument()
    })

    it('shows password hint', () => {
      renderWithRouter(<RegisterPage />)

      expect(screen.getByText('Must be at least 12 characters')).toBeInTheDocument()
    })
  })

  describe('form submission', () => {
    it('submits registration with all fields', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.register).mockResolvedValue({
        success: true,
        user: {
          id: 1,
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          full_name: 'John Doe',
          is_active: true,
          date_joined: '2024-01-01T00:00:00Z',
          email_verified: false,
          two_factor_enabled: false,
        },
      })

      renderWithRouter(<RegisterPage />)

      const firstNameInput = screen.getByLabelText('First Name')
      const lastNameInput = screen.getByLabelText('Last Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number (Optional)')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(phoneInput, { target: { value: '+1234567890' } })
      fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(authAdapter.register).toHaveBeenCalledWith({
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          phone_number: '+1234567890',
          password: 'SecurePassword123!',
          password_confirm: 'SecurePassword123!',
        })
      })
    })

    it('displays error on password mismatch', async () => {
      renderWithRouter(<RegisterPage />)

      const firstNameInput = screen.getByLabelText('First Name')
      const lastNameInput = screen.getByLabelText('Last Name')
      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'Password123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'DifferentPassword123!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
      })
    })

    it('displays error on short password', async () => {
      renderWithRouter(<RegisterPage />)

      const firstNameInput = screen.getByLabelText('First Name')
      const lastNameInput = screen.getByLabelText('Last Name')
      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
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

      renderWithRouter(<RegisterPage />)

      const firstNameInput = screen.getByLabelText('First Name')
      const lastNameInput = screen.getByLabelText('Last Name')
      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.click(submitButton)

      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument()
      })
    })

    it('disables submit button while loading', async () => {
      const { authAdapter } = await import('../adapters/authAdapter')
      vi.mocked(authAdapter.register).mockImplementation(
        () => new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      )

      renderWithRouter(<RegisterPage />)

      const firstNameInput = screen.getByLabelText('First Name')
      const lastNameInput = screen.getByLabelText('Last Name')
      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
      fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })
      fireEvent.click(submitButton)

      expect(submitButton).toBeDisabled()
      expect(screen.getByText('Creating Account...')).toBeInTheDocument()
    })
  })

  describe('form validation', () => {
    it('requires required fields', () => {
      renderWithRouter(<RegisterPage />)

      expect(screen.getByLabelText('First Name')).toHaveAttribute('required')
      expect(screen.getByLabelText('Last Name')).toHaveAttribute('required')
      expect(screen.getByLabelText('Email')).toHaveAttribute('required')
      expect(screen.getByLabelText('Password')).toHaveAttribute('required')
      expect(screen.getByLabelText('Confirm Password')).toHaveAttribute('required')
    })

    it('does not require phone number', () => {
      renderWithRouter(<RegisterPage />)

      const phoneInput = screen.getByLabelText('Phone Number (Optional)')
      expect(phoneInput).not.toHaveAttribute('required')
    })

    it('has correct autocomplete attributes', () => {
      renderWithRouter(<RegisterPage />)

      const firstNameInput = screen.getByLabelText('First Name')
      const lastNameInput = screen.getByLabelText('Last Name')
      const emailInput = screen.getByLabelText('Email')
      const phoneInput = screen.getByLabelText('Phone Number (Optional)')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')

      expect(firstNameInput).toHaveAttribute('autocomplete', 'given-name')
      expect(lastNameInput).toHaveAttribute('autocomplete', 'family-name')
      expect(emailInput).toHaveAttribute('autocomplete', 'email')
      expect(phoneInput).toHaveAttribute('autocomplete', 'tel')
      expect(passwordInput).toHaveAttribute('autocomplete', 'new-password')
      expect(confirmPasswordInput).toHaveAttribute('autocomplete', 'new-password')
    })
  })

  describe('accessibility', () => {
    it('has proper form labels', () => {
      renderWithRouter(<RegisterPage />)

      expect(screen.getByLabelText('First Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Email')).toBeInTheDocument()
      expect(screen.getByLabelText('Phone Number (Optional)')).toBeInTheDocument()
      expect(screen.getByLabelText('Password')).toBeInTheDocument()
      expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
    })

    it('displays error with role="alert"', async () => {
      renderWithRouter(<RegisterPage />)

      const firstNameInput = screen.getByLabelText('First Name')
      const lastNameInput = screen.getByLabelText('Last Name')
      const emailInput = screen.getByLabelText('Email')
      const passwordInput = screen.getByLabelText('Password')
      const confirmPasswordInput = screen.getByLabelText('Confirm Password')
      const submitButton = screen.getByRole('button', { name: /create account/i })

      fireEvent.change(firstNameInput, { target: { value: 'John' } })
      fireEvent.change(lastNameInput, { target: { value: 'Doe' } })
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
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
