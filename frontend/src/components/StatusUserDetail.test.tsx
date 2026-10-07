import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { StatusUserDetail } from './StatusUserDetail'
import { statusAdapter } from '../adapters/statusAdapter'
import { saveBlob } from '../utils/saveBlob'
import { TOTALS } from '../test/statusFixtures'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { getUserDetail: vi.fn(), exportUserHistory: vi.fn() },
}))
vi.mock('../utils/saveBlob', () => ({ saveBlob: vi.fn() }))

const getUser = vi.mocked(statusAdapter.getUserDetail)
const exportHistory = vi.mocked(statusAdapter.exportUserHistory)

const BOOKING = {
  id: 901, reference: 'TB-901', hotel: { id: 11, name: 'Alpha Hotel' }, check_in: '2026-04-10', check_out: '2026-04-13',
  nights: 3, rooms: 1, guests: 2, status: 'completed', total_price: '300.00', currency: 'USD',
  charge_amount: '3750000.00', charge_currency: 'UZS', paid: [{ currency: 'UZS', amount: '3750000.00' }], refunded: [],
}

const DETAIL = {
  user: {
    id: 42, full_name: 'Madina Nazarova', first_name: 'Madina', last_name: 'Nazarova', phone: '+998903330002',
    email: 'guest2@example.com', date_joined: '2025-02-01T10:00:00Z',
  },
  period: 'all',
  period_range: { from: null, to: null },
  totals: { ...TOTALS, stayed: 7, counted: 8, guests: 15 },
  hotels_visited: 2,
  hotels: [
    { id: 11, name: 'Alpha Hotel', city: 'Tashkent', country: 'Uzbekistan', bookings: 5, stayed: 4, nights: 12, guests: 9,
      spent: [{ currency: 'UZS', amount: '3750000.00' }, { currency: 'USD', amount: '120.00' }] },
    { id: 12, name: 'Beta Hotel', city: 'Samarkand', country: 'Uzbekistan', bookings: 3, stayed: 3, nights: 6, guests: 6,
      spent: [{ currency: 'USD', amount: '90.00' }] },
  ],
  history: { count: 1, next: null, previous: null, results: [BOOKING] },
}

const loaded = (extra: Record<string, unknown> = {}) => ({ data: { ...DETAIL, ...extra }, error: null }) as never

function renderDetail(props: Partial<React.ComponentProps<typeof StatusUserDetail>> = {}) {
  const handlers = { onPeriodChange: vi.fn(), onRangeChange: vi.fn() }
  render(<StatusUserDetail userId={42} period="all" {...handlers} {...props} />)
  return handlers
}

