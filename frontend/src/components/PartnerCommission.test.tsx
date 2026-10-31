import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { PartnerCommission } from './PartnerCommission'
import { I18nProvider } from '../i18n/I18nContext'
import { partnerAdapter } from '../adapters/partnerAdapter'
import type { CommissionStatement } from '../adapters/commissionTypes'

vi.mock('../adapters/partnerAdapter', () => ({ partnerAdapter: { getCommission: vi.fn() } }))

const getCommission = vi.mocked(partnerAdapter.getCommission)

const STATEMENT: CommissionStatement = {
  percent: '2.50',
  percent_since: '2026-03-01',
  months: [
    { month: '2026-05', bookings: 0, gross: [], percent: '2.50', commission: [], paid: null },
    {
      month: '2026-04', bookings: 3, gross: [{ currency: 'USD', amount: '1000.00' }, { currency: 'UZS', amount: '4000000.00' }],
      percent: '2.50', commission: [{ currency: 'USD', amount: '25.00' }, { currency: 'UZS', amount: '100000.00' }],
      paid: { by: 'Kola Admin', role: 'staff', at: '2026-05-03T09:00:00Z', amounts: [{ currency: 'USD', amount: '25.00' }] },
    },
    { month: '2026-02', bookings: 1, gross: [{ currency: 'USD', amount: '80.00' }], percent: null, commission: null, paid: null },
  ],
  years: null,
}

function show() {
  localStorage.setItem('tickbron.language', 'en')
  render(<I18nProvider><PartnerCommission /></I18nProvider>)
}

describe('PartnerCommission', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getCommission.mockResolvedValue({ data: STATEMENT, error: null })
  })

  it('shows the percent and each month with its figures per currency', async () => {
    show()
    expect(await screen.findByText(/Commission percent: 2.50%/)).toBeInTheDocument()
    const april = screen.getByRole('row', { name: /April 2026/ })
    expect(within(april).getByText('3')).toBeInTheDocument()
    expect(within(april).getAllByText(/\$/).length).toBeGreaterThan(0)
  })

  it('shows who confirmed a paid month, by name and role', async () => {
    show()
    expect(await screen.findByText('Confirmed by Kola Admin (Admin)')).toBeInTheDocument()
    expect(screen.getByText('Paid')).toBeInTheDocument()
  })

  it('says "Not set" for a month that had no percent', async () => {
    show()
    const february = within(await screen.findByRole('row', { name: /February 2026/ }))
    expect(february.getAllByText('Not set')).toHaveLength(2)
  })

  it('never offers the owner a way to confirm or take back a payment', async () => {
    show()
    await screen.findByText(/Commission percent/)
    expect(screen.queryByRole('button', { name: /Mark as paid|Take back/ })).not.toBeInTheDocument()
  })

  it('shows no year totals for a young account and shows them for an old one', async () => {
    show()
    await screen.findByText(/Commission percent/)
    expect(screen.queryByText('Year totals')).not.toBeInTheDocument()
  })

  it('shows the year totals when the account is a year old', async () => {
    getCommission.mockResolvedValue({
      data: { ...STATEMENT, years: [{ year: 2025, bookings: 9, gross: [{ currency: 'USD', amount: '900.00' }], commission: [{ currency: 'USD', amount: '22.50' }] }] },
      error: null,
    })
    show()
    const heading = await screen.findByText('Year totals')
    expect(heading).toBeInTheDocument()
    expect(screen.getByRole('row', { name: /2025/ })).toBeInTheDocument()
  })

  it('explains that no commission is counted while no percent is set', async () => {
    getCommission.mockResolvedValue({ data: { ...STATEMENT, percent: null, percent_since: null }, error: null })
    show()
    expect(await screen.findByText(/No commission percent has been set/)).toBeInTheDocument()
  })

  it('shows a loading state, then an error with Try Again that loads again', async () => {
    getCommission.mockResolvedValueOnce({ data: null, error: 'down' })
    show()
    expect(screen.getByRole('status')).toHaveTextContent('Loading')
    expect(await screen.findByRole('alert')).toHaveTextContent('down')
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByText(/Commission percent: 2.50%/)).toBeInTheDocument()
    expect(getCommission).toHaveBeenCalledTimes(2)
  })
})
