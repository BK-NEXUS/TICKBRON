import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerStatusTab } from './PartnerStatusTab'
import { statusAdapter } from '../adapters/statusAdapter'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { getPartnerStatus: vi.fn() },
}))

const getStatus = vi.mocked(statusAdapter.getPartnerStatus)

const months = Array.from({ length: 12 }, (_, i) => ({
  month: `2026-${String(i + 1).padStart(2, '0')}`,
  bookings: i === 3 ? 3 : 0,
  guests: i === 3 ? 3 : 0,
  revenue: i === 3 ? [{ currency: 'USD', amount: '350.00' }, { currency: 'EUR', amount: '60.00' }] : [],
}))

const STATUS = {
  since: '2025-01-15',
  period: 'all',
  totals: { bookings: 1205, guests: 1003, revenue: [{ currency: 'EUR', amount: '60.00' }, { currency: 'USD', amount: '12530.00' }] },
  properties: [
    { id: 1, name: 'Alpha Hotel', city: 'Tashkent', region: 'Tashkent', country: 'Uzbekistan', status: 'active',
      bookings: 1203, guests: 1001, revenue: [{ currency: 'USD', amount: '12450.00' }] },
    { id: 2, name: 'Beta Hotel', city: 'Tashkent', region: 'Unspecified', country: 'Uzbekistan', status: 'active',
      bookings: 2, guests: 2, revenue: [{ currency: 'EUR', amount: '60.00' }, { currency: 'USD', amount: '80.00' }] },
  ],
  year: 2026,
  available_years: [2025, 2026],
  monthly: months,
}

describe('PartnerStatusTab', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getStatus.mockResolvedValue({ data: STATUS, error: null })
  })

  it('summary cards: since when, bookings, guests via TICKBRON, revenue per currency', async () => {
    render(<PartnerStatusTab />)

    expect(await screen.findByRole('heading', { name: 'Status' })).toBeInTheDocument()
    expect(getStatus).toHaveBeenCalledWith({ period: 'all' })
    expect(screen.getByText('On TICKBRON since')).toBeInTheDocument()
    expect(screen.getByText('Jan 15, 2025')).toBeInTheDocument()
    expect(screen.getByText('Guests via TICKBRON')).toBeInTheDocument()
    expect(screen.getByText('1,003')).toBeInTheDocument()
    expect(screen.getByText('1,205')).toBeInTheDocument()
    expect(screen.getByText('€60.00 · $12,530.00')).toBeInTheDocument()
  })

  it('per-property table', async () => {
    render(<PartnerStatusTab />)

    const table = await screen.findByRole('table', { name: 'Your properties' })
    const rows = within(table).getAllByRole('row')
    expect(rows).toHaveLength(3)
    expect(within(rows[1]).getByText('Alpha Hotel')).toBeInTheDocument()
    expect(within(rows[1]).getByText('1,203')).toBeInTheDocument()
    expect(within(rows[1]).getByText('$12,450.00')).toBeInTheDocument()
    expect(within(rows[2]).getByText('€60.00 · $80.00')).toBeInTheDocument()
  })

  it('month or year selector', async () => {
    render(<PartnerStatusTab />)
    await screen.findByRole('table', { name: 'Your properties' })

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'month' } })

    await waitFor(() => expect(getStatus).toHaveBeenLastCalledWith(
      expect.objectContaining({ period: expect.stringMatching(/^\d{4}-\d{2}$/) })))
  })

  it('monthly chart with year and currency selectors', async () => {
    render(<PartnerStatusTab />)
    await screen.findByRole('table', { name: 'Your properties' })

    // USD has the larger total, so it is the default chart currency
    expect(screen.getByRole('img', { name: 'Revenue (USD) per month in 2026' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Guests per month in 2026' })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Chart currency'), { target: { value: 'EUR' } })
    expect(screen.getByRole('img', { name: 'Revenue (EUR) per month in 2026' })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Chart year'), { target: { value: '2025' } })
    await waitFor(() => expect(getStatus).toHaveBeenLastCalledWith({ period: 'all', year: 2025 }))
  })

  it('empty state when the owner has no properties', async () => {
    getStatus.mockResolvedValue({
      data: { ...STATUS, totals: { bookings: 0, guests: 0, revenue: [] }, properties: [] }, error: null,
    })
    render(<PartnerStatusTab />)

    expect(await screen.findByText('No properties yet. Numbers appear here once guests book them.')).toBeInTheDocument()
  })

  it('error state', async () => {
    getStatus.mockResolvedValue({ data: null, error: 'Hotel owner role required' })
    render(<PartnerStatusTab />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Hotel owner role required')
  })
})
