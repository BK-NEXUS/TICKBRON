import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminPropertyModeration } from './AdminPropertyModeration'
import { adminAdapter } from '../adapters/adminAdapter'

// Mock adminAdapter
vi.mock('../adapters/adminAdapter')

describe('AdminPropertyModeration', () => {
  const mockProperties = [
    {
      id: 1,
      owner: 2,
      owner_name: 'Hotel Owner',
      status: 'pending',
      city: 'Tashkent',
      country: 'Uzbekistan',
      address_line1: '123 Main St',
      base_price: 100,
      currency: 'USD',
      max_guests: 4,
      bedrooms: 2,
      bathrooms: 1,
      has_wifi: true,
      has_parking: true,
      has_ac: true,
      has_heating: true,
      has_elevator: false,
      created_at: '2024-01-01T00:00:00Z',
    },
    {
      id: 2,
      owner: 3,
      owner_name: 'Another Owner',
      status: 'active',
      city: 'Samarkand',
      country: 'Uzbekistan',
      address_line1: '456 Oak St',
      base_price: 150,
      currency: 'USD',
      max_guests: 6,
      bedrooms: 3,
      bathrooms: 2,
      has_wifi: true,
      has_parking: false,
      has_ac: true,
      has_heating: true,
      has_elevator: true,
      approved_by: 1,
      approved_at: '2024-01-02T00:00:00Z',
      created_at: '2024-01-01T00:00:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render property moderation page', () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    expect(screen.getByText('Property Moderation')).toBeInTheDocument()
    expect(screen.getByText('Review and moderate property submissions')).toBeInTheDocument()
  })

  it('should load properties on mount', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(adminAdapter.getProperties).toHaveBeenCalled()
    })
  })

  it('should display properties list', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Tashkent, Uzbekistan')).toBeInTheDocument()
      expect(screen.getByText('Samarkand, Uzbekistan')).toBeInTheDocument()
    })
  })

  it('should show approve button for pending properties', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const approveButtons = screen.getAllByText('Approve')
      expect(approveButtons.length).toBeGreaterThan(0)
    })
  })

  it('should show reject button for pending properties', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const rejectButtons = screen.getAllByText('Reject')
      expect(rejectButtons.length).toBeGreaterThan(0)
    })
  })

  it('should show suspend button for active properties', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const suspendButtons = screen.getAllByText('Suspend')
      expect(suspendButtons.length).toBeGreaterThan(0)
    })
  })

  it('should show reactivate button for suspended properties', async () => {
    const suspendedProperties = [
      {
        ...mockProperties[0],
        status: 'suspended',
      },
    ]

    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: suspendedProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Reactivate')).toBeInTheDocument()
    })
  })

  it('should open reject modal when reject button is clicked', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const rejectButtons = screen.getAllByText('Reject')
      expect(rejectButtons.length).toBeGreaterThan(0)
    })
  })

  it('should call approveProperty when approve button is clicked', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    ;(adminAdapter.approveProperty as any).mockResolvedValueOnce({
      data: { ...mockProperties[0], status: 'active' },
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const approveButtons = screen.getAllByText('Approve')
      fireEvent.click(approveButtons[0])
    })

    await waitFor(() => {
      expect(adminAdapter.approveProperty).toHaveBeenCalledWith(1, {})
    })
  })

  it('should call approveProperty with rejection reason when reject is submitted', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    ;(adminAdapter.approveProperty as any).mockResolvedValueOnce({
      data: { ...mockProperties[0], status: 'rejected', rejection_reason: 'Invalid information' },
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const rejectButtons = screen.getAllByText('Reject')
      expect(rejectButtons.length).toBeGreaterThan(0)
    })
  })

  it('should call suspendProperty when suspend button is clicked', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    ;(adminAdapter.suspendProperty as any).mockResolvedValueOnce({
      data: { ...mockProperties[1], status: 'suspended' },
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const suspendButtons = screen.getAllByText('Suspend')
      fireEvent.click(suspendButtons[0])
    })

    await waitFor(() => {
      expect(adminAdapter.suspendProperty).toHaveBeenCalledWith(2)
    })
  })

  it('should display loading state while loading', () => {
    ;(adminAdapter.getProperties as any).mockImplementation(
      () => new Promise(() => {})
    )

    render(<AdminPropertyModeration />)

    expect(screen.getByText('Loading properties...')).toBeInTheDocument()
  })

  it('should display empty state when no properties', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: [],
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('No properties found for moderation.')).toBeInTheDocument()
    })
  })

  it('should display error message on API failure', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: null,
      error: 'Failed to load properties',
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load properties')).toBeInTheDocument()
    })
  })

  it('should close reject modal when cancel is clicked', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const rejectButtons = screen.getAllByText('Reject')
      fireEvent.click(rejectButtons[0])
    })

    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)
    })

    await waitFor(() => {
      expect(screen.queryByText('Reject Property')).not.toBeInTheDocument()
    })
  })

  it('should display property amenities tags', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Property Moderation')).toBeInTheDocument()
    })
  })

  it('should display property status badges', async () => {
    ;(adminAdapter.getProperties as any).mockResolvedValueOnce({
      data: mockProperties,
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('PENDING')).toBeInTheDocument()
      expect(screen.getByText('ACTIVE')).toBeInTheDocument()
    })
  })
})
