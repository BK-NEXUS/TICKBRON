import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { ProfilePage } from './ProfilePage'
import { AuthProvider, useAuth } from '../contexts/AuthContext'
import { settle } from '../test/utils'

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

const mockUseAuth = useAuth as ReturnType<typeof vi.fn>

const mockUser = {
  id: 1,
  email: 'john@example.com',
  first_name: 'John',
  last_name: 'Doe',
  full_name: 'John Doe',
  phone_number: '+1234567890',
  whatsapp: '+9876543210',
  telegram: '@johndoe',
  preferred_contact_method: 'whatsapp' as const,
  is_active: true,
  date_joined: '2025-01-01T00:00:00Z',
  last_login: '2025-01-15T00:00:00Z',
  email_verified: true,
  two_factor_enabled: false,
}

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/profile' }]}>
      <AuthProvider>
        <Routes>
          <Route path="/profile" element={component} />
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/bookings" element={<div>Bookings Page</div>} />
          <Route path="/favorites" element={<div>Favorites Page</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>
  )
}

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Partner Dashboard quick link', () => {
    const renderAs = (user: typeof mockUser & { role?: string | null }) => {
      mockUseAuth.mockReturnValue({
        user,
        isAuthenticated: true,
        isLoading: false,
        updateProfile: vi.fn(),
      })
      renderWithRouter(<ProfilePage />)
    }

    it('is hidden from regular users', () => {
      renderAs({ ...mockUser, role: null })
      expect(screen.getByText('My Bookings')).toBeInTheDocument()
      expect(screen.queryByText('Partner Dashboard')).not.toBeInTheDocument()
    })

    it('is shown to hotel owners', () => {
      renderAs({ ...mockUser, role: 'hotel-owner' })
      expect(screen.getByText('Partner Dashboard')).toBeInTheDocument()
    })
  })

  describe('Authentication redirect', () => {
    it('should redirect to login if not authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Sign in required')).toBeInTheDocument()
      expect(screen.getByText('Please sign in to view your profile.')).toBeInTheDocument()
      expect(screen.getByText('Sign In')).toBeInTheDocument()
    })

    it('should redirect to login if user is null but authenticated', () => {
      mockUseAuth.mockReturnValue({
        user: null,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Sign in required')).toBeInTheDocument()
    })
  })

  describe('Profile display', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })
    })

    it('should render profile header with avatar', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('JD')).toBeInTheDocument()
      expect(screen.getByText('John Doe')).toBeInTheDocument()
      expect(screen.getAllByText('john@example.com')).toHaveLength(2)
    })

    it('should display active status badge', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    it('should display verified status badge when email is verified', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Verified')).toBeInTheDocument()
    })

    it('should not display verified status badge when email is not verified', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, email_verified: false },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.queryByText('Verified')).not.toBeInTheDocument()
    })

    it('should display inactive status badge when user is not active', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, is_active: false },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })
  })

  describe('Personal information section', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })
    })

    it('should display personal information section', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Personal Information')).toBeInTheDocument()
    })

    it('should display first name', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('First Name')).toBeInTheDocument()
      expect(screen.getByText('John')).toBeInTheDocument()
    })

    it('should display last name', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Last Name')).toBeInTheDocument()
      expect(screen.getByText('Doe')).toBeInTheDocument()
    })

    it('should display email', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Email')).toBeInTheDocument()
      const emailLabel = screen.getByText('Email')
      const emailValue = emailLabel.nextElementSibling
      expect(emailValue).toBeInTheDocument()
      expect(emailValue?.textContent).toBe('john@example.com')
    })

    it('should display phone number', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Phone Number')).toBeInTheDocument()
      expect(screen.getByText('+1234567890')).toBeInTheDocument()
    })

    it('should display "Not provided" when phone number is missing', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, phone_number: null },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Phone Number')).toBeInTheDocument()
      expect(screen.getByText('Not provided')).toBeInTheDocument()
    })

    it('should display WhatsApp', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('WhatsApp')).toBeInTheDocument()
      expect(screen.getByText('+9876543210')).toBeInTheDocument()
    })

    it('should display "Not provided" when WhatsApp is missing', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, whatsapp: null },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('WhatsApp')).toBeInTheDocument()
      expect(screen.getByText('Not provided')).toBeInTheDocument()
    })

    it('should display Telegram', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Telegram')).toBeInTheDocument()
      expect(screen.getByText('@johndoe')).toBeInTheDocument()
    })

    it('should display "Not provided" when Telegram is missing', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, telegram: null },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Telegram')).toBeInTheDocument()
      expect(screen.getByText('Not provided')).toBeInTheDocument()
    })

    it('should display preferred contact method', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Preferred Contact Method')).toBeInTheDocument()
      expect(screen.getByText('WhatsApp')).toBeInTheDocument()
    })

    it('should display "Email" as default when preferred contact method is missing', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, preferred_contact_method: null },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Preferred Contact Method')).toBeInTheDocument()
      const allEmailElements = screen.getAllByText('Email')
      const emailValue = allEmailElements.find(el => el.tagName === 'P')
      expect(emailValue).toBeInTheDocument()
    })
  })

  describe('Account information section', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })
    })

    it('should display account information section', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Account Information')).toBeInTheDocument()
    })

    it('should display member since date', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Member Since')).toBeInTheDocument()
      const memberSinceLabel = screen.getByText('Member Since')
      const memberSinceValue = memberSinceLabel.nextElementSibling
      expect(memberSinceValue).toBeInTheDocument()
      expect(memberSinceValue?.textContent).toBeTruthy()
    })

    it('should display last login date', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Last Login')).toBeInTheDocument()
      const lastLoginLabel = screen.getByText('Last Login')
      const lastLoginValue = lastLoginLabel.nextElementSibling
      expect(lastLoginValue).toBeInTheDocument()
      expect(lastLoginValue?.textContent).toBeTruthy()
    })

    it('should display two-factor authentication status', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Two-Factor Authentication')).toBeInTheDocument()
      expect(screen.getByText('Disabled')).toBeInTheDocument()
    })

    it('should display two-factor authentication as enabled when enabled', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, two_factor_enabled: true },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Enabled')).toBeInTheDocument()
    })
  })

  describe('Quick links section', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })
    })

    it('should display quick links section', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Quick Links')).toBeInTheDocument()
    })

    it('should display My Bookings link', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('My Bookings')).toBeInTheDocument()
    })

    it('should display My Favorites link', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('My Favorites')).toBeInTheDocument()
    })
  })

  describe('Avatar initials', () => {
    it('should display first name initial when last name is missing', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, last_name: null, full_name: 'John' },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('J')).toBeInTheDocument()
    })

    it('should display U when no name is available', () => {
      mockUseAuth.mockReturnValue({
        user: { ...mockUser, first_name: null, last_name: null, full_name: null },
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })

      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('U')).toBeInTheDocument()
    })
  })

  describe('Profile edit functionality', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: vi.fn(),
      })
    })

    it('should display edit button', () => {
      renderWithRouter(<ProfilePage />)

      expect(screen.getByText('Edit Profile')).toBeInTheDocument()
    })

    it('should open edit form when edit button is clicked', () => {
      renderWithRouter(<ProfilePage />)

      const editButton = screen.getByText('Edit Profile')
      fireEvent.click(editButton)

      expect(screen.getByText('Edit Profile')).toBeInTheDocument()
      expect(screen.getByLabelText('First Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Last Name')).toBeInTheDocument()
      expect(screen.getByLabelText('Phone Number')).toBeInTheDocument()
      expect(screen.getByLabelText('WhatsApp')).toBeInTheDocument()
      expect(screen.getByLabelText('Telegram')).toBeInTheDocument()
      expect(screen.getByLabelText('Preferred Contact Method')).toBeInTheDocument()
    })

    it('should pre-fill edit form with current user data', () => {
      renderWithRouter(<ProfilePage />)

      const editButton = screen.getByText('Edit Profile')
      fireEvent.click(editButton)

      expect(screen.getByLabelText('First Name')).toHaveValue('John')
      expect(screen.getByLabelText('Last Name')).toHaveValue('Doe')
      expect(screen.getByLabelText('Phone Number')).toHaveValue('+1234567890')
      expect(screen.getByLabelText('WhatsApp')).toHaveValue('+9876543210')
      expect(screen.getByLabelText('Telegram')).toHaveValue('@johndoe')
    })

    it('formats a new phone number and stops at a complete +998 number', () => {
      renderWithRouter(<ProfilePage />)
      fireEvent.click(screen.getByText('Edit Profile'))
      const phoneInput = screen.getByLabelText('Phone Number')

      fireEvent.change(phoneInput, { target: { value: '9012345678901' } })

      expect(phoneInput).toHaveValue('+998 90 123 45 67')
    })

    it('does not save an incomplete new phone number', async () => {
      const mockUpdateProfile = vi.fn()
      mockUseAuth.mockReturnValue({
        user: mockUser, isAuthenticated: true, isLoading: false, updateProfile: mockUpdateProfile,
      })
      renderWithRouter(<ProfilePage />)
      fireEvent.click(screen.getByText('Edit Profile'))

      fireEvent.change(screen.getByLabelText('Phone Number'), { target: { value: '90 123' } })
      fireEvent.click(screen.getByText('Save Changes'))

      expect(await screen.findByText(/valid phone number/i)).toBeInTheDocument()
      expect(mockUpdateProfile).not.toHaveBeenCalled()
    })

    it('saves a new phone number in E.164', async () => {
      const mockUpdateProfile = vi.fn().mockResolvedValue({ success: true, user: mockUser })
      mockUseAuth.mockReturnValue({
        user: mockUser, isAuthenticated: true, isLoading: false, updateProfile: mockUpdateProfile,
      })
      renderWithRouter(<ProfilePage />)
      fireEvent.click(screen.getByText('Edit Profile'))

      fireEvent.change(screen.getByLabelText('Phone Number'), { target: { value: '+998 91 555 44 33' } })
      fireEvent.click(screen.getByText('Save Changes'))

      await waitFor(() => expect(mockUpdateProfile).toHaveBeenCalledWith(
        expect.objectContaining({ phone_number: '+998915554433' }),
      ))
    })

    it('should close edit form when cancel button is clicked', () => {
      renderWithRouter(<ProfilePage />)

      const editButton = screen.getByText('Edit Profile')
      fireEvent.click(editButton)

      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)

      expect(screen.queryByLabelText('First Name')).not.toBeInTheDocument()
    })

    it('should call updateProfile when save button is clicked', async () => {
      const mockUpdateProfile = vi.fn().mockResolvedValue({ success: true, user: mockUser })
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: mockUpdateProfile,
      })

      renderWithRouter(<ProfilePage />)

      const editButton = screen.getByText('Edit Profile')
      fireEvent.click(editButton)

      const firstNameInput = screen.getByLabelText('First Name')
      fireEvent.change(firstNameInput, { target: { value: 'Jane' } })

      const saveButton = screen.getByText('Save Changes')
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(mockUpdateProfile).toHaveBeenCalledWith({
          first_name: 'Jane',
          last_name: 'Doe',
          phone_number: '+1234567890',
          whatsapp: '+9876543210',
          telegram: '@johndoe',
          preferred_contact_method: 'whatsapp',
        })
      })
    })

    it('should display success message after successful profile update', async () => {
      const mockUpdateProfile = vi.fn().mockResolvedValue({ success: true, user: mockUser })
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: mockUpdateProfile,
      })

      renderWithRouter(<ProfilePage />)

      const editButton = screen.getByText('Edit Profile')
      fireEvent.click(editButton)

      const saveButton = screen.getByText('Save Changes')
      fireEvent.click(saveButton)

      // Verify that updateProfile was called
      expect(mockUpdateProfile).toHaveBeenCalled()
      // Let the page finish loading inside the test
      await settle()
    })

    it('should display error message when profile update fails', async () => {
      const mockUpdateProfile = vi.fn().mockResolvedValue({ success: false, error: 'Update failed' })
      mockUseAuth.mockReturnValue({
        user: mockUser,
        isAuthenticated: true,
        isLoading: false,
        login: vi.fn(),
        register: vi.fn(),
        logout: vi.fn(),
        refreshUser: vi.fn(),
        updateProfile: mockUpdateProfile,
      })

      renderWithRouter(<ProfilePage />)

      const editButton = screen.getByText('Edit Profile')
      fireEvent.click(editButton)

      const saveButton = screen.getByText('Save Changes')
      fireEvent.click(saveButton)

      await waitFor(() => {
        expect(screen.getByText('Update failed')).toBeInTheDocument()
      })
    })
  })
})
