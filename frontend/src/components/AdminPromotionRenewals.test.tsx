import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { AdminPromotionRenewals } from './AdminPromotionRenewals'
import { I18nProvider } from '../i18n/I18nContext'
import { promotionAdapter, type AdRenewalRow } from '../adapters/promotionAdapter'
import { settle } from '../test/utils'

vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { listRenewals: vi.fn(), confirmRenewal: vi.fn(), declineRenewal: vi.fn() },
}))

const adapter = vi.mocked(promotionAdapter)

function renewal(id: number, extra: Partial<AdRenewalRow> = {}): AdRenewalRow {
  return {
    id, promotion_id: id * 10, property_id: id * 100, hotel_name: `Hotel ${id}`, city: 'Samarkand',
    address: '1 Main Street', latitude: '39.654', longitude: '66.975', owner_name: 'Olim Egasi',
    owner_phone: '+998901112233', owner_email: 'olim@example.com', start_date: '2026-11-01',
    end_date: '2026-11-30', price_amount: '2500000.00', price_currency: 'UZS', ends_on: '2026-11-30',
    deadline: '2026-12-05', days_left: 3, status: 'pending', decided_via: '', decided_at: null, ...extra,
  }
}

const page = (...rows: AdRenewalRow[]) => ({ count: rows.length, next: null, previous: null, results: rows })

function show(isSuperAdmin = true, onChanged = vi.fn()) {
  localStorage.setItem('tickbron.language', 'en')
  render(<I18nProvider><AdminPromotionRenewals isSuperAdmin={isSuperAdmin} onChanged={onChanged} /></I18nProvider>)
  return onChanged
}

describe('AdminPromotionRenewals', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    adapter.listRenewals.mockResolvedValue({ data: page(renewal(1)), error: null, code: null })
    adapter.confirmRenewal.mockResolvedValue({ data: renewal(1, { status: 'renewed' }), error: null, code: null })
    adapter.declineRenewal.mockResolvedValue({ data: renewal(1, { status: 'declined' }), error: null, code: null })
  })

  it('lists the ads waiting for the answer with the owner contact, the deadline and a map link', async () => {
    show()
    expect(await screen.findByText('Hotel 1')).toBeInTheDocument()
    expect(adapter.listRenewals).toHaveBeenCalledWith({ status: 'pending', page: 1 })
    expect(screen.getByText('olim@example.com')).toBeInTheDocument()
    expect(screen.getByText('Days left: 3')).toBeInTheDocument()
    const map = screen.getByRole('link', { name: /Open on map/ })
    expect(map).toHaveAttribute('href', expect.stringContaining('mlat=39.654&mlon=66.975'))
    expect(map).toHaveAttribute('rel', expect.stringContaining('noopener'))
  })

  it('has an empty state', async () => {
    adapter.listRenewals.mockResolvedValue({ data: page(), error: null, code: null })
    show()
    expect(await screen.findByText('Nothing here.')).toBeInTheDocument()
  })

  it('shows a failed load with a Try again button', async () => {
    adapter.listRenewals.mockResolvedValueOnce({ data: null, error: 'down', code: null })
    show()
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load the renewals.')
    adapter.listRenewals.mockResolvedValue({ data: page(renewal(1)), error: null, code: null })
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByText('Hotel 1')).toBeInTheDocument()
  })

  it('confirms the payment, reloads the list and tells the page', async () => {
    const onChanged = show()
    fireEvent.click(await screen.findByRole('button', { name: /Paid, extend one month/ }))
    await waitFor(() => expect(adapter.confirmRenewal).toHaveBeenCalledWith(1))
    await waitFor(() => expect(adapter.listRenewals).toHaveBeenCalledTimes(2))
    expect(onChanged).toHaveBeenCalled()
  })

  it('asks before removing an ad and does nothing on No', async () => {
    show()
    fireEvent.click(await screen.findByRole('button', { name: /Remove ad now/ }))
    expect(screen.getByText('Remove this ad from the banner now?')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'No' }))
    expect(adapter.declineRenewal).not.toHaveBeenCalled()
    expect(screen.queryByText('Remove this ad from the banner now?')).not.toBeInTheDocument()
  })

  it('removes the ad after Yes', async () => {
    const onChanged = show()
    fireEvent.click(await screen.findByRole('button', { name: /Remove ad now/ }))
    fireEvent.click(screen.getByRole('button', { name: 'Yes, remove' }))
    await waitFor(() => expect(adapter.declineRenewal).toHaveBeenCalledWith(1))
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
  })

  it('shows why an answer was refused, in the page language', async () => {
    adapter.confirmRenewal.mockResolvedValue({ data: null, error: 'x', code: 'already_decided' })
    show()
    fireEvent.click(await screen.findByRole('button', { name: /Paid, extend one month/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('This question has already been answered.')
  })

  it('lets the staff look but not answer', async () => {
    show(false)
    expect(await screen.findByText('Hotel 1')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Paid, extend one month/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Remove ad now/ })).not.toBeInTheDocument()
  })

  it('shows the history of another status without buttons and says how it was answered', async () => {
    adapter.listRenewals.mockResolvedValueOnce({ data: page(renewal(1)), error: null, code: null })
    adapter.listRenewals.mockResolvedValue({
      data: page(renewal(2, { status: 'expired', decided_via: 'auto', days_left: -2 })), error: null, code: null,
    })
    show()
    await screen.findByText('Hotel 1')
    fireEvent.change(screen.getByLabelText('Show'), { target: { value: 'expired' } })
    expect(await screen.findByText('Hotel 2')).toBeInTheDocument()
    expect(adapter.listRenewals).toHaveBeenLastCalledWith({ status: 'expired', page: 1 })
    expect(screen.getByText('No answer in time')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Paid, extend one month/ })).not.toBeInTheDocument()
    await settle()
  })
})
