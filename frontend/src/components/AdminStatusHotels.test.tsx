import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { AdminStatusHotels } from './AdminStatusHotels'
import { statusAdapter } from '../adapters/statusAdapter'
import { useStatusPeriod } from '../hooks/useStatusPeriod'
import { saveBlob } from '../utils/saveBlob'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { getAdminHotels: vi.fn(), exportAdminHotels: vi.fn() },
}))
vi.mock('../utils/saveBlob', () => ({ saveBlob: vi.fn() }))

const getHotels = vi.mocked(statusAdapter.getAdminHotels)
const exportHotels = vi.mocked(statusAdapter.exportAdminHotels)

const HOTEL = {
  rank: 1, id: 11, name: 'Alpha Hotel', city: 'Tashkent', region_id: 3, region: 'Tashkent', country_code: 'UZ',
  status: 'active', created_at: '2025-01-15T09:00:00Z', rating: '4.50', bookings: 1500, guests: 3210,
  unique_customers: 1100, nights: 5400, room_nights: 6100, stayed: 1380,
  revenue: [{ currency: 'UZS', amount: '1500000000.00' }, { currency: 'USD', amount: '45000.00' }],
  booking_value: [{ currency: 'UZS', amount: '1600000000.00' }],
}
const UNRATED = { ...HOTEL, rank: 2, id: 12, name: 'Beta Hotel', rating: null, revenue: [], stayed: 0, bookings: 0, guests: 0, nights: 0 }

const pageOf = (results: unknown[], extra: Record<string, unknown> = {}) => ({
  data: {
    count: results.length, next: null, previous: null, results, period: 'all',
    period_range: { from: null, to: null }, ordering: '-bookings', ...extra,
  },
  error: null,
}) as never

function Harness({ onOpen = vi.fn() }: { onOpen?: (hotel: { id: number; name: string }) => void }) {
  const state = useStatusPeriod()
  return (
    <AdminStatusHotels
      period={state.period} range={state.range} onPeriodChange={state.setPeriod} onRangeChange={state.setRange}
      onOpen={onOpen}
    />
  )
}

