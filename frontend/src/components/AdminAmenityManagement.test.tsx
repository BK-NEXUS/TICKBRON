import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminAmenityManagement } from './AdminAmenityManagement'
import { adminAdapter } from '../adapters/adminAdapter'

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

  it('should render amenity management page', () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    expect(screen.getByText('Amenity Management')).toBeInTheDocument()
    expect(screen.getByText('Manage amenity categories and amenities')).toBeInTheDocument()
  })

  it('should load amenities on mount', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(adminAdapter.getAmenities).toHaveBeenCalled()
    })
  })

  it('should load categories when switching to categories view', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.getAmenityCategories as any).mockResolvedValueOnce({
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
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('WiFi')).toBeInTheDocument()
      expect(screen.getByText('Kitchen')).toBeInTheDocument()
    })
  })

  it('should show create button', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Create Amenity')).toBeInTheDocument()
    })
  })

  it('should open create form when create button is clicked', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const createButton = screen.getByText('Create Amenity')
      fireEvent.click(createButton)
    })

    await waitFor(() => {
      expect(screen.getByText('Create Amenity')).toBeInTheDocument()
      expect(screen.getByLabelText(/Category/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/Name/i)).toBeInTheDocument()
    })
  })

  it('should call createAmenity when form is submitted', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.createAmenity as any).mockResolvedValueOnce({
      data: { ...mockAmenities[0], id: 2 },
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const createButton = screen.getByText('Create Amenity')
      fireEvent.click(createButton)
    })

    await waitFor(() => {
      const categorySelect = screen.getByLabelText(/Category/i)
      fireEvent.change(categorySelect, { target: { value: '1' } })

      const nameInput = screen.getByLabelText(/Name/i)
      fireEvent.change(nameInput, { target: { value: 'Pool' } })

      const slugInput = screen.getByLabelText(/Slug/i)
      fireEvent.change(slugInput, { target: { value: 'pool' } })

      const submitButton = screen.getByText('Create')
      fireEvent.click(submitButton)
    })

    await waitFor(() => {
      expect(adminAdapter.createAmenity).toHaveBeenCalled()
    })
  })

  it('should call updateAmenity when edit form is submitted', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.updateAmenity as any).mockResolvedValueOnce({
      data: { ...mockAmenities[0], name: 'WiFi Updated' },
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const editButton = screen.getAllByText('Edit')[0]
      fireEvent.click(editButton)
    })

    await waitFor(() => {
      const nameInput = screen.getByLabelText(/Name/i)
      fireEvent.change(nameInput, { target: { value: 'WiFi Updated' } })

      const submitButton = screen.getByText('Update')
      fireEvent.click(submitButton)
    })

    await waitFor(() => {
      expect(adminAdapter.updateAmenity).toHaveBeenCalled()
    })
  })

  it('should call deleteAmenity when delete button is clicked', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    ;(adminAdapter.deleteAmenity as any).mockResolvedValueOnce({
      data: null,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const deleteButton = screen.getAllByText('Delete')[0]
      fireEvent.click(deleteButton)
    })

    await waitFor(() => {
      expect(adminAdapter.deleteAmenity).toHaveBeenCalledWith(1)
    })
  })

  it('should display empty state when no amenities', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: [],
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('No amenities found.')).toBeInTheDocument()
    })
  })

  it('should display loading state while loading', () => {
    ;(adminAdapter.getAmenities as any).mockImplementation(
      () => new Promise(() => {})
    )

    render(<AdminAmenityManagement />)

    expect(screen.getByText('Loading amenities...')).toBeInTheDocument()
  })

  it('should display error message on API failure', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: null,
      error: 'Failed to load amenities',
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load amenities')).toBeInTheDocument()
    })
  })

  it('should close form when cancel is clicked', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      const createButton = screen.getByText('Create Amenity')
      fireEvent.click(createButton)
    })

    await waitFor(() => {
      const cancelButton = screen.getByText('Cancel')
      fireEvent.click(cancelButton)
    })

    await waitFor(() => {
      expect(screen.queryByText('Create Amenity')).not.toBeInTheDocument()
    })
  })

  it('should display searchable badge for searchable amenities', async () => {
    ;(adminAdapter.getAmenities as any).mockResolvedValueOnce({
      data: mockAmenities,
      error: null,
    })

    render(<AdminAmenityManagement />)

    await waitFor(() => {
      expect(screen.getByText('Searchable')).toBeInTheDocument()
    })
  })
})
