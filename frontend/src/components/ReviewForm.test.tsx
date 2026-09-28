import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { ReviewForm } from './ReviewForm'
import { accountAdapter } from '../adapters/accountAdapter'

// Mock accountAdapter
vi.mock('../adapters/accountAdapter', () => ({
  accountAdapter: {
    createReview: vi.fn(),
  },
}))

describe('ReviewForm', () => {
  it('should render review form', () => {
    render(<ReviewForm propertyId={1} bookingId={7} />)

    expect(screen.getByText('Write a Review')).toBeInTheDocument()
    expect(screen.getByText('Overall Rating')).toBeInTheDocument()
    expect(screen.getByText('Cleanliness')).toBeInTheDocument()
    expect(screen.getByText('Location')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    expect(screen.getByText('Amenities')).toBeInTheDocument()
    expect(screen.getByText('Service')).toBeInTheDocument()
  })

  it('should render title and comment fields', () => {
    render(<ReviewForm propertyId={1} bookingId={7} />)

    expect(screen.getByLabelText('Title (Optional)')).toBeInTheDocument()
    expect(screen.getByLabelText('Comment (Optional)')).toBeInTheDocument()
  })

  it('should allow star rating selection', () => {
    render(<ReviewForm propertyId={1} bookingId={7} />)

    const starButtons = screen.getAllByRole('button')
    expect(starButtons.length).toBeGreaterThan(0)

    // Click the first star button
    fireEvent.click(starButtons[0])
  })

  it('should submit review with overall rating', async () => {
    const mockCreateReview = vi.mocked(accountAdapter.createReview).mockResolvedValueOnce({
      data: {
        id: 1,
        user: 1,
        property: 1,
        overall_rating: 5,
        status: 'pending',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      },
      error: null,
    })

    const onSubmitSuccess = vi.fn()
    render(<ReviewForm propertyId={1} bookingId={7} onSubmitSuccess={onSubmitSuccess} />)

    const stars = screen.getAllByLabelText(/Overall Rating \d stars/)
    fireEvent.click(stars[4]) // Select 5 stars

    const submitButton = screen.getByText('Submit Review')
    fireEvent.click(submitButton)

    await waitFor(() => expect(mockCreateReview).toHaveBeenCalledWith({
      property: 1,
      booking: 7,
      overall_rating: 5,
    }))
  })

  it('should submit review with category ratings', async () => {
    const mockCreateReview = vi.mocked(accountAdapter.createReview).mockResolvedValueOnce({
      data: {
        id: 1,
        user: 1,
        property: 1,
        overall_rating: 5,
        cleanliness_rating: 5,
        location_rating: 4,
        status: 'pending',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      },
      error: null,
    })

    const onSubmitSuccess = vi.fn()
    render(<ReviewForm propertyId={1} bookingId={7} onSubmitSuccess={onSubmitSuccess} />)

    // Select overall rating
    const overallStars = screen.getAllByLabelText(/Overall Rating \d stars/)
    fireEvent.click(overallStars[4])

    // Select category ratings
    const cleanlinessStars = screen.getAllByLabelText(/Cleanliness \d stars/)
    fireEvent.click(cleanlinessStars[4])

    const locationStars = screen.getAllByLabelText(/Location \d stars/)
    fireEvent.click(locationStars[3])

    const submitButton = screen.getByText('Submit Review')
    fireEvent.click(submitButton)

    // Flat fields, as ReviewCreateSerializer expects; unrated categories are not sent
    await waitFor(() => expect(mockCreateReview).toHaveBeenCalledWith({
      property: 1,
      booking: 7,
      overall_rating: 5,
      cleanliness_rating: 5,
      location_rating: 4,
    }))
  })

  it('should submit review with title and comment', async () => {
    const mockCreateReview = vi.mocked(accountAdapter.createReview).mockResolvedValueOnce({
      data: {
        id: 1,
        user: 1,
        property: 1,
        overall_rating: 5,
        title: 'Great stay!',
        comment: 'Amazing property',
        status: 'pending',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      },
      error: null,
    })

    const onSubmitSuccess = vi.fn()
    render(<ReviewForm propertyId={1} bookingId={7} onSubmitSuccess={onSubmitSuccess} />)

    // Select overall rating
    const overallStars = screen.getAllByLabelText(/Overall Rating \d stars/)
    fireEvent.click(overallStars[4])

    // Enter title
    const titleInput = screen.getByLabelText('Title (Optional)')
    fireEvent.change(titleInput, { target: { value: 'Great stay!' } })

    // Enter comment
    const commentInput = screen.getByLabelText('Comment (Optional)')
    fireEvent.change(commentInput, { target: { value: 'Amazing property' } })

    const submitButton = screen.getByText('Submit Review')
    fireEvent.click(submitButton)

    await waitFor(() => expect(mockCreateReview).toHaveBeenCalledWith({
      property: 1,
      booking: 7,
      overall_rating: 5,
      title: 'Great stay!',
      comment: 'Amazing property',
    }))
  })

  it('should show validation error when overall rating is missing', async () => {
    render(<ReviewForm propertyId={1} bookingId={7} />)

    const submitButton = screen.getByText('Submit Review')
    fireEvent.click(submitButton)

    expect(screen.getByText('Overall rating is required')).toBeInTheDocument()
  })

  it('should show error message from API', async () => {
    vi.mocked(accountAdapter.createReview).mockResolvedValueOnce({
      data: null,
      error: 'Invalid review data',
    })

    render(<ReviewForm propertyId={1} bookingId={7} />)

    // Select overall rating
    const overallStars = screen.getAllByLabelText(/Overall Rating \d stars/)
    fireEvent.click(overallStars[4])

    const submitButton = screen.getByText('Submit Review')
    fireEvent.click(submitButton)

    await waitFor(() => expect(screen.getByText('Invalid review data')).toBeInTheDocument())
  })

  it('should call onCancel when cancel button is clicked', () => {
    const onCancel = vi.fn()
    render(<ReviewForm propertyId={1} onCancel={onCancel} />)

    const cancelButton = screen.getByText('Cancel')
    fireEvent.click(cancelButton)

    expect(onCancel).toHaveBeenCalled()
  })

  it('should disable submit button while loading', async () => {
    vi.mocked(accountAdapter.createReview).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<ReviewForm propertyId={1} bookingId={7} />)

    // Select overall rating
    const overallStars = screen.getAllByLabelText(/Overall Rating \d stars/)
    fireEvent.click(overallStars[4])

    const submitButton = screen.getByText('Submit Review')
    fireEvent.click(submitButton)

    expect(submitButton).toBeDisabled()
    expect(screen.getByText('Submitting...')).toBeInTheDocument()
  })

  it('should not submit without a booking', async () => {
    vi.mocked(accountAdapter.createReview).mockClear()
    render(<ReviewForm propertyId={1} />)

    fireEvent.click(screen.getAllByLabelText(/Overall Rating \d stars/)[4])
    fireEvent.click(screen.getByText('Submit Review'))

    expect(screen.getByText('You can review this property after a completed stay.')).toBeInTheDocument()
    expect(accountAdapter.createReview).not.toHaveBeenCalled()
  })

  it('should send the booking id as booking', async () => {
    const mockCreateReview = vi.mocked(accountAdapter.createReview).mockResolvedValueOnce({
      data: {
        id: 1,
        user: 1,
        property: 1,
        booking: 1,
        overall_rating: 5,
        status: 'pending',
        created_at: '2025-01-15T10:00:00Z',
        updated_at: '2025-01-15T10:00:00Z',
      },
      error: null,
    })

    const onSubmitSuccess = vi.fn()
    render(<ReviewForm propertyId={1} bookingId={3} onSubmitSuccess={onSubmitSuccess} />)

    // Select overall rating
    const overallStars = screen.getAllByLabelText(/Overall Rating \d stars/)
    fireEvent.click(overallStars[4])

    const submitButton = screen.getByText('Submit Review')
    fireEvent.click(submitButton)

    await waitFor(() => expect(mockCreateReview).toHaveBeenCalledWith({
      property: 1,
      booking: 3,
      overall_rating: 5,
    }))
  })
})
