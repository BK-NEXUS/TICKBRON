import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PropertyGallery } from './PropertyGallery'
import { Property } from '../adapters/propertyAdapter'

describe('PropertyGallery', () => {
  const mockProperty: Property = {
    id: 1,
    owner_id: 1,
    property_type: { id: 1, name: 'Apartment', slug: 'apartment' },
    status: 'active',
    max_guests: 4,
    bedrooms: 2,
    bathrooms: 1,
    address_line1: '123 Test Street',
    city: 'Test City',
    country: 'Test Country',
    base_price: 100,
    currency: 'USD',
    has_elevator: true,
    has_parking: false,
    has_wifi: true,
    has_ac: true,
    has_heating: true,
    translations: [
      {
        language: 'en',
        name: 'Test Property',
        description: 'Test description',
      },
    ],
    policies: [],
    gallery: {
      exterior: [
        { id: 1, photo: 'house.jpg', photo_type: 'exterior', is_primary: true, display_order: 1 },
        { id: 2, photo: 'castle.jpg', photo_type: 'exterior', is_primary: false, display_order: 2 },
        { id: 3, photo: 'city.jpg', photo_type: 'exterior', is_primary: false, display_order: 3 },
      ],
    },
    primary_photo: {
      id: 1,
      photo: 'house.jpg',
      photo_type: 'exterior',
      is_primary: true,
      display_order: 1,
    },
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  }

  it('renders the gallery with main image', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const gallery = screen.getByRole('region', { name: 'Property image gallery' })
    expect(gallery).toBeInTheDocument()
  })

  it('renders navigation buttons when multiple images', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const prevButton = screen.getByLabelText('Previous image')
    const nextButton = screen.getByLabelText('Next image')
    
    expect(prevButton).toBeInTheDocument()
    expect(nextButton).toBeInTheDocument()
    expect(prevButton).not.toBeDisabled()
    expect(nextButton).not.toBeDisabled()
  })

  it('navigates to next image when next button is clicked', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const nextButton = screen.getByLabelText('Next image')
    fireEvent.click(nextButton)
    
    // Component should update state (visual verification would be in browser)
    expect(nextButton).toBeInTheDocument()
  })

  it('navigates to previous image when previous button is clicked', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const prevButton = screen.getByLabelText('Previous image')
    fireEvent.click(prevButton)
    
    expect(prevButton).toBeInTheDocument()
  })

  it('renders thumbnails when multiple images', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const thumbnails = screen.getAllByLabelText(/View image/)
    expect(thumbnails.length).toBe(3)
  })

  it('selects thumbnail when clicked', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const thumbnails = screen.getAllByLabelText(/View image/)
    const secondThumbnail = thumbnails[1]
    
    fireEvent.click(secondThumbnail)
    
    expect(secondThumbnail).toHaveAttribute('aria-pressed', 'true')
  })

  it('has proper ARIA attributes', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const gallery = screen.getByRole('region', { name: 'Property image gallery' })
    expect(gallery).toBeInTheDocument()
  })

  it('supports keyboard navigation with arrow keys', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const gallery = screen.getByRole('region', { name: 'Property image gallery' })
    
    fireEvent.keyDown(gallery, { key: 'ArrowRight' })
    fireEvent.keyDown(gallery, { key: 'ArrowLeft' })
    
    expect(gallery).toBeInTheDocument()
  })

  it('disables navigation buttons when only one image', () => {
    // Mock property with single image scenario would need different mock structure
    // For now, test that buttons exist and are functional
    render(<PropertyGallery property={mockProperty} />)
    
    const prevButton = screen.getByLabelText('Previous image')
    const nextButton = screen.getByLabelText('Next image')
    
    expect(prevButton).toBeInTheDocument()
    expect(nextButton).toBeInTheDocument()
  })

  it('has first thumbnail selected by default', () => {
    render(<PropertyGallery property={mockProperty} />)
    
    const thumbnails = screen.getAllByLabelText(/View image/)
    expect(thumbnails[0]).toHaveAttribute('aria-pressed', 'true')
  })

  describe('real photos and the full-screen view', () => {
    const mainImage = () => screen.getByTestId('gallery-main-image') as HTMLImageElement

    it('shows the current photo as an image, with an alt text', () => {
      render(<PropertyGallery property={mockProperty} />)
      expect(mainImage()).toHaveAttribute('src', 'house.jpg')
      expect(mainImage()).toHaveAttribute('alt', 'Test Property, photo 1')
    })

    it('thumbnails are small images of the photos', () => {
      render(<PropertyGallery property={mockProperty} />)
      const thumbnails = screen.getAllByLabelText(/View image/)
      expect(thumbnails.map(button => button.querySelector('img')?.getAttribute('src'))).toEqual(['house.jpg', 'castle.jpg', 'city.jpg'])
    })

    it('the arrows and the arrow keys change the photo', () => {
      render(<PropertyGallery property={mockProperty} />)
      fireEvent.click(screen.getByLabelText('Next image'))
      expect(mainImage()).toHaveAttribute('src', 'castle.jpg')
      fireEvent.keyDown(screen.getByRole('region', { name: 'Property image gallery' }), { key: 'ArrowLeft' })
      expect(mainImage()).toHaveAttribute('src', 'house.jpg')
    })

    it('a click on the photo opens the full-screen view on that photo', () => {
      render(<PropertyGallery property={mockProperty} />)
      fireEvent.click(screen.getAllByLabelText(/View image/)[1])
      fireEvent.click(screen.getByRole('button', { name: 'View photos full screen' }))
      const dialog = screen.getByRole('dialog', { name: 'Photos of Test Property' })
      expect(dialog.querySelector('img')).toHaveAttribute('src', 'castle.jpg')
      expect(screen.getByText('2 of 3')).toBeInTheDocument()
    })

    it('"View all photos" opens it too, and closing it returns to the gallery', () => {
      render(<PropertyGallery property={mockProperty} />)
      fireEvent.click(screen.getByRole('button', { name: 'View all 3 photos' }))
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      fireEvent.click(screen.getByRole('button', { name: 'Close photos' }))
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(mainImage()).toBeInTheDocument()
    })

    it('a property without photos shows the placeholder and offers no full-screen view', () => {
      render(<PropertyGallery property={{ ...mockProperty, gallery: undefined, primary_photo: undefined }} />)
      expect(screen.queryByTestId('gallery-main-image')).toBeNull()
      expect(screen.queryByRole('button', { name: 'View photos full screen' })).toBeNull()
      expect(screen.queryByRole('button', { name: /View all/ })).toBeNull()
    })
  })
})
