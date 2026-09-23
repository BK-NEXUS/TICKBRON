import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminCustomersList } from './AdminCustomersList'
import { adminAdapter } from '../adapters/adminAdapter'

// Mock the admin adapter
vi.mock('../adapters/adminAdapter', () => ({
  adminAdapter: {
    getCustomers: vi.fn(),
  },
}))

describe('AdminCustomersList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockCustomersResponse = {
    count: 2,
    next: null,
    previous: null,
    results: [
      {
        id: 1,
        registration_date: '2024-01-01T00:00:00Z',
        full_name: 'John Doe',
        phone: '+998901234567',
        email: 'john@example.com',
        whatsapp: '+998901234567',
        telegram: '@johndoe',
        preferred_contact_method: 'email',
        total_booking_count: 5,
        last_booking_date: '2024-09-01T00:00:00Z',
        total_amount_paid: 1500,
        customer_status: 'active',
      },
      {
        id: 2,
        registration_date: '2024-02-01T00:00:00Z',
        full_name: 'Jane Smith',
        phone: '+998907654321',
        email: 'jane@example.com',
        whatsapp: null,
        telegram: null,
        preferred_contact_method: 'phone',
        total_booking_count: 2,
        last_booking_date: '2024-08-15T00:00:00Z',
        total_amount_paid: 800,
        customer_status: 'active',
      },
    ],
  }

  it('should render the customers list with header', () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    expect(screen.getByText('Customers Directory')).toBeInTheDocument()
    expect(screen.getByText('View and search customer information with booking history')).toBeInTheDocument()
  })

  it('should render search bar and controls', () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    expect(screen.getByLabelText('Search customers')).toBeInTheDocument()
    expect(screen.getByLabelText('Sort customers by')).toBeInTheDocument()
    expect(screen.getByLabelText('Items per page')).toBeInTheDocument()
  })

  it('should render customers table with data', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('Total customers: 2')).toBeInTheDocument()
    })

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('jane@example.com')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument() // booking count
    expect(screen.getByText('2')).toBeInTheDocument() // booking count
  })

  it('should render loading state', () => {
    ;(adminAdapter.getCustomers as any).mockImplementation(() => new Promise(() => {}))

    render(<AdminCustomersList />)

    expect(screen.getByText('Loading customers...')).toBeInTheDocument()
  })

  it('should render empty state when no customers', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: { count: 0, next: null, previous: null, results: [] },
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('No customers found.')).toBeInTheDocument()
    })
  })

  it('should render error state', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: null,
      error: 'Failed to load customers',
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load customers')).toBeInTheDocument()
    })
  })

  it('should handle search input change', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    const searchInput = screen.getByLabelText('Search customers')
    fireEvent.change(searchInput, { target: { value: 'John' } })

    await waitFor(() => {
      expect(adminAdapter.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'John' })
      )
    })
  })

  it('should handle sort field change', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    const sortSelect = screen.getByLabelText('Sort customers by')
    fireEvent.change(sortSelect, { target: { value: 'total_booking_count' } })

    await waitFor(() => {
      expect(adminAdapter.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ sort_by: 'total_booking_count' })
      )
    })
  })

  it('should handle sort order toggle', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    const sortOrderButton = screen.getByLabelText(/Sort order:/)
    fireEvent.click(sortOrderButton)

    await waitFor(() => {
      expect(adminAdapter.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ sort_order: 'asc' })
      )
    })
  })

  it('should handle page size change', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    const pageSizeSelect = screen.getByLabelText('Items per page')
    fireEvent.change(pageSizeSelect, { target: { value: '50' } })

    await waitFor(() => {
      expect(adminAdapter.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ page_size: 50 })
      )
    })
  })

  it('should handle pagination - next page', async () => {
    const paginatedResponse = {
      count: 50,
      next: 'http://test-api/api/v1/admin-panel/customers/?page=2',
      previous: null,
      results: mockCustomersResponse.results,
    }

    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: paginatedResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument()
    })

    const nextButton = screen.getByLabelText('Next page')
    fireEvent.click(nextButton)

    await waitFor(() => {
      expect(adminAdapter.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 })
      )
    })
  })

  it('should handle pagination - previous page', async () => {
    const paginatedResponse = {
      count: 50,
      next: null,
      previous: 'http://test-api/api/v1/admin-panel/customers/?page=1',
      results: mockCustomersResponse.results,
    }

    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: paginatedResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    // Start on page 2
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: paginatedResponse,
      error: null,
    })

    await waitFor(() => {
      expect(screen.getByText('Page 2 of 3')).toBeInTheDocument()
    })

    const prevButton = screen.getByLabelText('Previous page')
    fireEvent.click(prevButton)

    await waitFor(() => {
      expect(adminAdapter.getCustomers).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1 })
      )
    })
  })

  it('should disable pagination buttons when on first/last page', async () => {
    const singlePageResponse = {
      count: 2,
      next: null,
      previous: null,
      results: mockCustomersResponse.results,
    }

    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: singlePageResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 1')).toBeInTheDocument()
    })

    const prevButton = screen.getByLabelText('Previous page')
    const nextButton = screen.getByLabelText('Next page')

    expect(prevButton).toBeDisabled()
    expect(nextButton).toBeDisabled()
  })

  it('should display customer data in table columns', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument()
    })

    // Check table headers
    expect(screen.getByText('ID')).toBeInTheDocument()
    expect(screen.getByText('Registration Date')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Phone')).toBeInTheDocument()
    expect(screen.getByText('Email')).toBeInTheDocument()
    expect(screen.getByText('WhatsApp')).toBeInTheDocument()
    expect(screen.getByText('Telegram')).toBeInTheDocument()
    expect(screen.getByText('Preferred Contact')).toBeInTheDocument()
    expect(screen.getByText('Booking Count')).toBeInTheDocument()
    expect(screen.getByText('Last Booking Date')).toBeInTheDocument()
    expect(screen.getByText('Total Paid')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
  })

  it('should display N/A for missing contact information', async () => {
    const customersWithMissingData = {
      count: 1,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          registration_date: '2024-01-01T00:00:00Z',
          full_name: 'John Doe',
          phone: '+998901234567',
          email: 'john@example.com',
          whatsapp: null,
          telegram: null,
          preferred_contact_method: 'email',
          total_booking_count: 0,
          last_booking_date: null,
          total_amount_paid: 0,
          customer_status: 'active',
        },
      ],
    }

    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: customersWithMissingData,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('N/A')).toBeInTheDocument()
    })
  })

  it('should display correct status badges', async () => {
    const customersWithStatuses = {
      count: 2,
      next: null,
      previous: null,
      results: [
        {
          id: 1,
          registration_date: '2024-01-01T00:00:00Z',
          full_name: 'John Doe',
          phone: '+998901234567',
          email: 'john@example.com',
          whatsapp: '+998901234567',
          telegram: '@johndoe',
          preferred_contact_method: 'email',
          total_booking_count: 5,
          last_booking_date: '2024-09-01T00:00:00Z',
          total_amount_paid: 1500,
          customer_status: 'active',
        },
        {
          id: 2,
          registration_date: '2024-02-01T00:00:00Z',
          full_name: 'Jane Smith',
          phone: '+998907654321',
          email: 'jane@example.com',
          whatsapp: null,
          telegram: null,
          preferred_contact_method: 'phone',
          total_booking_count: 0,
          last_booking_date: null,
          total_amount_paid: 0,
          customer_status: 'inactive',
        },
      ],
    }

    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: customersWithStatuses,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })
  })

  it('should format currency correctly', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('$1,500.00')).toBeInTheDocument()
      expect(screen.getByText('$800.00')).toBeInTheDocument()
    })
  })

  it('should format dates correctly', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('Jan 1, 2024')).toBeInTheDocument()
      expect(screen.getByText('Sep 1, 2024')).toBeInTheDocument()
    })
  })

  it('should display contact method labels correctly', async () => {
    ;(adminAdapter.getCustomers as any).mockResolvedValueOnce({
      data: mockCustomersResponse,
      error: null,
    })

    render(<AdminCustomersList />)

    await waitFor(() => {
      expect(screen.getByText('Email')).toBeInTheDocument()
      expect(screen.getByText('Phone')).toBeInTheDocument()
    })
  })
})

// Total tests: 20 for AdminCustomersList component
