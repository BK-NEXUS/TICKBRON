/**
 * The phone number is back (plan PLAN_CASH_ONLY stage 1): asked at sign-up and in the profile.
 * It is only stored: no code is sent.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { RegisterPage } from './RegisterPage'
import { ProfilePage } from './ProfilePage'
import { useAuth } from '../contexts/AuthContext'

vi.mock('../contexts/AuthContext', () => ({ useAuth: vi.fn() }))
const mockUseAuth = vi.mocked(useAuth)

const base = { login: vi.fn(), logout: vi.fn(), refreshUser: vi.fn(), isLoading: false }

describe('register: phone number', () => {
  const register = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    register.mockResolvedValue({ success: true })
    mockUseAuth.mockReturnValue({ ...base, user: null, isAuthenticated: false, register } as never)
  })

  function fill(phone: string) {
    fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'Ali Valiyev' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'ali@example.com' } })
    fireEvent.change(screen.getByLabelText('Phone number'), { target: { value: phone } })
    for (const box of screen.getAllByLabelText(/password/i)) fireEvent.change(box, { target: { value: 'Str0ng#Passw0rd-2026' } })
  }

  it('asks for the phone number and marks it required', () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>)
    const box = screen.getByLabelText('Phone number')
    expect(box).toBeRequired()
    expect(box).toHaveAttribute('type', 'tel')
    expect(screen.getByText(/international format/i)).toBeInTheDocument()
  })

  it('keeps only digits and a leading plus while typing', () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>)
    const box = screen.getByLabelText('Phone number')
    fireEvent.change(box, { target: { value: '+998 90 12abc3' } })
    expect(box).toHaveValue('+99890123')
  })

  it('sends the number with the sign-up', async () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>)
    fill('+998901234567')
    fireEvent.click(screen.getByRole('button', { name: /create account|sign up|register/i }))
    await waitFor(() => expect(register).toHaveBeenCalledWith(expect.objectContaining({ phone_number: '+998901234567' })))
  })

  it('refuses a number that cannot be valid and does not call the server', async () => {
    render(<MemoryRouter><RegisterPage /></MemoryRouter>)
    fill('12345')
    fireEvent.click(screen.getByRole('button', { name: /create account|sign up|register/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a valid phone number in international format')
    expect(register).not.toHaveBeenCalled()
  })
})

describe('profile: phone number', () => {
  const updateProfile = vi.fn()
  const user = {
    id: 1, email: 'john@example.com', first_name: 'John', last_name: 'Doe', full_name: 'John Doe',
    phone_number: '+998901112233', whatsapp: '', telegram: '', preferred_contact_method: 'email' as const,
    is_active: true, date_joined: '2025-01-01T00:00:00Z', last_login: '2025-01-15T00:00:00Z',
    email_verified: true, two_factor_enabled: false,
  }

  beforeEach(() => {
    vi.clearAllMocks()
    updateProfile.mockResolvedValue({ success: true })
    mockUseAuth.mockReturnValue({ ...base, user, isAuthenticated: true, updateProfile } as never)
  })

  it('shows the number', () => {
    render(<MemoryRouter><ProfilePage /></MemoryRouter>)
    expect(screen.getByText('+998901112233')).toBeInTheDocument()
  })

  it('changes the number', async () => {
    render(<MemoryRouter><ProfilePage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /edit/i }))
    fireEvent.change(screen.getByLabelText('Phone number'), { target: { value: '+998915554433' } })
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => expect(updateProfile).toHaveBeenCalledWith(expect.objectContaining({ phone_number: '+998915554433' })))
  })

  it('does not let the number be blanked or made invalid', async () => {
    render(<MemoryRouter><ProfilePage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /edit/i }))
    const box = screen.getByLabelText('Phone number')
    fireEvent.change(box, { target: { value: '' } })
    fireEvent.submit(box.closest('form') as HTMLFormElement) // the browser's own "required" stops a click first
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a valid phone number in international format')
    expect(updateProfile).not.toHaveBeenCalled()
  })

  it('an old account without a number can still save other changes', async () => {
    mockUseAuth.mockReturnValue({ ...base, user: { ...user, phone_number: undefined }, isAuthenticated: true, updateProfile } as never)
    render(<MemoryRouter><ProfilePage /></MemoryRouter>)
    fireEvent.click(screen.getByRole('button', { name: /edit/i }))
    fireEvent.change(screen.getByLabelText('Telegram'), { target: { value: '@john' } })
    fireEvent.click(screen.getByRole('button', { name: /save/i }))
    await waitFor(() => expect(updateProfile).toHaveBeenCalled())
  })
})
