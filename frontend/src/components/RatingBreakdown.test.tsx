import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RatingBreakdown } from './RatingBreakdown'
import { PropertyScores } from '../adapters/accountAdapter'

describe('RatingBreakdown', () => {
  const mockPropertyScores: PropertyScores = {
    property_id: 1,
    total_reviews: 10,
    average_rating: 4.5,
    category_scores: {
      cleanliness_rating: 4.8,
      location_rating: 4.6,
      value_rating: 4.4,
      amenities_rating: 4.5,
      service_rating: 4.7,
    },
  }

  it('should render rating breakdown', () => {
    render(<RatingBreakdown propertyScores={mockPropertyScores} />)

    expect(screen.getAllByText('4.5').length).toBeGreaterThan(0)
    expect(screen.getByText('10 reviews')).toBeInTheDocument()
  })

  it('should render overall rating stars', () => {
    render(<RatingBreakdown propertyScores={mockPropertyScores} />)

    const stars = screen.getAllByText('★')
    expect(stars).toHaveLength(5)
  })

  it('should render category ratings', () => {
    render(<RatingBreakdown propertyScores={mockPropertyScores} />)

    expect(screen.getByText('Cleanliness')).toBeInTheDocument()
    expect(screen.getByText('4.8')).toBeInTheDocument()
    expect(screen.getByText('Location')).toBeInTheDocument()
    expect(screen.getByText('4.6')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    expect(screen.getByText('4.4')).toBeInTheDocument()
    expect(screen.getByText('Amenities')).toBeInTheDocument()
    expect(screen.getByText('Service')).toBeInTheDocument()
    expect(screen.getByText('4.7')).toBeInTheDocument()
    // 4.5 appears twice (in multiple contexts), so we check that it exists
    expect(screen.getAllByText('4.5').length).toBeGreaterThan(0)
  })

  it('should render empty state when no reviews', () => {
    const emptyScores: PropertyScores = {
      property_id: 1,
      total_reviews: 0,
      average_rating: null,
      category_scores: {},
    }

    render(<RatingBreakdown propertyScores={emptyScores} />)

    expect(screen.getByText('No reviews yet')).toBeInTheDocument()
  })

  it('should render singular review text', () => {
    const singleReviewScores: PropertyScores = {
      property_id: 1,
      total_reviews: 1,
      average_rating: 5.0,
      category_scores: {
        cleanliness_rating: 5,
      },
    }

    render(<RatingBreakdown propertyScores={singleReviewScores} />)

    expect(screen.getByText('1 review')).toBeInTheDocument()
  })

  it('should not render missing category scores', () => {
    const partialScores: PropertyScores = {
      property_id: 1,
      total_reviews: 5,
      average_rating: 4.0,
      category_scores: {
        cleanliness_rating: 4.5,
        location_rating: 4.0,
      },
    }

    render(<RatingBreakdown propertyScores={partialScores} />)

    expect(screen.getByText('Cleanliness')).toBeInTheDocument()
    expect(screen.getByText('Location')).toBeInTheDocument()
    expect(screen.queryByText('Value')).not.toBeInTheDocument()
    expect(screen.queryByText('Amenities')).not.toBeInTheDocument()
    expect(screen.queryByText('Service')).not.toBeInTheDocument()
  })

  it('should render progress bars for each category', () => {
    render(<RatingBreakdown propertyScores={mockPropertyScores} />)

    // Check that progress bars are rendered
    const progressBars = screen.getAllByTestId('rating-breakdown-bar-fill')
    expect(progressBars.length).toBeGreaterThan(0)
  })

  it('should format average rating to one decimal place', () => {
    const scoresWithDecimals: PropertyScores = {
      property_id: 1,
      total_reviews: 10,
      average_rating: 4.523,
      category_scores: {},
    }

    render(<RatingBreakdown propertyScores={scoresWithDecimals} />)

    expect(screen.getByText('4.5')).toBeInTheDocument()
  })

  it('should format category scores to one decimal place', () => {
    const scoresWithDecimals: PropertyScores = {
      property_id: 1,
      total_reviews: 10,
      average_rating: 4.5,
      category_scores: {
        cleanliness_rating: 4.567,
      },
    }

    render(<RatingBreakdown propertyScores={scoresWithDecimals} />)

    expect(screen.getByText('4.6')).toBeInTheDocument()
  })
})
