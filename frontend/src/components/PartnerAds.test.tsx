import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerAds } from './PartnerAds'
import { I18nProvider } from '../i18n/I18nContext'
import { partnerAdapter, type OwnerPromotion } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({ partnerAdapter: { getPromotions: vi.fn() } }))

const adapter = vi.mocked(partnerAdapter)

function ad(id: number, extra: Partial<OwnerPromotion> = {}): OwnerPromotion {
  return {
    id, property: { id: id * 10, name: `Hotel ${id}` }, start_date: '2026-11-01', end_date: '2026-11-30',
    status: 'active', paid: true, is_shown_now: true, blocked_reason: null, impressions: 400, clicks: 12,
    click_rate: '3.0', renewal: null, ...extra,
  }
}

const page = (results: OwnerPromotion[], hasMore = false) => ({ data: { count: results.length, hasMore, results }, error: null })

function show() {
  localStorage.setItem('tickbron.language', 'en')
  render(<I18nProvider><PartnerAds /></I18nProvider>)
}

describe('PartnerAds', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    adapter.getPromotions.mockResolvedValue(page([ad(1)]))
  })

  it('shows an ad with its hotel, period, views, clicks and click rate', async () => {
    show()
    expect(await screen.findByText('Hotel 1')).toBeInTheDocument()
    expect(adapter.getPromotions).toHaveBeenCalledWith({ status: undefined, page: 1 })
    expect(screen.getByText('Shown on the site now')).toBeInTheDocument()
    expect(screen.getByText('400')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('3.0%')).toBeInTheDocument()
  })

  it('shows a dash for the click rate before the first view', async () => {
    adapter.getPromotions.mockResolvedValue(page([ad(1, { impressions: 0, clicks: 0, click_rate: null })]))
    show()
    await screen.findByText('Hotel 1')
    expect(screen.getByText('-')).toBeInTheDocument()
  })

  it('says why an ad is not shown', async () => {
    adapter.getPromotions.mockResolvedValue(page([
      ad(1, { is_shown_now: false, blocked_reason: 'hotel_not_active' }),
      ad(2, { is_shown_now: false, paid: false, status: 'scheduled' }),
      ad(3, { is_shown_now: false, status: 'paused' }),
    ]))
    show()
    expect(await screen.findByText('Not shown: your hotel is not published')).toBeInTheDocument()
    expect(screen.getByText('Not shown yet: waiting for the payment to be confirmed')).toBeInTheDocument()
    expect(screen.getByText('Paused', { selector: '.status-badge' })).toBeInTheDocument()
  })

  it('tells the owner an ad stays visible while the payment for the next month is awaited', async () => {
    adapter.getPromotions.mockResolvedValue(page([
      ad(1, { renewal: { ends_on: '2026-11-30', deadline: '2026-12-05', days_left: 3 } }),
    ]))
    show()
    expect(await screen.findByText(/Waiting for the payment for the next month/)).toHaveTextContent('Days left: 3')
  })

  it('never shows a price', async () => {
    show()
    await screen.findByText('Hotel 1')
    expect(screen.queryByText(/UZS|so'm|price/i)).not.toBeInTheDocument()
  })

  it('has an empty state that points to the chat', async () => {
    adapter.getPromotions.mockResolvedValue(page([]))
    show()
    expect(await screen.findByText(/You have no ads yet/)).toBeInTheDocument()
  })

  it('shows a failed load with a Try Again button', async () => {
    adapter.getPromotions.mockResolvedValueOnce({ data: null, error: 'down' })
    show()
    expect(await screen.findByRole('alert')).toHaveTextContent('down')
    adapter.getPromotions.mockResolvedValue(page([ad(1)]))
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByText('Hotel 1')).toBeInTheDocument()
  })

  it('loads the next page with Show more and hides the button at the end', async () => {
    adapter.getPromotions.mockResolvedValueOnce(page([ad(1)], true)).mockResolvedValueOnce(page([ad(2)], false))
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Show more' }))
    expect(await screen.findByText('Hotel 2')).toBeInTheDocument()
    expect(adapter.getPromotions).toHaveBeenLastCalledWith({ status: undefined, page: 2 })
    expect(screen.getByText('Hotel 1')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Show more' })).not.toBeInTheDocument()
  })

  it('filters by status from the first page', async () => {
    show()
    await screen.findByText('Hotel 1')
    fireEvent.change(screen.getByLabelText('Show'), { target: { value: 'ended' } })
    await waitFor(() => expect(adapter.getPromotions).toHaveBeenLastCalledWith({ status: 'ended', page: 1 }))
  })
})
