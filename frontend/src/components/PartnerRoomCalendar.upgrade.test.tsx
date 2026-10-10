/**
 * Calendar upgrade: data per visible month, a month summary, one-click close/open,
 * and the price of a rate plan shown in the day cells and changed for a range.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerRoomCalendar } from './PartnerRoomCalendar'
import { partnerAdapter, type PartnerRatePlan, type PartnerRoomInventory } from '../adapters/partnerAdapter'
import { I18nProvider } from '../i18n/I18nContext'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    getRoomInventory: vi.fn(),
    getBlocks: vi.fn(),
    getRatePlans: vi.fn(),
    getDateInventory: vi.fn(),
    createRoomInventory: vi.fn(),
    updateRoomInventory: vi.fn(),
    bulkSetRoomInventory: vi.fn(),
    bulkSetPrice: vi.fn(),
    createBlock: vi.fn(),
    deleteBlock: vi.fn(),
  },
}))

const adapter = vi.mocked(partnerAdapter)
const MONTH = '2030-03'
const day = (n: number) => `2030-03-${String(n).padStart(2, '0')}`
const cell = (container: HTMLElement, date: string) => container.querySelector(`[data-date="${date}"]`) as HTMLElement

function row(id: number, date: string, extra: Partial<PartnerRoomInventory> = {}): PartnerRoomInventory {
  return { id, room_type: 7, date, available_rooms: 5, booked_rooms: 0, remaining_rooms: 5, is_available: true, ...extra } as PartnerRoomInventory
}

function plan(id: number, name: string, extra: Partial<PartnerRatePlan> = {}): PartnerRatePlan {
  return { id, room_type: 7, name, base_price: 400000, currency: 'UZS', is_active: true, ...extra } as PartnerRatePlan
}

function renderCalendar() {
  return render(
    <I18nProvider>
      <PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />
    </I18nProvider>,
  )
}

const ok = <T,>(data: T) => ({ data, error: null })

describe('PartnerRoomCalendar upgrade', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    adapter.getRoomInventory.mockResolvedValue(ok([row(1, day(10), { remaining_rooms: 3, booked_rooms: 2 })]))
    adapter.getBlocks.mockResolvedValue(ok([]))
    adapter.getRatePlans.mockResolvedValue(ok([]))
    adapter.getDateInventory.mockResolvedValue(ok([]))
  })

  describe('data follows the visible month', () => {
    it('loads the inventory of the shown month, and of the next month after moving', async () => {
      renderCalendar()
      await screen.findByText('3 / 5')
      expect(adapter.getRoomInventory).toHaveBeenCalledWith({ room_type: 7, date_from: '2030-03-01', date_to: '2030-03-31' })
      fireEvent.click(screen.getByRole('button', { name: 'Next month' }))
      await waitFor(() => expect(adapter.getRoomInventory).toHaveBeenLastCalledWith({ room_type: 7, date_from: '2030-04-01', date_to: '2030-04-30' }))
    })

    it('keeps the grid and the selection while another month loads', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      fireEvent.click(cell(container, day(20)))
      adapter.getRoomInventory.mockReturnValue(new Promise(() => {}))
      fireEvent.click(screen.getByRole('button', { name: 'Next month' }))
      expect(screen.getByRole('heading', { name: 'April 2030' })).toBeInTheDocument()
      expect(screen.getByRole('region', { name: 'Edit day' })).toBeInTheDocument()
    })

    it('shows an error when a month cannot be loaded and still shows the grid', async () => {
      adapter.getRoomInventory.mockResolvedValue({ data: null, error: 'Server error' })
      renderCalendar()
      expect(await screen.findByRole('alert')).toHaveTextContent('Server error')
      expect(screen.getByRole('heading', { name: 'March 2030' })).toBeInTheDocument()
    })
  })

  describe('month summary', () => {
    it('counts free room-nights of the shown month against its capacity', async () => {
      renderCalendar()
      // 31 days x 5 rooms = 155 room-nights; 2 rooms of 10 March are booked
      expect(await screen.findByText('153 of 155 room-nights free this month')).toBeInTheDocument()
    })

    it('counts a closed day as no free rooms and mentions how many days are closed', async () => {
      adapter.getRoomInventory.mockResolvedValue(ok([
        row(1, day(10), { is_available: false }), row(2, day(11), { is_available: false }), row(3, day(12), { remaining_rooms: 0, booked_rooms: 5 }),
      ]))
      renderCalendar()
      expect(await screen.findByText('140 of 155 room-nights free this month')).toBeInTheDocument()
      expect(screen.getByText('2 closed days')).toBeInTheDocument()
    })

    it('uses the singular for one closed day and says nothing when none are closed', async () => {
      adapter.getRoomInventory.mockResolvedValue(ok([row(1, day(10), { is_available: false })]))
      renderCalendar()
      expect(await screen.findByText('1 closed day')).toBeInTheDocument()
    })

    it('does not mention closed days when there are none', async () => {
      renderCalendar()
      await screen.findByText('153 of 155 room-nights free this month')
      expect(screen.queryByText(/closed day/)).toBeNull()
    })
  })

  describe('close and open in one click', () => {
    it('closes a single day that has no row by creating it closed at full capacity', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.createRoomInventory.mockResolvedValue(ok(row(2, day(20), { is_available: false })))
      fireEvent.click(cell(container, day(20)))
      fireEvent.click(screen.getByRole('button', { name: 'Close these days' }))
      await waitFor(() => expect(adapter.createRoomInventory).toHaveBeenCalledWith({
        room_type: 7, date: day(20), available_rooms: 5, is_available: false,
      }))
    })

    it('closes a single day that has a row without touching its room count', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.updateRoomInventory.mockResolvedValue(ok(row(1, day(10), { is_available: false })))
      fireEvent.click(cell(container, day(10)))
      fireEvent.click(screen.getByRole('button', { name: 'Close these days' }))
      await waitFor(() => expect(adapter.updateRoomInventory).toHaveBeenCalledWith(1, { is_available: false }))
    })

    it('closes and opens a range with the bulk call, leaving the room count alone', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.bulkSetRoomInventory.mockResolvedValue(ok([]))
      fireEvent.click(cell(container, day(20)))
      fireEvent.click(cell(container, day(23)))
      fireEvent.click(screen.getByRole('button', { name: 'Close these days' }))
      await waitFor(() => expect(adapter.bulkSetRoomInventory).toHaveBeenCalledWith({
        room_type: 7, date_from: day(20), date_to: day(23), is_available: false,
      }))
      await screen.findByText('Saved Wed, Mar 20 to Fri, Mar 22')
      fireEvent.click(cell(container, day(20)))
      fireEvent.click(cell(container, day(23)))
      fireEvent.click(screen.getByRole('button', { name: 'Open these days' }))
      await waitFor(() => expect(adapter.bulkSetRoomInventory).toHaveBeenLastCalledWith({
        room_type: 7, date_from: day(20), date_to: day(23), is_available: true,
      }))
    })

    it('reloads the month after closing', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.bulkSetRoomInventory.mockResolvedValue(ok([]))
      fireEvent.click(cell(container, day(20)))
      fireEvent.click(cell(container, day(23)))
      fireEvent.click(screen.getByRole('button', { name: 'Close these days' }))
      await waitFor(() => expect(adapter.getRoomInventory).toHaveBeenCalledTimes(2))
    })

    it('shows the backend message when closing fails and keeps the selection', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.bulkSetRoomInventory.mockResolvedValue({ data: null, error: 'Cannot set 2030-03-21 below the 2 room(s) already booked on TICKBRON.' })
      fireEvent.click(cell(container, day(20)))
      fireEvent.click(cell(container, day(23)))
      fireEvent.click(screen.getByRole('button', { name: 'Close these days' }))
      expect(await screen.findByRole('alert')).toHaveTextContent('already booked on TICKBRON')
      expect(screen.getByRole('region', { name: 'Edit day' })).toBeInTheDocument()
    })
  })

  describe('prices of a rate plan', () => {
    beforeEach(() => {
      adapter.getRatePlans.mockResolvedValue(ok([plan(11, 'Standard'), plan(12, 'Non-refundable', { base_price: 350000 }), plan(99, 'Other room', { room_type: 8 })]))
      adapter.getDateInventory.mockResolvedValue(ok([{ id: 1, rate_plan: 11, date: day(10), price: 450000, currency: 'UZS' } as never]))
    })

    it('has no price controls when the room type has no rate plan', async () => {
      adapter.getRatePlans.mockResolvedValue(ok([]))
      renderCalendar()
      await screen.findByText('3 / 5')
      expect(screen.queryByLabelText('Prices for')).toBeNull()
    })

    it('offers only the active rate plans of this room type and starts with the first', async () => {
      adapter.getRatePlans.mockResolvedValue(ok([plan(11, 'Standard'), plan(13, 'Old', { is_active: false }), plan(99, 'Other room', { room_type: 8 })]))
      renderCalendar()
      const select = await screen.findByLabelText('Prices for')
      expect(within(select).getAllByRole('option').map(option => option.textContent)).toEqual(['Standard'])
    })

    it('shows the price of the day under the room count, and the base price where no price was set', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      await waitFor(() => expect(adapter.getDateInventory).toHaveBeenCalledWith({ rate_plan: 11, date_from: '2030-03-01', date_to: '2030-03-31' }))
      await waitFor(() => expect(cell(container, day(10))).toHaveTextContent('450 000'))
      expect(cell(container, day(11))).toHaveTextContent('400 000')
    })

    it('loads the prices of another plan when it is chosen', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.getDateInventory.mockResolvedValue(ok([]))
      fireEvent.change(await screen.findByLabelText('Prices for'), { target: { value: '12' } })
      await waitFor(() => expect(adapter.getDateInventory).toHaveBeenLastCalledWith({ rate_plan: 12, date_from: '2030-03-01', date_to: '2030-03-31' }))
      await waitFor(() => expect(cell(container, day(10))).toHaveTextContent('350 000'))
    })

    it('still shows the calendar when the prices cannot be loaded', async () => {
      adapter.getDateInventory.mockResolvedValue({ data: null, error: 'Prices are unavailable' })
      const { container } = renderCalendar()
      expect(await screen.findByText('Prices are unavailable')).toBeInTheDocument()
      expect(cell(container, day(10))).toHaveTextContent('3 / 5')
    })

    it('sets one price for the chosen range, reloads the prices and confirms', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.bulkSetPrice.mockResolvedValue(ok([]))
      fireEvent.click(cell(container, day(20)))
      fireEvent.click(cell(container, day(23)))
      const save = screen.getByRole('button', { name: 'Set price' })
      expect(save).toBeDisabled()
      fireEvent.change(screen.getByLabelText('Price per night for these days (UZS)'), { target: { value: '520000' } })
      expect(save).toBeEnabled()
      fireEvent.click(save)
      await waitFor(() => expect(adapter.bulkSetPrice).toHaveBeenCalledWith({
        rate_plan: 11, date_from: day(20), date_to: day(23), price: 520000,
      }))
      expect(await screen.findByText('Price updated for Wed, Mar 20 to Fri, Mar 22')).toBeInTheDocument()
      await waitFor(() => expect(adapter.getDateInventory).toHaveBeenCalledTimes(2))
    })

    it('sets the price of a single day', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.bulkSetPrice.mockResolvedValue(ok([]))
      fireEvent.click(cell(container, day(20)))
      fireEvent.change(screen.getByLabelText('Price per night for these days (UZS)'), { target: { value: '500000' } })
      fireEvent.click(screen.getByRole('button', { name: 'Set price' }))
      await waitFor(() => expect(adapter.bulkSetPrice).toHaveBeenCalledWith({
        rate_plan: 11, date_from: day(20), date_to: day(21), price: 500000,
      }))
    })

    it('does not accept an empty, zero-less or negative price', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      fireEvent.click(cell(container, day(20)))
      const input = screen.getByLabelText('Price per night for these days (UZS)')
      const save = screen.getByRole('button', { name: 'Set price' })
      for (const bad of ['', '-5', 'abc']) {
        fireEvent.change(input, { target: { value: bad } })
        expect(save).toBeDisabled()
      }
      fireEvent.change(input, { target: { value: '0' } })
      expect(save).toBeEnabled()
    })

    it('shows the backend message when the price is refused', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.bulkSetPrice.mockResolvedValue({ data: null, error: 'Price must be a whole number of so\'m.' })
      fireEvent.click(cell(container, day(20)))
      fireEvent.change(screen.getByLabelText('Price per night for these days (UZS)'), { target: { value: '500000' } })
      fireEvent.click(screen.getByRole('button', { name: 'Set price' }))
      expect(await screen.findByRole('alert')).toHaveTextContent('whole number')
    })

    it('uses the plan that is chosen when saving', async () => {
      const { container } = renderCalendar()
      await screen.findByText('3 / 5')
      adapter.bulkSetPrice.mockResolvedValue(ok([]))
      fireEvent.change(await screen.findByLabelText('Prices for'), { target: { value: '12' } })
      fireEvent.click(cell(container, day(20)))
      fireEvent.change(screen.getByLabelText('Price per night for these days (USD)'.replace('USD', 'UZS')), { target: { value: '300000' } })
      fireEvent.click(screen.getByRole('button', { name: 'Set price' }))
      await waitFor(() => expect(adapter.bulkSetPrice).toHaveBeenCalledWith(expect.objectContaining({ rate_plan: 12 })))
    })
  })
})
