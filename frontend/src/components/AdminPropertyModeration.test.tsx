import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminPropertyModeration } from './AdminPropertyModeration'
import { adminAdapter } from '../adapters/adminAdapter'
import { settle } from '../test/utils'

// Mock adminAdapter
vi.mock('../adapters/adminAdapter')
vi.mock('../adapters/geographyAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: {
    getCountries: vi.fn().mockResolvedValue({ data: [{ id: 1, code: 'UZ', currency: 'UZS', name_uz: 'Oʻzbekiston', name_ru: 'Узбекистан', name_en: 'Uzbekistan', hotel_count: 1 }], error: null }),
    getRegions: vi.fn().mockResolvedValue({ data: [{ id: 10, name_uz: 'Toshkent', name_ru: 'Ташкент', name_en: 'Tashkent', hotel_count: 1 }], error: null }),
  },
}))

/** The list comes a page at a time since the alphabet filter (2026-11-01) */
const asPage = <T,>(rows: T[]) => ({ count: rows.length, hasMore: false, results: rows })

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

  it('should render property moderation page', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await settle()

    expect(screen.getByText('Property Moderation')).toBeInTheDocument()
    expect(screen.getByText('Review and moderate property submissions')).toBeInTheDocument()
  })

  it('each property card has a location field for the Status section', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage([{ ...mockProperties[0], country_ref: 1, region_ref: 10 }, mockProperties[1]]),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => expect(screen.getAllByLabelText('Region')).toHaveLength(2))
    const [first, second] = screen.getAllByLabelText('Region')
    await waitFor(() => expect(first).toHaveValue('10'))
    expect(second).toHaveValue('')
  })

  it('should load properties on mount', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(adminAdapter.getProperties).toHaveBeenCalled()
    })
  })

  it('should display properties list', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Tashkent, Uzbekistan')).toBeInTheDocument()
      expect(screen.getByText('Samarkand, Uzbekistan')).toBeInTheDocument()
    })
  })

  it('should show approve button for pending properties', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const approveButtons = screen.getAllByText('Approve')
      expect(approveButtons.length).toBeGreaterThan(0)
    })
  })

  it('should show reject button for pending properties', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const rejectButtons = screen.getAllByText('Reject')
      expect(rejectButtons.length).toBeGreaterThan(0)
    })
  })

  it('should show suspend button for active properties', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
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

    ;(adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(suspendedProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Reactivate')).toBeInTheDocument()
    })
  })

  it('should open reject modal when reject button is clicked', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      const rejectButtons = screen.getAllByText('Reject')
      expect(rejectButtons.length).toBeGreaterThan(0)
    })
  })

  it('should call approveProperty when approve button is clicked', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    ;(adminAdapter.approveProperty as never).mockResolvedValueOnce({
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

  it('tells the admin which parts are missing when approval is refused', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({ data: asPage(mockProperties), error: null })
    ;(adminAdapter.approveProperty as never).mockResolvedValueOnce({
      data: null,
      error: 'Property is not ready to be listed',
      missing: ['room', 'photo'],
    })

    render(<AdminPropertyModeration />)
    fireEvent.click((await screen.findAllByText('Approve'))[0])

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Cannot approve yet. Still missing: a room, a photo.')
    await settle()
  })

  it('should call approveProperty with rejection reason when reject is submitted', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    ;(adminAdapter.approveProperty as never).mockResolvedValueOnce({
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
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    ;(adminAdapter.suspendProperty as never).mockResolvedValueOnce({
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
    (adminAdapter.getProperties as never).mockImplementation(
      () => new Promise(() => {})
    )

    render(<AdminPropertyModeration />)

    expect(screen.getByText('Loading properties...')).toBeInTheDocument()
  })

  it('should display empty state when no properties', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage([]),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('No properties found for moderation.')).toBeInTheDocument()
    })
  })

  it('should display error message on API failure', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: null,
      error: 'Failed to load properties',
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load properties')).toBeInTheDocument()
    })
  })

  it('should close reject modal when cancel is clicked', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
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
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      expect(screen.getByText('Property Moderation')).toBeInTheDocument()
    })
  })

  it('should display property status badges', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage(mockProperties),
      error: null,
    })

    render(<AdminPropertyModeration />)

    await waitFor(() => {
      // The labels are in the page language since 2026-11-01; a code the site does not know is shown as it came
      expect(screen.getByText('pending', { selector: '.property-status' })).toBeInTheDocument()
      expect(screen.getByText('Active', { selector: '.property-status' })).toBeInTheDocument()
    })
  })

  it('offers to approve and reject a new hotel, which starts as a draft', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage([{ ...mockProperties[0], status: 'draft' }]),
      error: null,
    })

    render(<AdminPropertyModeration />)

    expect(await screen.findByRole('button', { name: /^Approve/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^Reject/ })).toBeInTheDocument()
    expect(screen.getByText('Draft', { selector: '.property-status' })).toBeInTheDocument()
  })

  it('also offers the decision to a hotel waiting for approval', async () => {
    (adminAdapter.getProperties as never).mockResolvedValueOnce({
      data: asPage([{ ...mockProperties[0], status: 'pending_approval' }]),
      error: null,
    })

    render(<AdminPropertyModeration />)

    expect(await screen.findByRole('button', { name: /^Approve/ })).toBeInTheDocument()
  })

  it('asks the server for a letter, a status and a search, from page 1', async () => {
    (adminAdapter.getProperties as never).mockResolvedValue({ data: asPage(mockProperties), error: null })

    render(<AdminPropertyModeration />)
    await settle()
    fireEvent.click(screen.getByRole('button', { name: 'Names starting with G' }))
    await waitFor(() => expect(adminAdapter.getProperties).toHaveBeenLastCalledWith({ letter: 'G', status: undefined, search: '', page: 1 }))
    fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'draft' } })
    await waitFor(() => expect(adminAdapter.getProperties).toHaveBeenLastCalledWith({ letter: 'G', status: 'draft', search: '', page: 1 }))
  })
})
