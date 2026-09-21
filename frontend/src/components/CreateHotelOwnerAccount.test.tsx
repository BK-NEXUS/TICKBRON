import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CreateHotelOwnerAccount } from './CreateHotelOwnerAccount'
import { adminAdapter } from '../adapters/adminAdapter'

// Mock adminAdapter
vi.mock('../adapters/adminAdapter')

describe('CreateHotelOwnerAccount', () => {
  const mockOnSuccess = vi.fn()
  const mockOnCancel = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the form', () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/First Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Last Name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Confirm Password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument()
  })

  it('should validate required fields', async () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeInTheDocument()
    })
  })

  it('should validate email format', async () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    const emailInput = screen.getByLabelText(/Email Address/i)
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } })

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument()
    })
  })

  it('should validate password length', async () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    const emailInput = screen.getByLabelText(/Email Address/i)
    fireEvent.change(emailInput, { target: { value: 'owner@example.com' } })

    const firstNameInput = screen.getByLabelText(/First Name/i)
    fireEvent.change(firstNameInput, { target: { value: 'John' } })

    const lastNameInput = screen.getByLabelText(/Last Name/i)
    fireEvent.change(lastNameInput, { target: { value: 'Doe' } })

    const passwordInput = screen.getByLabelText(/Password/i)
    fireEvent.change(passwordInput, { target: { value: 'short' } })

    const confirmPasswordInput = screen.getByLabelText(/Confirm Password/i)
    fireEvent.change(confirmPasswordInput, { target: { value: 'short' } })

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Password must be at least 12 characters')).toBeInTheDocument()
    })
  })

  it('should validate password confirmation', async () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    const emailInput = screen.getByLabelText(/Email Address/i)
    fireEvent.change(emailInput, { target: { value: 'owner@example.com' } })

    const firstNameInput = screen.getByLabelText(/First Name/i)
    fireEvent.change(firstNameInput, { target: { value: 'John' } })

    const lastNameInput = screen.getByLabelText(/Last Name/i)
    fireEvent.change(lastNameInput, { target: { value: 'Doe' } })

    const passwordInput = screen.getByLabelText(/Password/i)
    fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })

    const confirmPasswordInput = screen.getByLabelText(/Confirm Password/i)
    fireEvent.change(confirmPasswordInput, { target: { value: 'DifferentPassword123!' } })

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Passwords do not match')).toBeInTheDocument()
    })
  })

  it('should generate random password', () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    const generateButton = screen.getByRole('button', { name: /Generate/i })
    fireEvent.click(generateButton)

    const passwordInput = screen.getByLabelText(/Password/i) as HTMLInputElement
    const confirmPasswordInput = screen.getByLabelText(/Confirm Password/i) as HTMLInputElement

    expect(passwordInput.value.length).toBe(16)
    expect(passwordInput.value).toBe(confirmPasswordInput.value)
  })

  it('should call createHotelOwner on valid form submission', async () => {
    const mockResponse = {
      id: 2,
      email: 'owner@example.com',
      first_name: 'John',
      last_name: 'Doe',
      full_name: 'John Doe',
      role: 'hotel-owner',
      is_active: true,
      date_joined: '2024-01-01T00:00:00Z',
    }

    ;(adminAdapter.createHotelOwner as any).mockResolvedValueOnce({
      data: mockResponse,
      error: null,
    })

    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    const emailInput = screen.getByLabelText(/Email Address/i)
    fireEvent.change(emailInput, { target: { value: 'owner@example.com' } })

    const firstNameInput = screen.getByLabelText(/First Name/i)
    fireEvent.change(firstNameInput, { target: { value: 'John' } })

    const lastNameInput = screen.getByLabelText(/Last Name/i)
    fireEvent.change(lastNameInput, { target: { value: 'Doe' } })

    const passwordInput = screen.getByLabelText(/Password/i)
    fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })

    const confirmPasswordInput = screen.getByLabelText(/Confirm Password/i)
    fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(adminAdapter.createHotelOwner).toHaveBeenCalledWith({
        email: 'owner@example.com',
        first_name: 'John',
        last_name: 'Doe',
        phone_number: '',
        password: 'SecurePassword123!',
        password_confirm: 'SecurePassword123!',
      })
    })

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled()
    })
  })

  it('should display success panel with credentials after successful creation', async () => {
    const mockResponse = {
      id: 2,
      email: 'owner@example.com',
      first_name: 'John',
      last_name: 'Doe',
      full_name: 'John Doe',
      role: 'hotel-owner',
      is_active: true,
      date_joined: '2024-01-01T00:00:00Z',
    }

    ;(adminAdapter.createHotelOwner as any).mockResolvedValueOnce({
      data: mockResponse,
      error: null,
    })

    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    // Fill form
    const emailInput = screen.getByLabelText(/Email Address/i)
    fireEvent.change(emailInput, { target: { value: 'owner@example.com' } })

    const firstNameInput = screen.getByLabelText(/First Name/i)
    fireEvent.change(firstNameInput, { target: { value: 'John' } })

    const lastNameInput = screen.getByLabelText(/Last Name/i)
    fireEvent.change(lastNameInput, { target: { value: 'Doe' } })

    const passwordInput = screen.getByLabelText(/Password/i)
    fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })

    const confirmPasswordInput = screen.getByLabelText(/Confirm Password/i)
    fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Hotel Owner Account Created Successfully')).toBeInTheDocument()
      expect(screen.getByText('owner@example.com')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getByText('SecurePassword123!')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
    })
  })

  it('should display error message on API failure', async () => {
    ;(adminAdapter.createHotelOwner as any).mockResolvedValueOnce({
      data: null,
      error: 'Super-admin required',
    })

    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    // Fill form
    const emailInput = screen.getByLabelText(/Email Address/i)
    fireEvent.change(emailInput, { target: { value: 'owner@example.com' } })

    const firstNameInput = screen.getByLabelText(/First Name/i)
    fireEvent.change(firstNameInput, { target: { value: 'John' } })

    const lastNameInput = screen.getByLabelText(/Last Name/i)
    fireEvent.change(lastNameInput, { target: { value: 'Doe' } })

    const passwordInput = screen.getByLabelText(/Password/i)
    fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })

    const confirmPasswordInput = screen.getByLabelText(/Confirm Password/i)
    fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Super-admin required')).toBeInTheDocument()
    })
  })

  it('should call onCancel when cancel button is clicked', () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    const cancelButton = screen.getByRole('button', { name: /Cancel/i })
    fireEvent.click(cancelButton)

    expect(mockOnCancel).toHaveBeenCalled()
  })

  it('should reset form after successful creation and create another', async () => {
    const mockResponse = {
      id: 2,
      email: 'owner@example.com',
      first_name: 'John',
      last_name: 'Doe',
      full_name: 'John Doe',
      role: 'hotel-owner',
      is_active: true,
      date_joined: '2024-01-01T00:00:00Z',
    }

    ;(adminAdapter.createHotelOwner as any).mockResolvedValueOnce({
      data: mockResponse,
      error: null,
    })

    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    // Fill and submit first form
    const emailInput = screen.getByLabelText(/Email Address/i)
    fireEvent.change(emailInput, { target: { value: 'owner@example.com' } })

    const firstNameInput = screen.getByLabelText(/First Name/i)
    fireEvent.change(firstNameInput, { target: { value: 'John' } })

    const lastNameInput = screen.getByLabelText(/Last Name/i)
    fireEvent.change(lastNameInput, { target: { value: 'Doe' } })

    const passwordInput = screen.getByLabelText(/Password/i)
    fireEvent.change(passwordInput, { target: { value: 'SecurePassword123!' } })

    const confirmPasswordInput = screen.getByLabelText(/Confirm Password/i)
    fireEvent.change(confirmPasswordInput, { target: { value: 'SecurePassword123!' } })

    const submitButton = screen.getByRole('button', { name: /Create Account/i })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Hotel Owner Account Created Successfully')).toBeInTheDocument()
    })

    // Click create another
    const createAnotherButton = screen.getByRole('button', { name: /Create Another Account/i })
    fireEvent.click(createAnotherButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
      expect((screen.getByLabelText(/Email Address/i) as HTMLInputElement).value).toBe('')
    })
  })

  it('should show security information', () => {
    render(<CreateHotelOwnerAccount onSuccess={mockOnSuccess} onCancel={mockOnCancel} />)

    expect(screen.getByText('Important:')).toBeInTheDocument()
    expect(screen.getByText(/Only super-admins can create hotel owner accounts/i)).toBeInTheDocument()
    expect(screen.getByText(/Credentials will be shown once after creation/i)).toBeInTheDocument()
    expect(screen.getByText(/Password must be at least 12 characters/i)).toBeInTheDocument()
  })
})
