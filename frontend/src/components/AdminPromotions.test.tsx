import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import { AdminPromotions } from './AdminPromotions'
import { I18nProvider } from '../i18n/I18nContext'
import { promotionAdapter, type AdminPromotion } from '../adapters/promotionAdapter'
import { settle } from '../test/utils'

vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: {
    listPromotions: vi.fn(),
    searchHotels: vi.fn(),
    createPromotion: vi.fn(),
    pausePromotion: vi.fn(),
    resumePromotion: vi.fn(),
    markPromotionPaid: vi.fn(),
    cancelPromotion: vi.fn(),
    getPromotionStats: vi.fn(),
  },
}))

const adapter = vi.mocked(promotionAdapter)

function promo(id: number, extra: Partial<AdminPromotion> = {}): AdminPromotion {
  return {
    id,
    property: { id: id * 10, name: `Hotel ${id}`, city: 'Samarkand', status: 'active' },
    start_date: '2026-10-10',
    end_date: '2026-10-16',
    priority: 10,
    country_ref: null,
    region_ref: null,
    city_ref: null,
    price_amount: '2500000.00',
    price_currency: 'UZS',
    note: '',
    paid: true,
    paid_at: '2026-10-09T10:00:00Z',
    status: 'active',
    cancelled_reason: '',
    is_shown_now: true,
    blocked_reason: null,
    total_impressions: 400,
    total_clicks: 12,
    created_at: '2026-10-09T09:00:00Z',
    ...extra,
  }
}

function list(results: AdminPromotion[], count = results.length) {
  return { data: { count, next: null, previous: null, results }, error: null, code: null }
}

function renderScreen(isSuperAdmin = true) {
  render(
    <I18nProvider>
      <AdminPromotions isSuperAdmin={isSuperAdmin} />
    </I18nProvider>,
  )
}

