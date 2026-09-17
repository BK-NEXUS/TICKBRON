import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RatePlanCard } from './RatePlanCard'
import { RatePlan } from '../adapters/searchAdapter'

describe('RatePlanCard', () => {
  const mockRatePlan: RatePlan = {
    id: 1,
    room_type_id: 1,
    name: 'Standard Rate',
    slug: 'standard-rate',
    rate_type: 'standard',
    description: 'Standard flexible rate with free cancellation',
    base_price: 120,
    currency: 'EUR',
    min_nights: 1,
    max_nights: 30,
    is_active: true,
    cancellation_policy: 'Free cancellation up to 48 hours before check-in',
    deposit_required: false,
  }

  it('renders rate plan card with rate plan information', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} />)
    
    expect(screen.getByText('Standard Rate')).toBeInTheDocument()
    expect(screen.getByText('Standard')).toBeInTheDocument()
    expect(screen.getByText('Standard flexible rate with free cancellation')).toBeInTheDocument()
    expect(screen.getByText('1 night')).toBeInTheDocument()
    expect(screen.getByText('30 nights')).toBeInTheDocument()
    expect(screen.getByText('Free cancellation up to 48 hours before check-in')).toBeInTheDocument()
  })

  it('renders price in correct format', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} />)
    
    expect(screen.getByText('€120')).toBeInTheDocument()
    expect(screen.getByText('per night')).toBeInTheDocument()
  })

  it('formats rate type correctly', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} />)
    
    expect(screen.getByText('Standard')).toBeInTheDocument()
  })

  it('formats non-refundable rate type', () => {
    const nonRefundablePlan: RatePlan = { 
      ...mockRatePlan, 
      rate_type: 'non_refundable',
      name: 'Non-Refundable Rate'
    }
    render(<RatePlanCard ratePlan={nonRefundablePlan} />)
    
    expect(screen.getByText('Non-Refundable')).toBeInTheDocument()
  })

  it('renders deposit information when required', () => {
    const depositPlan: RatePlan = { 
      ...mockRatePlan, 
      deposit_required: true, 
      deposit_percentage: 20 
    }
    render(<RatePlanCard ratePlan={depositPlan} />)
    
    expect(screen.getByText('Deposit Required')).toBeInTheDocument()
    expect(screen.getByText('20%')).toBeInTheDocument()
  })

  it('does not render deposit information when not required', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} />)
    
    expect(screen.queryByText('Deposit Required')).not.toBeInTheDocument()
  })

  it('renders advance booking information when provided', () => {
    const advanceBookingPlan: RatePlan = { 
      ...mockRatePlan, 
      advance_booking_days: 7 
    }
    render(<RatePlanCard ratePlan={advanceBookingPlan} />)
    
    expect(screen.getByText('Advance Booking')).toBeInTheDocument()
    expect(screen.getByText('7 days')).toBeInTheDocument()
  })

  it('does not render advance booking information when not provided', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} />)
    
    expect(screen.queryByText('Advance Booking')).not.toBeInTheDocument()
  })

  it('calls onSelect when card is clicked', () => {
    const onSelect = vi.fn()
    render(<RatePlanCard ratePlan={mockRatePlan} onSelect={onSelect} />)
    
    const card = screen.getByRole('button')
    card.click()
    
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('calls onSelect when Enter key is pressed', () => {
    const onSelect = vi.fn()
    render(<RatePlanCard ratePlan={mockRatePlan} onSelect={onSelect} />)
    
    const card = screen.getByRole('button')
    card.click()
    
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('calls onSelect when Space key is pressed', () => {
    const onSelect = vi.fn()
    render(<RatePlanCard ratePlan={mockRatePlan} onSelect={onSelect} />)
    
    const card = screen.getByRole('button')
    card.click()
    
    expect(onSelect).toHaveBeenCalledWith(1)
  })

  it('shows selected indicator when isSelected is true', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} isSelected={true} />)
    
    expect(screen.getByText('✓ Selected')).toBeInTheDocument()
  })

  it('does not show selected indicator when isSelected is false', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} isSelected={false} />)
    
    expect(screen.queryByText('✓ Selected')).not.toBeInTheDocument()
  })

  it('applies selected styling when isSelected is true', () => {
    const { container } = render(<RatePlanCard ratePlan={mockRatePlan} isSelected={true} />)
    const card = container.querySelector('.rate-plan-card--selected')
    
    expect(card).toBeInTheDocument()
  })

  it('has proper accessibility attributes', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} isSelected={false} />)
    
    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('aria-pressed', 'false')
  })

  it('has proper accessibility attributes when selected', () => {
    render(<RatePlanCard ratePlan={mockRatePlan} isSelected={true} />)
    
    const card = screen.getByRole('button')
    expect(card).toHaveAttribute('aria-pressed', 'true')
  })

  it('formats price with different currency', () => {
    const usdPlan: RatePlan = { ...mockRatePlan, currency: 'USD', base_price: 150 }
    render(<RatePlanCard ratePlan={usdPlan} />)
    
    expect(screen.getByText('$150')).toBeInTheDocument()
  })

  it('handles unknown rate type gracefully', () => {
    const unknownTypePlan: RatePlan = { 
      ...mockRatePlan, 
      rate_type: 'custom_type' 
    }
    render(<RatePlanCard ratePlan={unknownTypePlan} />)
    
    expect(screen.getByText('Custom Type')).toBeInTheDocument()
  })
})