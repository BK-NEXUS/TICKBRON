import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { StatusInsights } from './StatusInsights'
import type { StatusInsights as Insights } from '../adapters/statusAdapter'

const INSIGHTS: Insights = {
  cancellation_rate: '25.00',
  occupancy_rate: '11.43',
  average_booking_value: [{ currency: 'USD', amount: '50.00' }, { currency: 'UZS', amount: '300000.00' }],
  average_stay_nights: '2.33',
  previous_period: {
    range: { from: '2026-09-23', to: '2026-09-29' },
    totals: { bookings: 1, guests: 1, nights: 2, stayed: 1, revenue: [] },
  },
  change_pct: {
    bookings: '200.0', guests: '-50.0', nights: null, stayed: '0.0',
    revenue: [{ currency: 'USD', pct: '12.5' }],
  },
}

const cardOf = (label: string) => screen.getByText(label).closest('.status-card') as HTMLElement

describe('StatusInsights', () => {
  it('shows the rates and the averages', () => {
    render(<StatusInsights insights={INSIGHTS} />)

    expect(within(cardOf('Cancellation rate')).getByText('25.00%')).toBeInTheDocument()
    expect(within(cardOf('Occupancy')).getByText('11.43%')).toBeInTheDocument()
    expect(within(cardOf('Average booking value')).getByText('$50.00 · UZS 300,000.00')).toBeInTheDocument()
    expect(within(cardOf('Average stay')).getByText('2.33 nights')).toBeInTheDocument()
  })

  it('shows a dash where there is nothing to calculate', () => {
    render(<StatusInsights insights={{
      ...INSIGHTS, cancellation_rate: null, occupancy_rate: null, average_booking_value: [], average_stay_nights: null,
    }} />)

    for (const label of ['Cancellation rate', 'Occupancy', 'Average booking value', 'Average stay']) {
      expect(within(cardOf(label)).getByText('—')).toBeInTheDocument()
    }
  })

  it('compares with the previous period: up, down, same and no base', () => {
    render(<StatusInsights insights={INSIGHTS} />)

    expect(screen.getByText(/Compared with 2026-09-23 – 2026-09-29/)).toBeInTheDocument()
    expect(screen.getByLabelText('Bookings: up 200.0%')).toHaveTextContent('+200.0%')
    expect(screen.getByLabelText('Guests: down 50.0%')).toHaveTextContent('−50.0%')
    expect(screen.getByLabelText('Stayed bookings: no change')).toHaveTextContent('0.0%')
    expect(screen.getByLabelText('Nights: nothing to compare with')).toHaveTextContent('—')
    expect(screen.getByLabelText('Revenue USD: up 12.5%')).toHaveTextContent('+12.5%')
  })

  it('has no comparison for all time', () => {
    render(<StatusInsights insights={{ ...INSIGHTS, previous_period: null, change_pct: null }} />)

    expect(screen.queryByText(/Compared with/)).toBeNull()
    expect(screen.getByText('Cancellation rate')).toBeInTheDocument()
  })

  it('shows the rank of the owner\'s hotel, and nothing when it is hidden', () => {
    const { rerender } = render(<StatusInsights insights={INSIGHTS} rank={{ position: 2, of: 5 }} />)
    expect(within(cardOf('Rank in your region')).getByText('#2 of 5')).toBeInTheDocument()

    rerender(<StatusInsights insights={INSIGHTS} rank={null} />)
    expect(screen.queryByText('Rank in your region')).toBeNull()
  })
})