describe('AdminPromotions', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    adapter.listPromotions.mockResolvedValue(list([promo(1)]))
  })

  describe('list', () => {
    it('shows the promotions with status, payment, visibility and numbers', async () => {
      adapter.listPromotions.mockResolvedValue(list([
        promo(1),
        promo(2, { paid: false, paid_at: null, status: 'scheduled', is_shown_now: false }),
        promo(3, { blocked_reason: 'hotel_not_active', is_shown_now: false }),
      ]))
      renderScreen()
      const rows = await screen.findAllByRole('row')
      expect(within(rows[1]).getByText('Hotel 1')).toBeInTheDocument()
      expect(within(rows[1]).getByText('Active')).toBeInTheDocument()
      expect(within(rows[1]).getByText('Paid')).toBeInTheDocument()
      expect(within(rows[1]).getByText('Shown now')).toBeInTheDocument()
      expect(within(rows[1]).getByText('400')).toBeInTheDocument()
      expect(within(rows[1]).getByText('12')).toBeInTheDocument()
      expect(within(rows[2]).getByText('Not paid')).toBeInTheDocument()
      expect(within(rows[2]).getByText('Scheduled')).toBeInTheDocument()
      expect(within(rows[3]).getByText('Hotel is not active')).toBeInTheDocument()
    })

    it('shows a loading state, then an empty state', async () => {
      adapter.listPromotions.mockResolvedValue(list([]))
      renderScreen()
      expect(screen.getByText('Loading promotions...')).toBeInTheDocument()
      expect(await screen.findByText('No promotions yet.')).toBeInTheDocument()
    })

    it('shows an error with a retry button', async () => {
      adapter.listPromotions.mockResolvedValueOnce({ data: null, error: 'boom', code: null })
      renderScreen()
      expect(await screen.findByRole('alert')).toHaveTextContent('Could not load promotions.')
      adapter.listPromotions.mockResolvedValue(list([promo(1)]))
      fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
      expect(await screen.findByText('Hotel 1')).toBeInTheDocument()
    })

    it('filters by status and payment', async () => {
      renderScreen()
      await screen.findByText('Hotel 1')
      fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'paused' } })
      await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ status: 'paused', page: 1 })))
      fireEvent.change(screen.getByLabelText('Payment'), { target: { value: 'false' } })
      await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ paid: 'false', status: 'paused' })))
      await settle()
    })

    it('filters by hotel name after a short pause in typing', async () => {
      renderScreen()
      await screen.findByText('Hotel 1')
      fireEvent.change(screen.getByLabelText('Hotel name'), { target: { value: 'regis' } })
      await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'regis' })))
      await settle()
    })

    it('goes to the next page', async () => {
      adapter.listPromotions.mockResolvedValue({ data: { count: 45, next: 'x', previous: null, results: [promo(1)] }, error: null, code: null })
      renderScreen()
      await screen.findByText('Hotel 1')
      fireEvent.click(screen.getByRole('button', { name: 'Next page' }))
      await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ page: 2 })))
      await settle()
    })
  })

  describe('permissions', () => {
    it('a super-admin sees the actions and the hotel finder', async () => {
      renderScreen(true)
      await screen.findByText('Hotel 1')
      expect(screen.getByRole('button', { name: 'Pause' })).toBeInTheDocument()
      expect(screen.getByLabelText('Find a hotel by name')).toBeInTheDocument()
      expect(screen.queryByText(/Only a super-admin can change them/)).toBeNull()
    })

    it('staff can only look: no actions, no finder, with a note', async () => {
      renderScreen(false)
      await screen.findByText('Hotel 1')
      expect(screen.queryByRole('button', { name: 'Pause' })).toBeNull()
      expect(screen.queryByRole('button', { name: 'Mark as paid' })).toBeNull()
      expect(screen.queryByRole('button', { name: 'Cancel promotion' })).toBeNull()
      expect(screen.queryByLabelText('Find a hotel by name')).toBeNull()
      expect(screen.getByText(/Only a super-admin can change them/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: 'Statistics' })).toBeInTheDocument()
    })
  })

  describe('row actions', () => {
    it('only offers the actions that fit the state', async () => {
      adapter.listPromotions.mockResolvedValue(list([
        promo(1, { status: 'paused', is_shown_now: false }),
        promo(2, { status: 'ended', is_shown_now: false }),
        promo(3, { paid: false, paid_at: null, status: 'scheduled', is_shown_now: false }),
      ]))
      renderScreen()
      const rows = await screen.findAllByRole('row')
      expect(within(rows[1]).getByRole('button', { name: 'Resume' })).toBeInTheDocument()
      expect(within(rows[1]).queryByRole('button', { name: 'Pause' })).toBeNull()
      expect(within(rows[2]).queryByRole('button', { name: 'Pause' })).toBeNull()
      expect(within(rows[2]).queryByRole('button', { name: 'Cancel promotion' })).toBeNull()
      expect(within(rows[2]).getByRole('button', { name: 'Statistics' })).toBeInTheDocument()
      expect(within(rows[3]).getByRole('button', { name: 'Mark as paid' })).toBeInTheDocument()
      expect(within(rows[1]).queryByRole('button', { name: 'Mark as paid' })).toBeNull()
    })

    it('marks a promotion as paid and reloads the list', async () => {
      adapter.listPromotions.mockResolvedValueOnce(list([promo(1, { paid: false, paid_at: null, status: 'scheduled', is_shown_now: false })]))
      adapter.markPromotionPaid.mockResolvedValue({ data: promo(1), error: null, code: null })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Mark as paid' }))
      await waitFor(() => expect(adapter.markPromotionPaid).toHaveBeenCalledWith(1))
      await waitFor(() => expect(adapter.listPromotions).toHaveBeenCalledTimes(2))
      await settle()
    })

    it('pauses and resumes', async () => {
      adapter.pausePromotion.mockResolvedValue({ data: promo(1), error: null, code: null })
      adapter.resumePromotion.mockResolvedValue({ data: promo(1), error: null, code: null })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Pause' }))
      await waitFor(() => expect(adapter.pausePromotion).toHaveBeenCalledWith(1))
      await settle()
    })

    it('shows a translated message when an action fails', async () => {
      adapter.listPromotions.mockResolvedValue(list([promo(1, { paid: false, paid_at: null, status: 'scheduled', is_shown_now: false })]))
      adapter.markPromotionPaid.mockResolvedValue({ data: null, error: 'x', code: 'already_paid' })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Mark as paid' }))
      expect(await screen.findByRole('alert')).toHaveTextContent('The payment is already recorded.')
    })

    it('disables the buttons of a row while its action runs', async () => {
      let finish: (value: Awaited<ReturnType<typeof promotionAdapter.pausePromotion>>) => void = () => {}
      adapter.pausePromotion.mockReturnValue(new Promise(resolve => { finish = resolve }))
      renderScreen()
      const pause = await screen.findByRole('button', { name: 'Pause' })
      fireEvent.click(pause)
      await waitFor(() => expect(pause).toBeDisabled())
      finish({ data: promo(1), error: null, code: null })
      await settle()
    })
  })

  describe('cancel', () => {
    it('needs a reason, then cancels and reloads', async () => {
      adapter.cancelPromotion.mockResolvedValue({ data: promo(1, { status: 'cancelled' }), error: null, code: null })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Cancel promotion' }))
      const dialog = await screen.findByRole('dialog')
      const confirm = within(dialog).getByRole('button', { name: 'Cancel promotion' })
      expect(confirm).toBeDisabled()
      fireEvent.change(within(dialog).getByLabelText('Reason (required)'), { target: { value: 'Client withdrew' } })
      expect(confirm).toBeEnabled()
      fireEvent.click(confirm)
      await waitFor(() => expect(adapter.cancelPromotion).toHaveBeenCalledWith(1, 'Client withdrew'))
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
      await settle()
    })

    it('Keep it closes the dialog without calling the backend', async () => {
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Cancel promotion' }))
      fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Keep it' }))
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(adapter.cancelPromotion).not.toHaveBeenCalled()
    })

    it('shows the backend error inside the dialog and keeps it open', async () => {
      adapter.cancelPromotion.mockResolvedValue({ data: null, error: 'x', code: 'bad_status' })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Cancel promotion' }))
      const dialog = await screen.findByRole('dialog')
      fireEvent.change(within(dialog).getByLabelText('Reason (required)'), { target: { value: 'because' } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Cancel promotion' }))
      expect(await within(dialog).findByRole('alert')).toHaveTextContent('This cannot be done in the current state.')
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  describe('statistics', () => {
    it('shows the daily numbers, the totals and the click rate', async () => {
      adapter.getPromotionStats.mockResolvedValue({
        data: {
          days: [{ date: '2026-10-09', impressions: 200, clicks: 10, ctr: 5 }, { date: '2026-10-10', impressions: 100, clicks: 0, ctr: 0 }],
          totals: { impressions: 300, clicks: 10, ctr: 3.33 },
        },
        error: null,
        code: null,
      })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Statistics' }))
      const dialog = await screen.findByRole('dialog')
      expect(await within(dialog).findByText('Statistics: Hotel 1')).toBeInTheDocument()
      expect(adapter.getPromotionStats).toHaveBeenCalledWith(1)
      const rows = within(dialog).getAllByRole('row')
      expect(rows).toHaveLength(4)
      expect(within(rows[1]).getByText('200')).toBeInTheDocument()
      expect(within(rows[1]).getByText('5%')).toBeInTheDocument()
      expect(within(rows[3]).getByText('300')).toBeInTheDocument()
      expect(within(rows[3]).getByText('3.33%')).toBeInTheDocument()
    })

    it('shows an empty message when there are no views and a dash for the rate', async () => {
      adapter.getPromotionStats.mockResolvedValue({
        data: { days: [], totals: { impressions: 0, clicks: 0, ctr: null } }, error: null, code: null,
      })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Statistics' }))
      expect(await screen.findByText('No views yet.')).toBeInTheDocument()
    })

    it('shows an error and closes with the Close button', async () => {
      adapter.getPromotionStats.mockResolvedValue({ data: null, error: 'x', code: null })
      renderScreen()
      fireEvent.click(await screen.findByRole('button', { name: 'Statistics' }))
      const dialog = await screen.findByRole('dialog')
      expect(await within(dialog).findByRole('alert')).toBeInTheDocument()
      fireEvent.click(within(dialog).getByRole('button', { name: 'Close' }))
      expect(screen.queryByRole('dialog')).toBeNull()
    })
  })

  describe('hotel finder and create form', () => {
    const hotels = [
      { id: 7, name: 'Registan Plaza', city: 'Samarkand', status: 'active', has_running_promotion: false },
      { id: 8, name: 'Registan Inn', city: 'Samarkand', status: 'suspended', has_running_promotion: false },
      { id: 9, name: 'Registan Star', city: 'Samarkand', status: 'active', has_running_promotion: true },
    ]

    async function find(text = 'regis') {
      renderScreen()
      await screen.findByText('Hotel 1')
      fireEvent.change(screen.getByLabelText('Find a hotel by name'), { target: { value: text } })
    }

    it('does not search for fewer than 2 letters', async () => {
      await find('r')
      await new Promise(resolve => setTimeout(resolve, 400))
      expect(adapter.searchHotels).not.toHaveBeenCalled()
    })

    it('lists matching hotels with a Promote button', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      await find()
      expect(await screen.findByText('Registan Plaza')).toBeInTheDocument()
      expect(adapter.searchHotels).toHaveBeenCalledWith('regis')
      expect(screen.getByRole('button', { name: 'Promote Registan Plaza' })).toBeEnabled()
    })

    it('disables the button of a hotel that already has a promotion', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      await find()
      await screen.findByText('Registan Star')
      expect(screen.getByRole('button', { name: 'Promote Registan Star' })).toBeDisabled()
      expect(screen.getByText('Already has a promotion')).toBeInTheDocument()
    })

    it('says so when no hotel matches', async () => {
      adapter.searchHotels.mockResolvedValue({ data: [], error: null, code: null })
      await find('zzz')
      expect(await screen.findByText('No hotels found')).toBeInTheDocument()
    })

    it('warns when the chosen hotel is not active', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      await find()
      fireEvent.click(await screen.findByRole('button', { name: 'Promote Registan Inn' }))
      const dialog = await screen.findByRole('dialog')
      expect(within(dialog).getByText(/this hotel is not active/i)).toBeInTheDocument()
    })

    it('creates a promotion with the typed values, then closes and reloads', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      adapter.createPromotion.mockResolvedValue({ data: promo(5), error: null, code: null })
      await find()
      fireEvent.click(await screen.findByRole('button', { name: 'Promote Registan Plaza' }))
      const dialog = await screen.findByRole('dialog')
      fireEvent.change(within(dialog).getByLabelText('Start date'), { target: { value: '2026-10-10' } })
      fireEvent.change(within(dialog).getByLabelText('End date'), { target: { value: '2026-10-16' } })
      fireEvent.change(within(dialog).getByLabelText('Priority (0-100)'), { target: { value: '40' } })
      fireEvent.change(within(dialog).getByLabelText('Agreed price'), { target: { value: '2500000' } })
      fireEvent.change(within(dialog).getByLabelText('Internal note'), { target: { value: 'Invoice 7' } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Create promotion' }))
      await waitFor(() => expect(adapter.createPromotion).toHaveBeenCalledWith({
        property: 7, start_date: '2026-10-10', end_date: '2026-10-16', priority: 40,
        price_amount: '2500000', price_currency: 'UZS', note: 'Invoice 7',
      }))
      await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
      await waitFor(() => expect(adapter.listPromotions).toHaveBeenCalledTimes(2))
      await settle()
    })

    it('sends no price when the price box is empty', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      adapter.createPromotion.mockResolvedValue({ data: promo(5), error: null, code: null })
      await find()
      fireEvent.click(await screen.findByRole('button', { name: 'Promote Registan Plaza' }))
      const dialog = await screen.findByRole('dialog')
      fireEvent.change(within(dialog).getByLabelText('Start date'), { target: { value: '2026-10-10' } })
      fireEvent.change(within(dialog).getByLabelText('End date'), { target: { value: '2026-10-16' } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Create promotion' }))
      await waitFor(() => expect(adapter.createPromotion).toHaveBeenCalledWith(expect.objectContaining({ price_amount: null, priority: 0 })))
      await settle()
    })

    it('does not submit without both dates', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      await find()
      fireEvent.click(await screen.findByRole('button', { name: 'Promote Registan Plaza' }))
      const dialog = await screen.findByRole('dialog')
      expect(within(dialog).getByRole('button', { name: 'Create promotion' })).toBeDisabled()
    })

    it('shows the translated backend error and keeps the form open', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      adapter.createPromotion.mockResolvedValue({ data: null, error: 'x', code: 'overlap' })
      await find()
      fireEvent.click(await screen.findByRole('button', { name: 'Promote Registan Plaza' }))
      const dialog = await screen.findByRole('dialog')
      fireEvent.change(within(dialog).getByLabelText('Start date'), { target: { value: '2026-10-10' } })
      fireEvent.change(within(dialog).getByLabelText('End date'), { target: { value: '2026-10-16' } })
      fireEvent.click(within(dialog).getByRole('button', { name: 'Create promotion' }))
      expect(await within(dialog).findByRole('alert')).toHaveTextContent('This hotel already has a promotion in these dates.')
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    it('Cancel closes the form without creating anything', async () => {
      adapter.searchHotels.mockResolvedValue({ data: hotels, error: null, code: null })
      await find()
      fireEvent.click(await screen.findByRole('button', { name: 'Promote Registan Plaza' }))
      fireEvent.click(within(await screen.findByRole('dialog')).getByRole('button', { name: 'Cancel' }))
      expect(screen.queryByRole('dialog')).toBeNull()
      expect(adapter.createPromotion).not.toHaveBeenCalled()
    })
  })
})
