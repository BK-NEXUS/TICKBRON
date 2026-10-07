import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerStatusTab } from './PartnerStatusTab'
import { statusAdapter } from '../adapters/statusAdapter'
import { saveBlob } from '../utils/saveBlob'
import { PARTNER_HOTEL, PARTNER_STATUS, TOTALS } from '../test/statusFixtures'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: {
    getPartnerStatus: vi.fn(),
    getPartnerHotel: vi.fn(),
    getPartnerArrivals: vi.fn(),
    exportPartnerReconciliation: vi.fn(),
  },
}))
vi.mock('../utils/saveBlob', () => ({ saveBlob: vi.fn() }))

const getStatus = vi.mocked(statusAdapter.getPartnerStatus)
const getHotel = vi.mocked(statusAdapter.getPartnerHotel)
const getArrivals = vi.mocked(statusAdapter.getPartnerArrivals)
const exportCsv = vi.mocked(statusAdapter.exportPartnerReconciliation)

const months = Array.from({ length: 12 }, (_, i) => ({
  month: `2026-${String(i + 1).padStart(2, '0')}`,
  bookings: i === 3 ? 3 : 0,
  guests: i === 3 ? 3 : 0,
  revenue: i === 3 ? [{ currency: 'USD', amount: '350.00' }, { currency: 'EUR', amount: '60.00' }] : [],
}))

const STATUS = {
  ...PARTNER_STATUS,
  since: '2025-01-15',
  period: 'all',
  totals: {
    ...TOTALS, bookings: 1205, counted: 1205, stayed: 1100, guests: 1003, upcoming: 9,
    revenue: [{ currency: 'EUR', amount: '60.00' }, { currency: 'USD', amount: '12530.00' }],
  },
  properties: [
    { id: 1, name: 'Alpha Hotel', city: 'Tashkent', region: 'Tashkent', country: 'Uzbekistan', status: 'active',
      bookings: 1203, guests: 1001, unique_customers: 800, nights: 4000, room_nights: 4300, stayed: 1090, booking_value: [],
      revenue: [{ currency: 'USD', amount: '12450.00' }] },
    { id: 2, name: 'Beta Hotel', city: 'Tashkent', region: 'Unspecified', country: 'Uzbekistan', status: 'active',
      bookings: 2, guests: 2, unique_customers: 2, nights: 4, room_nights: 4, stayed: 1, booking_value: [],
      revenue: [{ currency: 'EUR', amount: '60.00' }, { currency: 'USD', amount: '80.00' }] },
  ],
  year: 2026,
  available_years: [2025, 2026],
  monthly: months,
}

