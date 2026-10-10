import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { DateRangeCalendar } from './DateRangeCalendar'

// A fixed month keeps the tests independent of today's date
const MONTH = '2030-03'
const day = (n: number) => `2030-03-${String(n).padStart(2, '0')}`

function Harness(props: Partial<React.ComponentProps<typeof DateRangeCalendar>> & { onRange?: (a: string | null, b: string | null) => void }) {
  const [range, setRange] = useState<{ checkIn: string | null; checkOut: string | null }>({ checkIn: null, checkOut: null })
  return (
    <DateRangeCalendar
      initialMonth={MONTH}
      minDate="2030-01-01"
      checkIn={range.checkIn}
      checkOut={range.checkOut}
      onChange={(checkIn, checkOut) => {
        setRange({ checkIn, checkOut })
        props.onRange?.(checkIn, checkOut)
      }}
      {...props}
    />
  )
}

const cell = (container: HTMLElement, date: string) =>
  container.querySelector(`[data-date="${date}"]`) as HTMLElement

describe('DateRangeCalendar', () => {
  it('tells the screen which month is shown, at the start and after every move', () => {
    const onMonthChange = vi.fn()
    render(<Harness onMonthChange={onMonthChange} />)
    expect(onMonthChange).toHaveBeenLastCalledWith('2030-03')
    fireEvent.click(screen.getByRole('button', { name: 'Next month' }))
    expect(onMonthChange).toHaveBeenLastCalledWith('2030-04')
    fireEvent.click(screen.getByRole('button', { name: 'Previous month' }))
    fireEvent.click(screen.getByRole('button', { name: 'Previous month' }))
    expect(onMonthChange).toHaveBeenLastCalledWith('2030-02')
    expect(onMonthChange).toHaveBeenCalledTimes(4)
  })

  it('does not repeat the month notice when something else re-renders it', () => {
    const onMonthChange = vi.fn()
    const { container } = render(<Harness onMonthChange={onMonthChange} />)
    fireEvent.click(cell(container, day(5)))
    fireEvent.click(cell(container, day(8)))
    expect(onMonthChange).toHaveBeenCalledTimes(1)
  })

  it('first click picks check-in, second click picks check-out', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)

    fireEvent.click(cell(container, day(10)))
    expect(onRange).toHaveBeenLastCalledWith(day(10), null)

    fireEvent.click(cell(container, day(13)))
    expect(onRange).toHaveBeenLastCalledWith(day(10), day(13))
  })

  it('highlights the start, the nights in between and the end', () => {
    const { container } = render(<Harness />)
    fireEvent.click(cell(container, day(10)))
    fireEvent.click(cell(container, day(13)))

    expect(cell(container, day(10))).toHaveClass('availability-calendar-day--range-start')
    expect(cell(container, day(11))).toHaveClass('availability-calendar-day--in-range')
    expect(cell(container, day(12))).toHaveClass('availability-calendar-day--in-range')
    expect(cell(container, day(13))).toHaveClass('availability-calendar-day--range-end')
    expect(cell(container, day(14))).not.toHaveClass('availability-calendar-day--in-range')
  })

  it('a click before the check-in starts again from that day', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)
    fireEvent.click(cell(container, day(10)))
    fireEvent.click(cell(container, day(8)))
    expect(onRange).toHaveBeenLastCalledWith(day(8), null)
  })

  it('a third click starts a new range', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)
    fireEvent.click(cell(container, day(10)))
    fireEvent.click(cell(container, day(12)))
    fireEvent.click(cell(container, day(20)))
    expect(onRange).toHaveBeenLastCalledWith(day(20), null)
  })

  it('blocks a range the validator rejects and shows why', () => {
    const onRange = vi.fn()
    const validateRange = (start: string, end: string) =>
      start <= day(11) && end > day(11) ? 'Wed, Mar 11 is not available' : null
    const { container } = render(<Harness onRange={onRange} validateRange={validateRange} />)

    fireEvent.click(cell(container, day(10)))
    fireEvent.click(cell(container, day(13)))

    expect(screen.getByRole('alert')).toHaveTextContent('Wed, Mar 11 is not available')
    expect(onRange).toHaveBeenLastCalledWith(day(10), null)
  })

  it('does not let a closed day start a stay, but it can be the check-out day', () => {
    const onRange = vi.fn()
    const describeDay = (date: string) => ({ selectable: date !== day(12) })
    const { container } = render(<Harness onRange={onRange} describeDay={describeDay} />)

    expect(cell(container, day(12))).toHaveAttribute('aria-disabled', 'true')
    fireEvent.click(cell(container, day(12)))
    expect(onRange).not.toHaveBeenCalled()

    fireEvent.click(cell(container, day(10)))
    expect(cell(container, day(12))).toHaveAttribute('aria-disabled', 'false')
    fireEvent.click(cell(container, day(12)))
    expect(onRange).toHaveBeenLastCalledWith(day(10), day(12))
  })

  it('days before minDate cannot be picked', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} minDate={day(15)} />)
    fireEvent.click(cell(container, day(14)))
    expect(onRange).not.toHaveBeenCalled()
    expect(cell(container, day(14))).toHaveAttribute('aria-disabled', 'true')
  })

  it('keeps the selection while moving between months', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)
    fireEvent.click(cell(container, day(30)))
    fireEvent.click(screen.getByRole('button', { name: /next month/i }))
    fireEvent.click(cell(container, '2030-04-02'))
    expect(onRange).toHaveBeenLastCalledWith(day(30), '2030-04-02')
  })

  it('works from the keyboard', () => {
    const onRange = vi.fn()
    const { container } = render(<Harness onRange={onRange} />)
    fireEvent.keyDown(cell(container, day(10)), { key: 'Enter' })
    fireEvent.keyDown(cell(container, day(11)), { key: ' ' })
    expect(onRange).toHaveBeenLastCalledWith(day(10), day(11))
  })
})
