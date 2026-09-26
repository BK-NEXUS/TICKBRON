import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { AvailabilityCalendar } from './AvailabilityCalendar'
import { DateInventory } from '../adapters/propertyAdapter'

// Dates far enough ahead that "today" never makes them past dates
const d = (n: number) => `2030-03-${String(n).padStart(2, '0')}`
const label = (date: string) => {
  const [y, m, dd] = date.split('-').map(Number)
  return new Date(y, m - 1, dd).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

const row = (date: string, overrides: Partial<DateInventory> = {}): DateInventory => ({
  id: Number(date.slice(-2)), rate_plan_id: 1, date, status: 'available', available_rooms: 3, booked_rooms: 0,
  price: 60, currency: 'EUR', min_stay: 1, max_stay: 30, is_available: true, ...overrides,
})

const inventory = [
  row(d(10)), row(d(11)), row(d(12), { price: 69 }), row(d(13)),
  row(d(14), { is_available: false, status: 'closed' }),
  row(d(15), { is_available: false, status: 'fully_booked', booked_rooms: 3 }),
  row(d(16)),
]

function Harness({ onRange, ...props }: Partial<React.ComponentProps<typeof AvailabilityCalendar>> & {
  onRange?: (checkIn: string | null, checkOut: string | null) => void
}) {
  const [range, setRange] = useState<{ checkIn: string | null; checkOut: string | null }>({ checkIn: null, checkOut: null })
  return (
    <AvailabilityCalendar
      inventory={inventory}
      checkIn={range.checkIn}
      checkOut={range.checkOut}
      onRangeChange={(checkIn, checkOut) => {
        setRange({ checkIn, checkOut })
        onRange?.(checkIn, checkOut)
      }}
      {...props}
    />
  )
}

const cell = (container: HTMLElement, date: string) =>
  container.querySelector(`.availability-calendar-day[data-date="${date}"]`) as HTMLElement

describe('AvailabilityCalendar', () => {
  it('renders empty state when no inventory provided', () => {
    render(<AvailabilityCalendar inventory={[]} checkIn={null} checkOut={null} onRangeChange={vi.fn()} />)
    expect(screen.getByText('No availability data available')).toBeInTheDocument()
  })

  it('opens on the month of the first available night and shows each night\'s price', () => {
    const { container } = render(<Harness />)
    expect(screen.getByRole('heading', { name: 'March 2030' })).toBeInTheDocument()
    expect(cell(container, d(10))).toHaveTextContent('€60')
    expect(cell(container, d(12))).toHaveTextContent('€69')
  })

  it('renders month navigation, weekdays and the legend', () => {
    render(<Harness />)
    expect(screen.getByRole('button', { name: /previous month/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /next month/i })).toBeInTheDocument()
    for (const weekday of ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']) {
      expect(screen.getByText(weekday)).toBeInTheDocument()
    }
    expect(screen.getByText('Available')).toBeInTheDocument()
    expect(screen.getByText('Fully Booked')).toBeInTheDocument()
  })

  it('selects check-in then check-out and highlights the range', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)

    fireEvent.click(cell(container, d(10)))
    fireEvent.click(cell(container, d(13)))

    expect(onRange).toHaveBeenLastCalledWith(d(10), d(13))
    expect(cell(container, d(10))).toHaveClass('availability-calendar-day--range-start')
    expect(cell(container, d(11))).toHaveClass('availability-calendar-day--in-range')
    expect(cell(container, d(13))).toHaveClass('availability-calendar-day--range-end')
  })

  it('a closed night can be the check-out day (no night is spent on it)', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)
    fireEvent.click(cell(container, d(12)))
    fireEvent.click(cell(container, d(14)))
    expect(onRange).toHaveBeenLastCalledWith(d(12), d(14))
  })

  it('blocks a range with a closed night and names the date', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)
    fireEvent.click(cell(container, d(13)))
    fireEvent.click(cell(container, d(16)))

    expect(screen.getByRole('alert')).toHaveTextContent(`${label(d(14))} is not available`)
    expect(onRange).toHaveBeenLastCalledWith(d(13), null)
  })

  it('names a sold-out night', () => {
    const { container } = render(<Harness inventory={[row(d(10)), row(d(11), { is_available: false, status: 'fully_booked', booked_rooms: 3 }), row(d(12))]} />)
    fireEvent.click(cell(container, d(10)))
    fireEvent.click(cell(container, d(13)))
    expect(screen.getByRole('alert')).toHaveTextContent(`${label(d(11))} is sold out`)
  })

  it('names a night with no availability data', () => {
    const { container } = render(<Harness inventory={[row(d(10)), row(d(12))]} />)
    fireEvent.click(cell(container, d(10)))
    fireEvent.click(cell(container, d(13)))
    expect(screen.getByRole('alert')).toHaveTextContent(`${label(d(11))} is not available`)
  })

  it('respects the rate plan minimum and maximum stay', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} minNights={2} maxNights={3} />)

    fireEvent.click(cell(container, d(10)))
    fireEvent.click(cell(container, d(11)))
    expect(screen.getByRole('alert')).toHaveTextContent('Minimum stay is 2 nights')

    fireEvent.click(cell(container, d(10)))
    fireEvent.click(cell(container, d(14)))
    expect(screen.getByRole('alert')).toHaveTextContent('Maximum stay is 3 nights')
    expect(onRange).not.toHaveBeenCalledWith(d(10), d(14))
  })

  it('respects a night\'s own minimum stay', () => {
    const { container } = render(<Harness inventory={[row(d(10), { min_stay: 3 }), row(d(11)), row(d(12))]} />)
    fireEvent.click(cell(container, d(10)))
    fireEvent.click(cell(container, d(12)))
    expect(screen.getByRole('alert')).toHaveTextContent(`A stay including ${label(d(10))} must be at least 3 nights`)
  })

  it('closed and sold-out days cannot start a stay', () => {
    const { container } = render(<Harness />)
    expect(cell(container, d(14))).toHaveAttribute('aria-disabled', 'true')
    expect(cell(container, d(15))).toHaveAttribute('aria-disabled', 'true')
    expect(cell(container, d(10))).toHaveAttribute('aria-disabled', 'false')
  })
})
