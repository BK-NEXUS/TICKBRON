import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PropertyPoliciesDetail } from './PropertyPoliciesDetail'
import { PropertyPolicy } from '../adapters/searchAdapter'

describe('PropertyPoliciesDetail', () => {
  const mockPolicies: PropertyPolicy[] = [
    {
      policy_type: 'check_in',
      title: 'Check-in Policy',
      description: 'Check-in from 3:00 PM to 8:00 PM',
      is_strict: false,
    },
    {
      policy_type: 'cancellation',
      title: 'Cancellation Policy',
      description: 'Free cancellation up to 48 hours before check-in',
      is_strict: false,
    },
    {
      policy_type: 'house_rules',
      title: 'No Smoking',
      description: 'Smoking is not allowed anywhere on the property',
      is_strict: true,
    },
    {
      policy_type: 'payment',
      title: 'Payment Methods',
      description: 'We accept credit cards and cash',
      is_strict: false,
    },
  ]

  it('renders empty state when no policies provided', () => {
    render(<PropertyPoliciesDetail policies={[]} />)
    
    expect(screen.getByText('No policy information available')).toBeInTheDocument()
  })

  it('renders policies grouped by type', () => {
    render(<PropertyPoliciesDetail policies={mockPolicies} />)
    
    expect(screen.getByText('Policies')).toBeInTheDocument()
    const groupTitles = screen.getAllByRole('heading', { level: 3 })
    expect(groupTitles.some(el => el.textContent === 'Check-in & Check-out')).toBe(true)
    expect(groupTitles.some(el => el.textContent === 'Cancellation Policy')).toBe(true)
    expect(groupTitles.some(el => el.textContent === 'House Rules')).toBe(true)
    expect(groupTitles.some(el => el.textContent === 'Payment Policy')).toBe(true)
  })

  it('renders policy items with correct information', () => {
    render(<PropertyPoliciesDetail policies={mockPolicies} />)
    
    const policyTitles = screen.getAllByRole('heading', { level: 4 })
    expect(policyTitles.some(el => el.textContent === 'Check-in Policy')).toBe(true)
    expect(screen.getByText('Check-in from 3:00 PM to 8:00 PM')).toBeInTheDocument()
    expect(policyTitles.some(el => el.textContent === 'Cancellation Policy')).toBe(true)
    expect(screen.getByText('Free cancellation up to 48 hours before check-in')).toBeInTheDocument()
  })

  it('renders strict policy badge for strict policies', () => {
    render(<PropertyPoliciesDetail policies={mockPolicies} />)
    
    expect(screen.getByText('No Smoking')).toBeInTheDocument()
    expect(screen.getByText('Strict')).toBeInTheDocument()
  })

  it('does not render strict badge for non-strict policies', () => {
    render(<PropertyPoliciesDetail policies={mockPolicies} />)
    
    const checkInPolicy = screen.getByText('Check-in Policy').closest('.property-policy-item')
    expect(checkInPolicy).not.toHaveClass('property-policy-item--strict')
  })

  it('formats policy type labels correctly', () => {
    render(<PropertyPoliciesDetail policies={mockPolicies} />)
    
    const groupTitles = screen.getAllByRole('heading', { level: 3 })
    expect(groupTitles.some(el => el.textContent === 'Check-in & Check-out')).toBe(true)
    expect(groupTitles.some(el => el.textContent === 'Cancellation Policy')).toBe(true)
    expect(groupTitles.some(el => el.textContent === 'House Rules')).toBe(true)
    expect(groupTitles.some(el => el.textContent === 'Payment Policy')).toBe(true)
  })

  it('handles unknown policy types by capitalizing words', () => {
    const unknownPolicy: PropertyPolicy[] = [
      {
        policy_type: 'custom_policy_type',
        title: 'Custom Policy',
        description: 'This is a custom policy type',
        is_strict: false,
      },
    ]
    
    render(<PropertyPoliciesDetail policies={unknownPolicy} />)
    
    expect(screen.getByText('Custom Policy Type')).toBeInTheDocument()
  })

  it('applies strict styling to strict policy items', () => {
    render(<PropertyPoliciesDetail policies={mockPolicies} />)
    
    const strictPolicy = screen.getByText('No Smoking').closest('.property-policy-item')
    expect(strictPolicy).toHaveClass('property-policy-item--strict')
  })
})
