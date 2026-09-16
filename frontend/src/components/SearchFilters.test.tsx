import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SearchFilters, FilterState } from './SearchFilters'

describe('SearchFilters', () => {
  const mockPropertyTypes = [
    { id: 1, name: 'Apartment', slug: 'apartment' },
    { id: 2, name: 'House', slug: 'house' },
    { id: 3, name: 'Villa', slug: 'villa' },
  ]

  const defaultFilters: FilterState = {
    property_type: undefined,
    min_price: undefined,
    max_price: undefined,
    amenities: [],
  }

  it('renders filter sections', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    expect(screen.getByText('Filters')).toBeInTheDocument()
    expect(screen.getByText('Property Type')).toBeInTheDocument()
    expect(screen.getByText('Price Range')).toBeInTheDocument()
    expect(screen.getByText('Amenities')).toBeInTheDocument()
  })

  it('renders property type options', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    expect(screen.getByLabelText('Apartment')).toBeInTheDocument()
    expect(screen.getByLabelText('House')).toBeInTheDocument()
    expect(screen.getByLabelText('Villa')).toBeInTheDocument()
  })

  it('handles property type selection', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const apartmentRadio = screen.getByLabelText('Apartment')
    fireEvent.click(apartmentRadio)

    expect(onFiltersChange).toHaveBeenCalledWith({
      ...defaultFilters,
      property_type: 'apartment',
    })
  })

  it('handles property type deselection', () => {
    const filtersWithType = { ...defaultFilters, property_type: 'apartment' }
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={filtersWithType}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    // Select a different property type to change selection
    const houseRadio = screen.getByLabelText('House')
    fireEvent.click(houseRadio)

    expect(onFiltersChange).toHaveBeenCalledWith({
      ...defaultFilters,
      property_type: 'house',
    })
  })

  it('handles minimum price input', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const minPriceInput = screen.getByLabelText('Minimum price')
    fireEvent.change(minPriceInput, { target: { value: '100' } })

    expect(onFiltersChange).toHaveBeenCalledWith({
      ...defaultFilters,
      min_price: 100,
    })
  })

  it('handles maximum price input', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const maxPriceInput = screen.getByLabelText('Maximum price')
    fireEvent.change(maxPriceInput, { target: { value: '500' } })

    expect(onFiltersChange).toHaveBeenCalledWith({
      ...defaultFilters,
      max_price: 500,
    })
  })

  it('handles amenity selection', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const wifiCheckbox = screen.getByLabelText('WiFi')
    fireEvent.click(wifiCheckbox)

    expect(onFiltersChange).toHaveBeenCalledWith({
      ...defaultFilters,
      amenities: ['wifi'],
    })
  })

  it('handles amenity deselection', () => {
    const filtersWithAmenities = { ...defaultFilters, amenities: ['wifi'] }
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={filtersWithAmenities}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const wifiCheckbox = screen.getByLabelText('WiFi')
    fireEvent.click(wifiCheckbox)

    expect(onFiltersChange).toHaveBeenCalledWith({
      ...defaultFilters,
      amenities: [],
    })
  })

  it('shows clear all button when filters are active', () => {
    const activeFilters = { ...defaultFilters, property_type: 'apartment' }
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={activeFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    expect(screen.getByText('Clear All')).toBeInTheDocument()
  })

  it('does not show clear all button when no filters are active', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    expect(screen.queryByText('Clear All')).not.toBeInTheDocument()
  })

  it('calls onClearFilters when clear all button is clicked', () => {
    const activeFilters = { ...defaultFilters, property_type: 'apartment' }
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={activeFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const clearButton = screen.getByText('Clear All')
    fireEvent.click(clearButton)

    expect(onClearFilters).toHaveBeenCalledTimes(1)
  })

  it('renders all amenity options', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    expect(screen.getByLabelText('WiFi')).toBeInTheDocument()
    expect(screen.getByLabelText('Parking')).toBeInTheDocument()
    expect(screen.getByLabelText('Air Conditioning')).toBeInTheDocument()
    expect(screen.getByLabelText('Heating')).toBeInTheDocument()
    expect(screen.getByLabelText('Elevator')).toBeInTheDocument()
  })

  it('has expand/collapse functionality', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const toggleButton = screen.getByText('Show More')
    expect(toggleButton).toBeInTheDocument()

    fireEvent.click(toggleButton)
    expect(screen.getByText('Show Less')).toBeInTheDocument()
  })

  it('has proper ARIA attributes', () => {
    const onFiltersChange = vi.fn()
    const onClearFilters = vi.fn()

    render(
      <SearchFilters
        filters={defaultFilters}
        onFiltersChange={onFiltersChange}
        onClearFilters={onClearFilters}
        propertyTypes={mockPropertyTypes}
      />
    )

    const toggleButton = screen.getByText('Show More')
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false')
  })
})
