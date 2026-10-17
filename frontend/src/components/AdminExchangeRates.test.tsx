import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { AdminExchangeRates } from './AdminExchangeRates'
import { I18nProvider } from '../i18n/I18nContext'
import { exchangeRateAdapter, type CurrencyRateStatus, type ExchangeRateRow } from '../adapters/exchangeRateAdapter'

vi.mock('../adapters/exchangeRateAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/exchangeRateAdapter')>()),
  exchangeRateAdapter: { list: vi.fn(), status: vi.fn(), accept: vi.fn() },
}))

const api = vi.mocked(exchangeRateAdapter)

const row = (id: number, patch: Partial<ExchangeRateRow> = {}): ExchangeRateRow => ({
  id, currency: 'USD', rate: '11772.950000', nominal: 1, rate_date: '2026-10-03', source: 'cbu.uz',
  status: 'accepted', note: '', fetched_at: '2026-10-03T06:00:00Z', ...patch,
})
const usd = (patch: Partial<CurrencyRateStatus> = {}): CurrencyRateStatus => ({
  currency: 'USD', rate: '11772.950000', date: '2026-10-03', source: 'cbu.uz', stale: false,
  last_fetch: { attempted_at: '2026-10-03T06:00:00Z', success: true, error: '' }, last_error: null, rejected: [], ...patch,
})
const page = (results: ExchangeRateRow[], extra = {}) => ({
  data: { count: results.length, next: null, previous: null, results, ...extra }, error: null,
})

function renderScreen(isSuperAdmin: boolean) {
  localStorage.setItem('tickbron.language', 'en')
  return render(<I18nProvider><AdminExchangeRates isSuperAdmin={isSuperAdmin} /></I18nProvider>)
}

describe('AdminExchangeRates', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetAllMocks()
    api.list.mockResolvedValue(page([row(2), row(1, { rate_date: '2026-10-02', rate: '11750.000000' })]))
    api.status.mockResolvedValue({ data: { currencies: [usd()] }, error: null })
    api.accept.mockResolvedValue({ data: row(9), error: null })
  })

  it('staff see the history but not the fetch status, and are told why', async () => {
    renderScreen(false)
    expect(await screen.findByRole('table')).toBeInTheDocument()
    expect(within(screen.getByRole('table')).getAllByRole('row')).toHaveLength(3)
    expect(api.status).not.toHaveBeenCalled()
    expect(screen.getByText('Only a super-admin can see the fetch status and accept a rate.')).toBeInTheDocument()
  })

  it('the super-admin sees the current rate with its date and source', async () => {
    renderScreen(true)
    const card = (await screen.findByText(/1 USD = /)).closest('.fx-rate-card') as HTMLElement
    expect(card).toHaveTextContent('1 USD = 11,772.95 UZS')
    expect(card).toHaveTextContent('Rate of Oct 3, 2026, source cbu.uz')
    expect(screen.queryByRole('alert')).toBeNull()
  })

  it('warns when a rate is out of date', async () => {
    api.status.mockResolvedValue({ data: { currencies: [usd({ stale: true })] }, error: null })
    renderScreen(true)
    expect(await screen.findByRole('alert')).toHaveTextContent('The latest USD rate is out of date.')
  })

  it('says so when no rate has ever been fetched, with the last error', async () => {
    api.status.mockResolvedValue({
      data: { currencies: [usd({ rate: null, date: null, source: null, stale: true, last_error: 'cbu.uz timed out' })] }, error: null,
    })
    renderScreen(true)
    expect(await screen.findByText(/No rate has been fetched yet/)).toBeInTheDocument()
    expect(screen.getByText('Last fetch failed: cbu.uz timed out')).toBeInTheDocument()
  })

  it('lists rejected rates with the number waiting for a decision', async () => {
    api.status.mockResolvedValue({
      data: { currencies: [usd({ rejected: [row(5, { status: 'rejected', rate: '13500.000000', rate_date: '2026-10-04', note: 'change over 10%' })] })] },
      error: null,
    })
    renderScreen(true)
    expect(await screen.findByText('1 fetched rate was rejected (change over the limit) and waits for your decision.')).toBeInTheDocument()
    const rejected = screen.getByRole('heading', { name: 'Rejected rates' }).parentElement as HTMLElement
    expect(rejected).toHaveTextContent('13,500.00')
    expect(rejected).toHaveTextContent('change over 10%')
  })

  describe('accepting a rejected rate', () => {
    const withRejected = () => api.status.mockResolvedValue({
      data: { currencies: [usd({ rejected: [row(5, { status: 'rejected', rate: '13500.000000', rate_date: '2026-10-04' })] })] }, error: null,
    })

    it('asks first, then accepts and reloads the screen', async () => {
      withRejected()
      renderScreen(true)
      fireEvent.click(await screen.findByRole('button', { name: 'Accept the USD rate of Oct 4, 2026' }))
      const dialog = screen.getByRole('dialog')
      expect(dialog).toHaveTextContent('Accept 1 USD = 13,500.00 UZS for Oct 4, 2026?')
      expect(api.accept).not.toHaveBeenCalled()

      api.status.mockResolvedValue({ data: { currencies: [usd({ rate: '13500.000000', date: '2026-10-04' })] }, error: null })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Accept' }))
      await waitFor(() => expect(api.accept).toHaveBeenCalledWith(5))
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
      expect(api.status.mock.calls.length).toBeGreaterThan(1)
      expect(api.list.mock.calls.length).toBeGreaterThan(1)
    })

    it('Cancel changes nothing', async () => {
      withRejected()
      renderScreen(true)
      fireEvent.click(await screen.findByRole('button', { name: 'Accept the USD rate of Oct 4, 2026' }))
      fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Cancel' }))
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(api.accept).not.toHaveBeenCalled()
    })

    it('shows the backend reason when it refuses (409: a rate for that date is already accepted)', async () => {
      withRejected()
      api.accept.mockResolvedValue({ data: null, error: 'A rate for that date is already accepted', status: 409 })
      renderScreen(true)
      fireEvent.click(await screen.findByRole('button', { name: 'Accept the USD rate of Oct 4, 2026' }))
      fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Accept' }))
      expect(await within(screen.getByRole('dialog')).findByRole('alert')).toHaveTextContent('already accepted')
    })
  })

  it('pages through the history', async () => {
    api.list.mockResolvedValue(page([row(2)], { count: 45, next: 'http://x/?page=2' }))
    renderScreen(false)
    await screen.findByRole('table')
    fireEvent.click(screen.getByRole('button', { name: /next/i }))
    await waitFor(() => expect(api.list).toHaveBeenLastCalledWith({ page: 2 }))
  })

  it('shows loading, then an error with Try Again, then the empty state', async () => {
    api.list.mockResolvedValueOnce({ data: null, error: 'boom' })
    renderScreen(false)
    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load the exchange rates.')
    api.list.mockResolvedValueOnce(page([]))
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByText('No rates have been fetched yet.')).toBeInTheDocument()
  })
})
