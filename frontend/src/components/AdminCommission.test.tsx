import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within, act } from '@testing-library/react'
import { AdminCommission } from './AdminCommission'
import { I18nProvider } from '../i18n/I18nContext'
import { adminAdapter } from '../adapters/adminAdapter'
import type { CommissionOwnerRow, CommissionStatement } from '../adapters/commissionTypes'

vi.mock('../adapters/adminAdapter', () => ({
  adminAdapter: {
    getCommissionOwners: vi.fn(), getCommissionStatement: vi.fn(), setCommissionPercent: vi.fn(),
    confirmCommissionMonth: vi.fn(), undoCommissionMonth: vi.fn(),
  },
}))

const adapter = vi.mocked(adminAdapter)

const OWNER: CommissionOwnerRow = {
  id: 7, name: 'Olim Karimov', email: 'olim@example.com', phone_number: '+998901112233', percent: '2.00',
  this_month: { month: '2026-05', bookings: 1, gross: [{ currency: 'USD', amount: '1000.00' }], commission: [{ currency: 'USD', amount: '20.00' }] },
  unpaid: [{ currency: 'USD', amount: '20.00' }],
}

const STATEMENT: CommissionStatement = {
  percent: '2.00', percent_since: '2026-01-01', years: null,
  months: [
    { month: '2026-03', bookings: 1, gross: [{ currency: 'USD', amount: '1000.00' }], percent: '2.00', commission: [{ currency: 'USD', amount: '20.00' }], paid: null },
    { month: '2026-01', bookings: 1, gross: [{ currency: 'USD', amount: '500.00' }], percent: '2.00', commission: [{ currency: 'USD', amount: '10.00' }],
      paid: { by: 'Boss Person', role: 'super_admin', at: '2026-02-03T09:00:00Z', amounts: [{ currency: 'USD', amount: '10.00' }] } },
  ],
}

const list = (...rows: CommissionOwnerRow[]) => ({ data: { count: rows.length, hasMore: false, results: rows }, error: null })

function show(isSuperAdmin = true) {
  localStorage.setItem('tickbron.language', 'en')
  render(<I18nProvider><AdminCommission isSuperAdmin={isSuperAdmin} /></I18nProvider>)
}

async function openOwner() {
  fireEvent.click(await screen.findByRole('button', { name: 'Open: Olim Karimov' }))
  await screen.findByText('Month by month')
}

describe('AdminCommission', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    adapter.getCommissionOwners.mockResolvedValue(list(OWNER))
    adapter.getCommissionStatement.mockResolvedValue({ data: STATEMENT, error: null })
    adapter.setCommissionPercent.mockResolvedValue({ data: { ...STATEMENT, percent: '3.50' }, error: null })
    adapter.confirmCommissionMonth.mockResolvedValue({ data: STATEMENT, error: null })
    adapter.undoCommissionMonth.mockResolvedValue({ data: STATEMENT, error: null })
  })

  afterEach(() => { vi.useRealTimers() })

  it('lists the owners with their percent, this month and the unpaid ended months', async () => {
    show()
    expect(await screen.findByText('Olim Karimov')).toBeInTheDocument()
    expect(screen.getByText('2.00%')).toBeInTheDocument()
    expect(screen.getByText(/olim@example.com/)).toBeInTheDocument()
    expect(adapter.getCommissionOwners).toHaveBeenCalledWith({ search: '', page: 1 })
  })

  it('has an empty state, a loading state and a failed load with Try Again', async () => {
    adapter.getCommissionOwners.mockResolvedValueOnce({ data: null, error: 'down' })
    show()
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
    expect(await screen.findByRole('alert')).toHaveTextContent('down')
    adapter.getCommissionOwners.mockResolvedValueOnce(list())
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByText('No hotel owners found.')).toBeInTheDocument()
  })

  it('searches after a short pause and asks the server for the typed text, from page 1', async () => {
    show()
    await screen.findByText('Olim Karimov')
    vi.useFakeTimers()
    fireEvent.change(screen.getByLabelText('Search'), { target: { value: ' My Hotel ' } })
    await act(async () => { await vi.advanceTimersByTimeAsync(400) })
    vi.useRealTimers()
    await waitFor(() => expect(adapter.getCommissionOwners).toHaveBeenLastCalledWith({ search: 'My Hotel', page: 1 }))
  })

  it('shows a super admin the percent form and saves a valid percent', async () => {
    show(true)
    await openOwner()
    const field = screen.getByLabelText('Commission percent (%)')
    expect(field).toHaveValue('2.00')
    fireEvent.change(field, { target: { value: '3.5' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save percent' }))
    await waitFor(() => expect(adapter.setCommissionPercent).toHaveBeenCalledWith(7, '3.5'))
    expect(await screen.findByText('The percent was saved.')).toBeInTheDocument()
  })

  it.each(['abc', '101', '1.234', '-2', ''])('refuses the percent "%s" before calling the server', async (value) => {
    show(true)
    await openOwner()
    fireEvent.change(screen.getByLabelText('Commission percent (%)'), { target: { value } })
    fireEvent.click(screen.getByRole('button', { name: 'Save percent' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a percent from 0 to 100')
    expect(adapter.setCommissionPercent).not.toHaveBeenCalled()
  })

  it('shows the server error when saving the percent fails', async () => {
    adapter.setCommissionPercent.mockResolvedValueOnce({ data: null, error: 'Not allowed' })
    show(true)
    await openOwner()
    fireEvent.click(screen.getByRole('button', { name: 'Save percent' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Not allowed')
  })

  it('does not show staff the percent form', async () => {
    show(false)
    await openOwner()
    expect(screen.queryByLabelText('Commission percent (%)')).not.toBeInTheDocument()
  })

  it('lets staff confirm an ended unpaid month and take back a paid one', async () => {
    show(false)
    await openOwner()
    const march = screen.getByRole('row', { name: /March 2026/ })
    fireEvent.click(within(march).getByRole('button', { name: /Mark as paid/ }))
    await waitFor(() => expect(adapter.confirmCommissionMonth).toHaveBeenCalledWith(7, '2026-03'))
    const january = screen.getByRole('row', { name: /January 2026/ })
    expect(within(january).getByText('Confirmed by Boss Person (Super admin)')).toBeInTheDocument()
    fireEvent.click(within(january).getByRole('button', { name: /Take back/ }))
    await waitFor(() => expect(adapter.undoCommissionMonth).toHaveBeenCalledWith(7, '2026-01'))
  })

  it('shows the server answer when a confirmation is refused', async () => {
    adapter.confirmCommissionMonth.mockResolvedValueOnce({ data: null, error: 'This month is already confirmed as paid.' })
    show(false)
    await openOwner()
    fireEvent.click(within(screen.getByRole('row', { name: /March 2026/ })).getByRole('button', { name: /Mark as paid/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('already confirmed')
  })

  it('goes back to the list and reads it again', async () => {
    show()
    await openOwner()
    fireEvent.click(screen.getByRole('button', { name: 'Back to the list' }))
    expect(await screen.findByText('Olim Karimov')).toBeInTheDocument()
    expect(adapter.getCommissionOwners).toHaveBeenCalledTimes(2)
  })
})
