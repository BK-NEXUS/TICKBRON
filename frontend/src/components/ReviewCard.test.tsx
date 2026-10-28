import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReviewCard } from './ReviewCard'
import { Review } from '../adapters/accountAdapter'

describe('ReviewCard', () => {
  const mockReview: Review = {
    id: 1,
    user: 1,
    property: 1,
    overall_rating: 5,
    cleanliness_rating: 5,
    location_rating: 4,
    value_rating: 5,
    amenities_rating: 4,
    service_rating: 5,
    title: 'Great stay!',
    comment: 'Amazing property with excellent service',
    status: 'approved',
    created_at: '2025-01-15T10:00:00Z',
    updated_at: '2025-01-15T10:00:00Z',
  }

  it('should render review card', () => {
    render(<ReviewCard review={mockReview} />)

    expect(screen.getByText('Great stay!')).toBeInTheDocument()
    expect(screen.getByText('Amazing property with excellent service')).toBeInTheDocument()
  })

  it('should render overall rating stars', () => {
    render(<ReviewCard review={mockReview} />)

    const stars = document.querySelectorAll('.review-card-star .star-icon')
    expect(stars).toHaveLength(5) // 5 stars for overall rating
  })

  it('should render category ratings', () => {
    render(<ReviewCard review={mockReview} />)

    expect(screen.getByText('Cleanliness')).toBeInTheDocument()
    expect(screen.getByText('Location')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    expect(screen.getByText('Amenities')).toBeInTheDocument()
    expect(screen.getByText('Service')).toBeInTheDocument()
    // Check that rating values exist (some may be duplicated)
    expect(screen.getAllByText('5/5').length).toBeGreaterThan(0)
    expect(screen.getAllByText('4/5').length).toBeGreaterThan(0)
  })

  it('should render formatted date', () => {
    render(<ReviewCard review={mockReview} />)

    expect(screen.getByText(/January 15, 2025/)).toBeInTheDocument()
  })

  it('should not render title when missing', () => {
    const reviewWithoutTitle: Review = {
      ...mockReview,
      title: undefined,
    }

    render(<ReviewCard review={reviewWithoutTitle} />)

    expect(screen.queryByText('Great stay!')).not.toBeInTheDocument()
  })

  it('should not render comment when missing', () => {
    const reviewWithoutComment: Review = {
      ...mockReview,
      comment: undefined,
    }

    render(<ReviewCard review={reviewWithoutComment} />)

    expect(screen.queryByText('Amazing property with excellent service')).not.toBeInTheDocument()
  })

  it('should not render category ratings when all missing', () => {
    const reviewWithoutCategories: Review = {
      ...mockReview,
      cleanliness_rating: undefined,
      location_rating: undefined,
      value_rating: undefined,
      amenities_rating: undefined,
      service_rating: undefined,
    }

    render(<ReviewCard review={reviewWithoutCategories} />)

    expect(screen.queryByText('Category Ratings')).not.toBeInTheDocument()
    expect(screen.queryByText('Cleanliness')).not.toBeInTheDocument()
  })

  it('should render only provided category ratings', () => {
    const reviewWithPartialCategories: Review = {
      ...mockReview,
      cleanliness_rating: 5,
      location_rating: undefined,
      value_rating: undefined,
      amenities_rating: undefined,
      service_rating: undefined,
    }

    render(<ReviewCard review={reviewWithPartialCategories} />)

    expect(screen.getByText('Cleanliness')).toBeInTheDocument()
    expect(screen.queryByText('Location')).not.toBeInTheDocument()
    expect(screen.queryByText('Value')).not.toBeInTheDocument()
  })

  it('should render pending status badge', () => {
    const pendingReview: Review = {
      ...mockReview,
      status: 'pending',
    }

    render(<ReviewCard review={pendingReview} />)

    expect(screen.getByText('Pending Approval')).toBeInTheDocument()
  })

  it('should not render pending status badge for approved reviews', () => {
    render(<ReviewCard review={mockReview} />)

    expect(screen.queryByText('Pending Approval')).not.toBeInTheDocument()
  })

  it('should render review with minimal data', () => {
    const minimalReview: Review = {
      id: 1,
      user: 1,
      property: 1,
      overall_rating: 4,
      status: 'approved',
      created_at: '2025-01-15T10:00:00Z',
      updated_at: '2025-01-15T10:00:00Z',
    }

    render(<ReviewCard review={minimalReview} />)

    expect(document.querySelectorAll('.review-card-star .star-icon')).toHaveLength(5) // 5 stars overall
    expect(screen.getByText(/January 15, 2025/)).toBeInTheDocument()
  })
})

describe('ReviewCard as a guest review of the hotel page', () => {
  const guestReview = {
    id: 7, reviewer: 'Aziz K.', stay_month: '2026-10', overall_rating: 4, title: 'Quiet', comment: 'Clean rooms',
    created_at: '2026-10-20T10:00:00Z',
  }

  it('names the reviewer by first name and initial and the month of the stay', () => {
    render(<ReviewCard review={guestReview} />)
    expect(screen.getByText('Aziz K.')).toBeInTheDocument()
    expect(screen.getByText(/October 2026/)).toBeInTheDocument()
  })

  it('shows no name line for a reviewer without a name', () => {
    render(<ReviewCard review={{ ...guestReview, reviewer: '' }} />)
    expect(screen.queryByText('Aziz K.')).not.toBeInTheDocument()
    expect(screen.getByText('Clean rooms')).toBeInTheDocument()
  })

  it('says a rejected own review is not shown to others, and says nothing for a guest review', () => {
    const own = { id: 1, user: 1, property: 5, overall_rating: 3, status: 'rejected' as const, created_at: '2026-10-20T10:00:00Z', updated_at: '2026-10-20T10:00:00Z' }
    const { rerender } = render(<ReviewCard review={own} />)
    expect(screen.getByText('Not approved: it is not shown to others.')).toBeInTheDocument()
    rerender(<ReviewCard review={guestReview} />)
    expect(screen.queryByText(/not shown/)).not.toBeInTheDocument()
  })
})