describe('StatusUserDetail', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    getUser.mockResolvedValue(loaded())
  })

  it('shows a loading state first', () => {
    getUser.mockReturnValue(new Promise(() => {}))
    renderDetail()
    expect(screen.getByRole('status')).toHaveTextContent('Loading user...')
  })

  it('shows the guest, totals with stayed first, and the may-still-change note', async () => {
    renderDetail()

    expect(await screen.findByRole('heading', { name: 'Madina Nazarova' })).toBeInTheDocument()
    expect(getUser).toHaveBeenCalledWith(42, { period: 'all', page: 1 })
    expect(screen.getByText('guest2@example.com')).toBeInTheDocument()
    expect(screen.getByText('+998903330002')).toBeInTheDocument()
    const stayed = document.querySelector('.status-card--headline') as HTMLElement
    expect(within(stayed).getByText('Stayed bookings')).toBeInTheDocument()
    expect(within(stayed).getByText('7')).toBeInTheDocument()
    expect(screen.getByRole('note')).toHaveTextContent('can still change')
  })

  it('shows hotels visited and a per-hotel table with money per currency', async () => {
    renderDetail()
    await screen.findByRole('heading', { name: 'Madina Nazarova' })

    expect(screen.getByText('Hotels visited').nextSibling).toHaveTextContent('2')
    const table = screen.getByRole('table', { name: 'Hotels' })
    const row = within(table).getByText('Alpha Hotel').closest('tr') as HTMLElement
    expect(within(row).getByText('UZS 3,750,000.00 · $120.00')).toBeInTheDocument()
    expect(within(row).getByText('Tashkent, Uzbekistan')).toBeInTheDocument()
  })

  it('lists the booking history with every status, paid and refunded', async () => {
    getUser.mockResolvedValue(loaded({
      history: {
        count: 2, next: null, previous: null,
        results: [BOOKING, { ...BOOKING, id: 902, reference: 'TB-902', status: 'cancelled', paid: [], refunded: [{ currency: 'UZS', amount: '100000.00' }] }],
      },
    }))
    renderDetail()
    await screen.findByRole('heading', { name: 'Madina Nazarova' })

    const table = screen.getByRole('table', { name: 'Booking history' })
    const first = within(table).getByText('TB-901').closest('tr') as HTMLElement
    expect(within(first).getByText('Apr 10, 2026')).toBeInTheDocument()
    expect(within(first).getByText('$300.00')).toBeInTheDocument()
    expect(within(first).getByText('completed')).toBeInTheDocument()
    const second = within(table).getByText('TB-902').closest('tr') as HTMLElement
    expect(within(second).getByText('cancelled')).toBeInTheDocument()
    expect(within(second).getByText('UZS 100,000.00')).toBeInTheDocument()
  })

  it('paginates the history on the server and starts over when the period changes', async () => {
    getUser.mockResolvedValue(loaded({
      history: { count: 45, next: 'http://x/?page=2', previous: null, results: [BOOKING] },
    }))
    const { onPeriodChange } = renderDetail()
    await screen.findByText('Page 1 of 3')

    fireEvent.click(screen.getByRole('button', { name: 'Next page' }))
    await waitFor(() => expect(getUser).toHaveBeenLastCalledWith(42, { period: 'all', page: 2 }))

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'this_year' } })
    expect(onPeriodChange).toHaveBeenCalledWith('this_year')
  })

  it('requests the applied custom range', async () => {
    renderDetail({ period: 'custom', range: { from: '2026-01-01', to: '2026-03-01' } })
    await screen.findByRole('heading', { name: 'Madina Nazarova' })

    expect(getUser).toHaveBeenCalledWith(42, { period: 'custom', from: '2026-01-01', to: '2026-03-01', page: 1 })
  })

  it('exports the history as CSV', async () => {
    exportHistory.mockResolvedValue({ data: { blob: new Blob(['x']), filename: 'status_user_42_history.csv' }, error: null })
    renderDetail()
    await screen.findByRole('heading', { name: 'Madina Nazarova' })

    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))

    await waitFor(() => expect(saveBlob).toHaveBeenCalled())
    expect(exportHistory).toHaveBeenCalledWith(42, { period: 'all' })
  })

  it('says so when there is no history or no hotel', async () => {
    getUser.mockResolvedValue(loaded({
      hotels_visited: 0, hotels: [], history: { count: 0, next: null, previous: null, results: [] },
    }))
    renderDetail()

    expect(await screen.findByText('No hotels in this period.')).toBeInTheDocument()
    expect(screen.getByText('No bookings in this period.')).toBeInTheDocument()
  })

  it('shows "not found" for an unknown user and a backend message inline', async () => {
    getUser.mockResolvedValue({ data: null, error: 'Not found' })
    renderDetail()
    expect(await screen.findByRole('alert')).toHaveTextContent('Not found')
    expect(screen.getByLabelText('Period')).toBeEnabled()
  })

  it('never renders API text as HTML', async () => {
    getUser.mockResolvedValue(loaded({
      user: { ...DETAIL.user, full_name: '<img src=x onerror=alert(1)>' },
    }))
    const { container } = render(<StatusUserDetail userId={42} period="all" onPeriodChange={vi.fn()} onRangeChange={vi.fn()} />)

    expect(await screen.findByRole('heading', { name: '<img src=x onerror=alert(1)>' })).toBeInTheDocument()
    expect(container.querySelector('img')).toBeNull()
  })
})
