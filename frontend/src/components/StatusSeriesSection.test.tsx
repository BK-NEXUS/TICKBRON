import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { StatusSeriesSection } from './StatusSeriesSection'
import { SERIES } from '../test/statusFixtures'

describe('StatusSeriesSection', () => {
  it('draws stayed, guests and revenue charts named after the granularity', () => {
    render(<StatusSeriesSection series={SERIES} granularity="month" onGranularityChange={vi.fn()} />)

    expect(screen.getByRole('img', { name: 'Stayed bookings per month' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Guests per month' })).toBeInTheDocument()
    // UZS has the larger total in the series, so it is the default chart currency
    expect(screen.getByRole('img', { name: 'Revenue (UZS) per month' })).toBeInTheDocument()
  })

  it('labels the buckets: month names, and dates for day and week', () => {
    const { rerender } = render(<StatusSeriesSection series={SERIES} granularity="month" onGranularityChange={vi.fn()} />)
    const chart = screen.getByRole('img', { name: 'Guests per month' })
    expect(within(chart).getByText('Aug')).toBeInTheDocument()
    expect(within(chart).getByText('Oct')).toBeInTheDocument()

    const days = [{ ...SERIES[0], period: '2026-10-01', start: '2026-10-01' }]
    rerender(<StatusSeriesSection series={days} granularity="day" onGranularityChange={vi.fn()} />)
    expect(within(screen.getByRole('img', { name: 'Guests per day' })).getByText('10-01')).toBeInTheDocument()

    const years = [{ ...SERIES[0], period: '2026', start: '2026-01-01' }]
    rerender(<StatusSeriesSection series={years} granularity="year" onGranularityChange={vi.fn()} />)
    expect(within(screen.getByRole('img', { name: 'Guests per year' })).getByText('2026')).toBeInTheDocument()
  })

  it('switches the revenue currency', () => {
    render(<StatusSeriesSection series={SERIES} granularity="month" onGranularityChange={vi.fn()} />)

    fireEvent.change(screen.getByLabelText('Revenue currency'), { target: { value: 'USD' } })

    expect(screen.getByRole('img', { name: 'Revenue (USD) per month' })).toBeInTheDocument()
  })

  it('reports a new granularity', () => {
    const onGranularityChange = vi.fn()
    render(<StatusSeriesSection series={SERIES} granularity="month" onGranularityChange={onGranularityChange} />)

    fireEvent.change(screen.getByLabelText('Group by'), { target: { value: 'week' } })

    expect(onGranularityChange).toHaveBeenCalledWith('week')
  })

  it('says so when there is nothing to chart', () => {
    render(<StatusSeriesSection series={[]} granularity="month" onGranularityChange={vi.fn()} />)

    expect(screen.getByText('No bookings in this period.')).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })

  it('shows a stayed chart without a revenue chart when there is no revenue', () => {
    const noMoney = SERIES.map(row => ({ ...row, revenue: [] }))
    render(<StatusSeriesSection series={noMoney} granularity="month" onGranularityChange={vi.fn()} />)

    expect(screen.getByRole('img', { name: 'Stayed bookings per month' })).toBeInTheDocument()
    expect(screen.queryByRole('img', { name: /Revenue/ })).not.toBeInTheDocument()
    expect(screen.getByText('No revenue in this period.')).toBeInTheDocument()
  })
})
