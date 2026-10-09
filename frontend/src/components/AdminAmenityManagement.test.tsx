import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminAmenityManagement } from './AdminAmenityManagement'
import { adminAdapter } from '../adapters/adminAdapter'
import { settle } from '../test/utils'

// Mock adminAdapter
vi.mock('../adapters/adminAdapter')

describe('AdminAmenityManagement', () => {
  const mockAmenities = [
    {
      id: 1,
      category: 1,
      category_name: 'Kitchen',
      name: 'WiFi',
      slug: 'wifi',
      description: 'Wireless internet',
      icon: 'wifi',
      is_searchable: true,
      sort_order: 1,
      created_at: '2024-01-01T00:00:00Z',
    },
  ]

  const mockCategories = [
    {
      id: 1,
      name: 'Kitchen',
      slug: 'kitchen',
      description: 'Kitchen amenities',
      icon: 'kitchen',
      sort_order: 1,
      created_at: '2024-01-01T00:00:00Z',
    },
  ]

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render amenity management page', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await settle()

    expect(screen.getByText('Amenity Management')).toBeInTheDocument()
    expect(screen.getByText('Manage amenity categories and amenities')).toBeInTheDocument()
  })

  it('should load amenities on mount', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(adminAdapter.getAmenities).toHaveBeenCalled()
    })
  })

  it('should load categories when switching to categories view', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.getAmenityCategories as never).mockResolvedValueOnce({
      data: mockCategories,
      error: null,
    })

    render(<AdminAmenityManagement />)

    const categoriesTab = screen.getByText('Categories')
    fireEvent.click(categoriesTab)

    await waitFor(() => {
      expect(adminAdapter.getAmenityCategories).toHaveBeenCalled()
    })
  })

  it('should display amenities list', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Amenity Management')).toBeInTheDocument()
    })
  })

  it('should show create button', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Create Amenity')).toBeInTheDocument()
    })
  })

  it('should open create form when create button is clicked', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Amenity Management')).toBeInTheDocument()
    })
  })

  it('should call createAmenity when form is submitted', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.createAmenity as never).mockResolvedValueOnce({
      data: { ...mockAmenities[0], id: 2 },
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Amenity Management')).toBeInTheDocument()
    })
  })

  it('should call updateAmenity when edit form is submitted', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.updateAmenity as never).mockResolvedValueOnce({
      data: { ...mockAmenities[0], name: 'WiFi Updated' },
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit')
      expect(editButtons.length).toBeGreaterThan(0)
    })
  })

  it('should call deleteAmenity when delete button is clicked', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.deleteAmenity as never).mockResolvedValueOnce({
      data: null,
      error: null,
    })

    // Mock window.confirm
    global.confirm = vi.fn(() => true)

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const deleteButtons = screen.getAllByText('Delete')
      expect(deleteButtons.length).toBeGreaterThan(0)
    })
  })

  it('should display empty state when no amenities', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: [],
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('No amenities found.')).toBeInTheDocument()
    })
  })

  it('should display loading state while loading', () => {
    (adminAdapter.getAmenities as never).mockImplementation(
      () => new Promise(() => {})
    )

    render(<AdminAmenityManagement />)

    expect(screen.getByText('Loading amenities...')).toBeInTheDocument()
  })

  it('should display error message on API failure', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: null,
      error: 'Failed to load amenities',
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load amenities')).toBeInTheDocument()
    })
  })

  it('should close form when cancel is clicked', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const createButton = screen.getByText('Create Amenity')
      fireEvent.click(createButton)
    })

    await waitFor(() => {
      expect(screen.getByLabelText(/Category/i)).toBeInTheDocument()
    })

    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)
    })

    await waitFor(() => {
      expect(screen.queryByLabelText(/Category/i)).not.toBeInTheDocument()
    })
  })

  it('should display searchable badge for searchable amenities', async () => {
    (adminAdapter.getAmenities as never).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Searchable')).toBeInTheDocument()
    })
  })
})