describe('AdminStatusHotels', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getHotels.mockResolvedValue(pageOf([HOTEL, UNRATED]))
  })

  it('lists hotels with the R12a numbers, per-currency revenue and thousand separators', async () => {
    render(<Harness />)

    const row = (await screen.findByRole('button', { name: 'Alpha Hotel' })).closest('tr') as HTMLElement
    expect(getHotels).toHaveBeenCalledWith({ period: 'all', search: '', page: 1, ordering: '-bookings' })
    expect(within(row).getByText('Tashkent, Tashkent, UZ')).toBeInTheDocument()
    expect(within(row).getByText('4.50')).toBeInTheDocument()
    expect(within(row).getByText('Jan 15, 2025')).toBeInTheDocument()
    expect(within(row).getByText('1,500')).toBeInTheDocument()
    expect(within(row).getByText('1,380')).toBeInTheDocument()
    expect(within(row).getByText('3,210')).toBeInTheDocument()
    expect(within(row).getByText('5,400')).toBeInTheDocument()
    expect(within(row).getByText('UZS 1,500,000,000.00 · $45,000.00')).toBeInTheDocument()
  })

  it('shows a dash for no rating and no revenue', async () => {
    render(<Harness />)
    const row = (await screen.findByRole('button', { name: 'Beta Hotel' })).closest('tr') as HTMLElement
    expect(within(row).getAllByText('—').length).toBeGreaterThanOrEqual(2)
  })

  it('sorts server-side by revenue, bookings, guests, nights, rating and created date', async () => {
    render(<Harness />)
    await screen.findByRole('button', { name: 'Alpha Hotel' })

    const select = screen.getByLabelText('Sort by')
    expect(Array.from(select.querySelectorAll('option')).map(o => (o as HTMLOptionElement).value))
      .toEqual(['revenue', 'bookings', 'guests', 'nights', 'rating', 'created_at'])

    fireEvent.change(select, { target: { value: 'revenue' } })
    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(
      { period: 'all', search: '', page: 1, ordering: '-revenue' }))

    fireEvent.change(screen.getByLabelText('Order'), { target: { value: 'asc' } })
    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(
      { period: 'all', search: '', page: 1, ordering: 'revenue' }))
  })

  it('searches from the first page', async () => {
    render(<Harness />)
    await screen.findByRole('button', { name: 'Alpha Hotel' })

    fireEvent.change(screen.getByLabelText('Search hotels'), { target: { value: 'hilton' } })

    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(
      { period: 'all', search: 'hilton', page: 1, ordering: '-bookings' }))
  })

  it('paginates on the server', async () => {
    getHotels.mockResolvedValue(pageOf([HOTEL], { count: 45, next: 'http://x/?page=2' }))
    render(<Harness />)
    await screen.findByText('Page 1 of 3')

    fireEvent.click(screen.getByRole('button', { name: 'Next page' }))

    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(
      { period: 'all', search: '', page: 2, ordering: '-bookings' }))
  })

  it('filters by a preset and by a custom range', async () => {
    render(<Harness />)
    await screen.findByRole('button', { name: 'Alpha Hotel' })

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'last_30_days' } })
    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(expect.objectContaining({ period: 'last_30_days' })))

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'custom' } })
    fireEvent.change(screen.getByLabelText('From'), { target: { value: '2026-01-01' } })
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-03-01' } })
    fireEvent.click(screen.getByRole('button', { name: 'Apply' }))
    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(
      expect.objectContaining({ period: 'custom', from: '2026-01-01', to: '2026-03-01' })))
  })

  it('exports the CSV with the current period, search and sort, without a page', async () => {
    exportHotels.mockResolvedValue({ data: { blob: new Blob(['x']), filename: 'status_hotels.csv' }, error: null })
    render(<Harness />)
    await screen.findByRole('button', { name: 'Alpha Hotel' })
    fireEvent.change(screen.getByLabelText('Sort by'), { target: { value: 'guests' } })
    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(expect.objectContaining({ ordering: '-guests' })))
    fireEvent.change(screen.getByLabelText('Search hotels'), { target: { value: 'alp' } })
    await waitFor(() => expect(getHotels).toHaveBeenLastCalledWith(expect.objectContaining({ search: 'alp' })))

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))

    await waitFor(() => expect(saveBlob).toHaveBeenCalled())
    expect(exportHotels).toHaveBeenCalledWith({ period: 'all', search: 'alp', ordering: '-guests' })
  })

  it('opens a hotel from its name', async () => {
    const onOpen = vi.fn()
    render(<Harness onOpen={onOpen} />)

    fireEvent.click(await screen.findByRole('button', { name: 'Alpha Hotel' }))

    expect(onOpen).toHaveBeenCalledWith(expect.objectContaining({ id: 11, name: 'Alpha Hotel' }))
  })

  it('shows loading, empty and error states', async () => {
    getHotels.mockReturnValueOnce(new Promise(() => {}))
    const { unmount } = render(<Harness />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading hotels...')
    unmount()

    getHotels.mockResolvedValue(pageOf([]))
    const empty = render(<Harness />)
    expect(await screen.findByText('No hotels found for this period.')).toBeInTheDocument()
    empty.unmount()

    getHotels.mockResolvedValue({ data: null, error: 'Admin or staff role required' })
    render(<Harness />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Admin or staff role required')
  })

  it('keeps the period selector after a backend validation error', async () => {
    getHotels.mockResolvedValueOnce(pageOf([HOTEL]))
    getHotels.mockResolvedValueOnce({ data: null, error: 'The range can be at most 20 years.' })
    render(<Harness />)
    await screen.findByRole('button', { name: 'Alpha Hotel' })

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'last_10_years' } })

    expect(await screen.findByRole('alert')).toHaveTextContent('at most 20 years')
    expect(screen.getByLabelText('Period')).toHaveValue('last_10_years')
  })

  it('never renders API text as HTML', async () => {
    getHotels.mockResolvedValue(pageOf([{ ...HOTEL, name: '<img src=x onerror=alert(1)>' }]))
    const { container } = render(<Harness />)

    expect(await screen.findByRole('button', { name: '<img src=x onerror=alert(1)>' })).toBeInTheDocument()
    expect(container.querySelector('img')).toBeNull()
  })
})
