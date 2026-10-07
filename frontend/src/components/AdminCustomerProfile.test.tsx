import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { AdminCustomerProfile } from './AdminCustomerProfile'
import { adminAdapter } from '../adapters/adminAdapter'
import { MemoryRouter, Route, Routes } from 'react-router-dom'

// Mock the admin adapter
vi.mock('../adapters/adminAdapter', () => ({
  adminAdapter: {
    getCustomerProfile: vi.fn(),
    createInternalNote: vi.fn(),
    updateInternalNote: vi.fn(),
    deleteInternalNote: vi.fn(),
  },
}))

// Mock react-router-dom
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ customerId: '1' }),
  }
})

describe('AdminCustomerProfile', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockCustomerProfile = {
    customer: {
      id: 1,
      email: 'john@example.com',
      first_name: 'John',
      last_name: 'Doe',
      full_name: 'John Doe',
      phone_number: '+998901234567',
      whatsapp: '+998901234567',
      telegram: '@johndoe',
      preferred_contact_method: 'email',
      date_joined: '2024-01-01T00:00:00Z',
      last_login: '2024-09-15T10:30:00Z',
      is_active: true,
      email_verified: true,
      phone_verified: true,
    },
    bookings: [
      {
        id: 1,
        reference_code: 'ABC123',
        status: 'confirmed',
        payment_status: 'paid',
        check_in: '2024-10-01T00:00:00Z',
        check_out: '2024-10-03T00:00:00Z',
        number_of_nights: 2,
        total_price: 200,
        currency: 'USD',
        property_name: 'Tashkent Hotel',
        property_city: 'Tashkent',
        created_at: '2024-09-01T00:00:00Z',
      },
    ],
    payments: [
      {
        id: 1,
        booking_id: 1,
        provider: 'payme',
        amount: 200,
        currency: 'USD',
        status: 'paid',
        created_at: '2024-09-01T00:00:00Z',
      },
    ],
    internal_notes: [
      {
        id: 1,
        customer: 1,
        author: 10,
        author_name: 'Admin User',
        author_email: 'admin@example.com',
        note: 'VIP customer - provide special assistance',
        created_at: '2024-09-10T10:00:00Z',
        updated_at: '2024-09-10T10:00:00Z',
      },
    ],
    last_activity: '2024-09-15T10:30:00Z',
  }

  const renderWithRouter = (component: React.ReactElement) => {
    return render(
      <MemoryRouter initialEntries={['/admin/customers/1']}>
        <Routes>
          <Route path="/admin/customers/:customerId" element={component} />
        </Routes>
      </MemoryRouter>
    )
  }

  it('should render loading state', () => {
    ;(adminAdapter.getCustomerProfile as any).mockImplementation(() => new Promise(() => {}))

    renderWithRouter(<AdminCustomerProfile />)

    expect(screen.getByText('Loading customer profile...')).toBeInTheDocument()
  })

  it('should render customer profile with header information', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    expect(screen.getByText('ID: 1')).toBeInTheDocument()
    expect(screen.getByText('john@example.com')).toBeInTheDocument()
    // The mock uses the same number for phone and WhatsApp, so check each row
    const phoneRow = screen.getByText('Phone:').closest('.contact-item') as HTMLElement
    expect(within(phoneRow).getByText('+998901234567')).toBeInTheDocument()
    const whatsappRow = screen.getByText('WhatsApp:').closest('.contact-item') as HTMLElement
    expect(within(whatsappRow).getByText('+998901234567')).toBeInTheDocument()
  })

  it('should render back button and navigate to admin dashboard', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByLabelText('Back to admin dashboard')).toBeInTheDocument()
    })

    const backButton = screen.getByLabelText('Back to admin dashboard')
    fireEvent.click(backButton)

    expect(mockNavigate).toHaveBeenCalledWith('/admin')
  })

  it('should render contact buttons with correct links', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Check email link
    const emailLink = screen.getByLabelText('Send email to john@example.com')
    expect(emailLink).toBeInTheDocument()
    expect(emailLink).toHaveAttribute('href', 'mailto:john@example.com')

    // Check phone link
    const phoneLink = screen.getByLabelText('Call +998901234567')
    expect(phoneLink).toBeInTheDocument()
    expect(phoneLink).toHaveAttribute('href', 'tel:+998901234567')

    // Check WhatsApp link
    const whatsappLink = screen.getByLabelText('Open WhatsApp chat with +998901234567')
    expect(whatsappLink).toBeInTheDocument()
    expect(whatsappLink).toHaveAttribute('href', 'https://wa.me/998901234567')

    // Check Telegram link
    const telegramLink = screen.getByLabelText('Open Telegram chat with @johndoe')
    expect(telegramLink).toBeInTheDocument()
    expect(telegramLink).toHaveAttribute('href', 'https://t.me/johndoe')
  })

  it('should render account status badges', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    expect(screen.getByText('Active')).toBeInTheDocument()
    const emailStatus = screen.getByText('Email Verified:').closest('.status-item') as HTMLElement
    expect(within(emailStatus).getByText('Verified')).toBeInTheDocument()
    const phoneStatus = screen.getByText('Phone Verified:').closest('.status-item') as HTMLElement
    expect(within(phoneStatus).getByText('Verified')).toBeInTheDocument()
  })

  it('should render tabs with correct counts', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Bookings (1)')).toBeInTheDocument()
    })

    expect(screen.getByText('Payments (1)')).toBeInTheDocument()
    expect(screen.getByText('Internal Notes (1)')).toBeInTheDocument()
  })

  it('should render bookings tab with table', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Bookings (1)')).toBeInTheDocument()
    })

    // Click on bookings tab
    const bookingsTab = screen.getByText('Bookings (1)')
    fireEvent.click(bookingsTab)

    await waitFor(() => {
      expect(screen.getByText('ABC123')).toBeInTheDocument()
    })

    expect(screen.getByText('Tashkent Hotel')).toBeInTheDocument()
    expect(screen.getByText('Tashkent')).toBeInTheDocument()
  })

  it('should render payments tab with table', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Payments (1)')).toBeInTheDocument()
    })

    // Click on payments tab
    const paymentsTab = screen.getByText('Payments (1)')
    fireEvent.click(paymentsTab)

    await waitFor(() => {
      expect(screen.getByText('payme')).toBeInTheDocument()
    })

    expect(screen.getByText('$200.00')).toBeInTheDocument()
  })

  it('should render internal notes tab with note list', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Internal Notes (1)')).toBeInTheDocument()
    })

    // Click on notes tab
    const notesTab = screen.getByText('Internal Notes (1)')
    fireEvent.click(notesTab)

    await waitFor(() => {
      expect(screen.getByText('VIP customer - provide special assistance')).toBeInTheDocument()
    })

    expect(screen.getByText('Admin User')).toBeInTheDocument()
    expect(screen.getByText('admin@example.com')).toBeInTheDocument()
  })

  it('should handle booking filter change', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Bookings (1)')).toBeInTheDocument()
    })

    const filterSelect = screen.getByLabelText('Filter bookings by status')
    fireEvent.change(filterSelect, { target: { value: 'upcoming' } })

    await waitFor(() => {
      expect(adminAdapter.getCustomerProfile).toHaveBeenCalledWith(
        1,
        expect.objectContaining({ booking_filter: 'upcoming' })
      )
    })
  })

  it('should handle adding internal note', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    ;(adminAdapter.createInternalNote as any).mockResolvedValueOnce({
      data: {
        id: 2,
        customer: 1,
        author: 10,
        author_name: 'Admin User',
        author_email: 'admin@example.com',
        note: 'New note',
        created_at: '2024-09-16T10:00:00Z',
        updated_at: '2024-09-16T10:00:00Z',
      },
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Internal Notes (1)')).toBeInTheDocument()
    })

    // Click on notes tab
    const notesTab = screen.getByText('Internal Notes (1)')
    fireEvent.click(notesTab)

    await waitFor(() => {
      expect(screen.getByLabelText('New internal note')).toBeInTheDocument()
    })

    const noteTextarea = screen.getByLabelText('New internal note')
    fireEvent.change(noteTextarea, { target: { value: 'New note' } })

    const addButton = screen.getByLabelText('Add note')
    fireEvent.click(addButton)

    await waitFor(() => {
      expect(adminAdapter.createInternalNote).toHaveBeenCalledWith(
        1,
        { note: 'New note' }
      )
    })
  })

  it('should handle editing internal note', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    ;(adminAdapter.updateInternalNote as any).mockResolvedValueOnce({
      data: {
        id: 1,
        customer: 1,
        author: 10,
        author_name: 'Admin User',
        author_email: 'admin@example.com',
        note: 'Updated note',
        created_at: '2024-09-10T10:00:00Z',
        updated_at: '2024-09-16T10:00:00Z',
      },
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Internal Notes (1)')).toBeInTheDocument()
    })

    // Click on notes tab
    const notesTab = screen.getByText('Internal Notes (1)')
    fireEvent.click(notesTab)

    await waitFor(() => {
      expect(screen.getByText('VIP customer - provide special assistance')).toBeInTheDocument()
    })

    // Click edit button
    const editButton = screen.getByLabelText(/Edit note from/)
    fireEvent.click(editButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/Edit note from/)).toBeInTheDocument()
    })

    const editTextarea = screen.getByLabelText(/Edit note from/)
    fireEvent.change(editTextarea, { target: { value: 'Updated note' } })

    const saveButton = screen.getByLabelText('Save note')
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(adminAdapter.updateInternalNote).toHaveBeenCalledWith(
        1,
        1,
        { note: 'Updated note' }
      )
    })
  })

  it('should handle deleting internal note', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    ;(adminAdapter.deleteInternalNote as any).mockResolvedValueOnce({
      data: null,
      error: null,
    })

    // Mock window.confirm
    global.confirm = vi.fn(() => true)

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Internal Notes (1)')).toBeInTheDocument()
    })

    // Click on notes tab
    const notesTab = screen.getByText('Internal Notes (1)')
    fireEvent.click(notesTab)

    await waitFor(() => {
      expect(screen.getByText('VIP customer - provide special assistance')).toBeInTheDocument()
    })

    // Click delete button
    const deleteButton = screen.getByLabelText(/Delete note from/)
    fireEvent.click(deleteButton)

    expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete this note?')

    await waitFor(() => {
      expect(adminAdapter.deleteInternalNote).toHaveBeenCalledWith(1, 1)
    })
  })

  it('should render error state', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: null,
      error: 'Failed to load customer profile',
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load customer profile')).toBeInTheDocument()
    })
  })

  it('should render empty state when customer not found', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: null,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Customer not found.')).toBeInTheDocument()
    })
  })

  it('should render empty bookings state', async () => {
    const emptyProfile = {
      ...mockCustomerProfile,
      bookings: [],
    }

    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: emptyProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Bookings (0)')).toBeInTheDocument()
    })

    const bookingsTab = screen.getByText('Bookings (0)')
    fireEvent.click(bookingsTab)

    await waitFor(() => {
      expect(screen.getByText('No bookings found for this customer.')).toBeInTheDocument()
    })
  })

  it('should render empty payments state', async () => {
    const emptyProfile = {
      ...mockCustomerProfile,
      payments: [],
    }

    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: emptyProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Payments (0)')).toBeInTheDocument()
    })

    const paymentsTab = screen.getByText('Payments (0)')
    fireEvent.click(paymentsTab)

    await waitFor(() => {
      expect(screen.getByText('No payments found for this customer.')).toBeInTheDocument()
    })
  })

  it('should render empty notes state', async () => {
    const emptyProfile = {
      ...mockCustomerProfile,
      internal_notes: [],
    }

    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: emptyProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Internal Notes (0)')).toBeInTheDocument()
    })

    const notesTab = screen.getByText('Internal Notes (0)')
    fireEvent.click(notesTab)

    await waitFor(() => {
      expect(screen.getByText('No internal notes for this customer.')).toBeInTheDocument()
    })
  })

  it('should not render WhatsApp/Telegram links when not provided', async () => {
    const profileWithoutSocial = {
      ...mockCustomerProfile,
      customer: {
        ...mockCustomerProfile.customer,
        whatsapp: undefined,
        telegram: undefined,
      },
    }

    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: profileWithoutSocial,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    expect(screen.queryByLabelText(/Open WhatsApp chat/)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/Open Telegram chat/)).not.toBeInTheDocument()
  })

  it('should not allow adding an empty note', async () => {
    ;(adminAdapter.getCustomerProfile as any).mockResolvedValueOnce({
      data: mockCustomerProfile,
      error: null,
    })

    renderWithRouter(<AdminCustomerProfile />)

    await waitFor(() => {
      expect(screen.getByText('Internal Notes (1)')).toBeInTheDocument()
    })

    // Click on notes tab
    const notesTab = screen.getByText('Internal Notes (1)')
    fireEvent.click(notesTab)

    await waitFor(() => {
      expect(screen.getByLabelText('New internal note')).toBeInTheDocument()
    })

    // An empty or whitespace-only note cannot be submitted: the button stays disabled
    const addButton = screen.getByLabelText('Add note')
    expect(addButton).toBeDisabled()
    fireEvent.change(screen.getByLabelText('New internal note'), { target: { value: '   ' } })
    expect(addButton).toBeDisabled()
    fireEvent.click(addButton)
    expect(adminAdapter.createInternalNote).not.toHaveBeenCalled()
  })
})

// Total tests: 21 for AdminCustomerProfile component