describe('PartnerStatusTab', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getStatus.mockResolvedValue({ data: STATUS, error: null })
    getArrivals.mockResolvedValue({
      data: { count: 0, next: null, previous: null, results: [], day: 'today', date: '2026-10-07' }, error: null,
    })
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
      data: { ...STATUS, totals: { ...TOTALS, bookings: 0, counted: 0, stayed: 0, guests: 0, revenue: [] }, properties: [] }, error: null,
    })
    render(<PartnerStatusTab />)

    expect(await screen.findByText('No properties yet. Numbers appear here once guests book them.')).toBeInTheDocument()
  })

  it('error state', async () => {
    getStatus.mockResolvedValue({ data: null, error: 'Hotel owner role required' })
    render(<PartnerStatusTab />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Hotel owner role required')
  })

  describe('R12a', () => {
    it('leads with stayed, keeps counted and upcoming apart, and shows the may-still-change note', async () => {
      render(<PartnerStatusTab />)
      await screen.findByRole('table', { name: 'Your properties' })

      const headline = document.querySelector('.status-card--headline') as HTMLElement
      expect(within(headline).getByText('Stayed bookings')).toBeInTheDocument()
      expect(within(headline).getByText('1,100')).toBeInTheDocument()
      expect(within(screen.getByText('Upcoming').closest('.status-card') as HTMLElement).getByText('9')).toBeInTheDocument()
      expect(screen.getAllByRole('note').length).toBeGreaterThan(0)
    })

    it('shows the series by granularity and the reconciliation block', async () => {
      render(<PartnerStatusTab />)
      await screen.findByRole('table', { name: 'Your properties' })

      expect(screen.getByRole('img', { name: 'Stayed bookings per month' })).toBeInTheDocument()
      expect(screen.getByRole('table', { name: 'Reconciliation' })).toBeInTheDocument()

      fireEvent.change(screen.getByLabelText('Group by'), { target: { value: 'week' } })
      await waitFor(() => expect(getStatus).toHaveBeenLastCalledWith({ period: 'all', granularity: 'week' }))
    })

    it('a custom range is sent with from and to', async () => {
      render(<PartnerStatusTab />)
      await screen.findByRole('table', { name: 'Your properties' })

      fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'custom' } })
      fireEvent.change(screen.getByLabelText('From'), { target: { value: '2026-01-01' } })
      fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-03-01' } })
      fireEvent.click(screen.getByRole('button', { name: 'Apply' }))

      await waitFor(() => expect(getStatus).toHaveBeenLastCalledWith(
        { period: 'custom', from: '2026-01-01', to: '2026-03-01' }))
    })

    it('exports the reconciliation CSV for the current period', async () => {
      exportCsv.mockResolvedValue({ data: { blob: new Blob(['x']), filename: 'partner_reconciliation.csv' }, error: null })
      render(<PartnerStatusTab />)
      await screen.findByRole('table', { name: 'Your properties' })

      fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))

      await waitFor(() => expect(saveBlob).toHaveBeenCalled())
      expect(exportCsv).toHaveBeenCalledWith({ period: 'all' })
    })

    it('lists today and tomorrow arrivals of all hotels', async () => {
      render(<PartnerStatusTab />)
      await screen.findByRole('table', { name: 'Your properties' })

      await waitFor(() => expect(getArrivals).toHaveBeenCalledWith({ day: 'today', page: 1 }))
      expect(screen.getByRole('button', { name: 'Tomorrow' })).toBeInTheDocument()
    })

    it('opens one own hotel and comes back', async () => {
      getHotel.mockResolvedValue({ data: PARTNER_HOTEL, error: null })
      render(<PartnerStatusTab />)
      const table = await screen.findByRole('table', { name: 'Your properties' })

      fireEvent.click(within(table).getByRole('button', { name: 'Alpha Hotel' }))

      expect(await screen.findByRole('heading', { name: 'Alpha Hotel' })).toBeInTheDocument()
      expect(getHotel).toHaveBeenCalledWith(1, { period: 'all' })

      fireEvent.click(screen.getByRole('button', { name: 'Back to Status' }))
      expect(await screen.findByRole('table', { name: 'Your properties' })).toBeInTheDocument()
    })

    it('a backend validation error stays inline and the period selector keeps working', async () => {
      getStatus.mockResolvedValueOnce({ data: STATUS, error: null })
      getStatus.mockResolvedValueOnce({ data: null, error: 'The range can be at most 20 years.' })
      render(<PartnerStatusTab />)
      await screen.findByRole('table', { name: 'Your properties' })

      fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'last_10_years' } })

      expect(await screen.findByRole('alert')).toHaveTextContent('at most 20 years')
      expect(screen.getByLabelText('Period')).toHaveValue('last_10_years')
    })

    it('never renders API text as HTML', async () => {
      getStatus.mockResolvedValue({
        data: { ...STATUS, properties: [{ ...STATUS.properties[0], name: '<img src=x onerror=alert(1)>' }] }, error: null,
      })
      const { container } = render(<PartnerStatusTab />)

      expect(await screen.findByRole('button', { name: '<img src=x onerror=alert(1)>' })).toBeInTheDocument()
      expect(container.querySelector('img')).toBeNull()
    })
  })
})
