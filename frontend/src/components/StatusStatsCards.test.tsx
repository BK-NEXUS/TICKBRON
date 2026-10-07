import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { StatusStatsCards } from './StatusStatsCards'
import { StatusBookingStatusCounts } from './StatusBookingStatusCounts'
import { TOTALS } from '../test/statusFixtures'

const cardOf = (label: string) => screen.getByText(label).closest('.status-card') as HTMLElement

describe('StatusStatsCards', () => {
  it('leads with stayed; counted and upcoming are separate cards', () => {
    render(<StatusStatsCards totals={TOTALS} caption="All time" />)

    const stayed = cardOf('Stayed bookings')
    expect(stayed).toHaveClass('status-card--headline')
    expect(within(stayed).getByText('1,380')).toBeInTheDocument()
    expect(within(cardOf('Counted')).getByText('1,500')).toBeInTheDocument()
    expect(within(cardOf('Upcoming')).getByText('42')).toBeInTheDocument()
  })

  it('shows persons, unique customers and nights with separators', () => {
    render(<StatusStatsCards totals={TOTALS} caption="All time" />)

    expect(within(cardOf('Guests')).getByText('3,210')).toBeInTheDocument()
    expect(within(cardOf('Unique customers')).getByText('1,100')).toBeInTheDocument()
    const nights = cardOf('Nights')
    expect(within(nights).getByText('5,400')).toBeInTheDocument()
    expect(within(nights).getByText(/6,100 room nights/)).toBeInTheDocument()
  })

  it('lists money per currency, never one sum', () => {
    render(<StatusStatsCards totals={TOTALS} caption="All time" />)

    expect(within(cardOf('Revenue')).getByText('UZS 1,500,000,000.00 · $45,000.00')).toBeInTheDocument()
    expect(within(cardOf('Booking value')).getByText('UZS 1,600,000,000.00')).toBeInTheDocument()
  })

  it('hides fully refunded, no-show and reported no-show while they are zero', () => {
    render(<StatusStatsCards totals={TOTALS} caption="All time" />)

    expect(screen.queryByText('Fully refunded')).not.toBeInTheDocument()
    expect(screen.queryByText('No-show')).not.toBeInTheDocument()
    expect(screen.queryByText('No-show reported')).not.toBeInTheDocument()
  })

  it('shows them when non-zero', () => {
    render(<StatusStatsCards totals={{ ...TOTALS, fully_refunded: 2, no_show: 3, no_show_reported: 1 }} caption="All time" />)

    expect(within(cardOf('Fully refunded')).getByText('2')).toBeInTheDocument()
    expect(within(cardOf('No-show')).getByText('3')).toBeInTheDocument()
    expect(within(cardOf('No-show reported')).getByText('1')).toBeInTheDocument()
  })

  it('takes a lead card and a custom guests label', () => {
    render(
      <StatusStatsCards
        totals={TOTALS} caption="All time" lead={{ label: 'On TICKBRON since', value: 'Jan 15, 2025' }}
        guestsLabel="Guests via TICKBRON"
      />,
    )
    expect(screen.getByText('On TICKBRON since')).toBeInTheDocument()
    expect(screen.getByText('Guests via TICKBRON')).toBeInTheDocument()
  })
})

describe('StatusBookingStatusCounts', () => {
  it('lists every status, hiding the no-show ones at zero', () => {
    render(<StatusBookingStatusCounts counts={TOTALS.booking_status} />)

    const list = screen.getByRole('list', { name: 'Bookings by status' })
    expect(within(list).getByText('Pending').nextSibling).toHaveTextContent('4')
    expect(within(list).getByText('Completed').nextSibling).toHaveTextContent('1,380')
    expect(within(list).getByText('Expired')).toBeInTheDocument()
    expect(within(list).queryByText('No-show')).not.toBeInTheDocument()
  })

  it('shows no-show counts when non-zero', () => {
    render(<StatusBookingStatusCounts counts={{ ...TOTALS.booking_status, no_show: 2, no_show_reported: 1 }} />)

    expect(screen.getByText('No-show').nextSibling).toHaveTextContent('2')
    expect(screen.getByText('No-show reported').nextSibling).toHaveTextContent('1')
  })
})
