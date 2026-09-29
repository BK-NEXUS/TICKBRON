/**
 * 3.6: the owner calendar for a room type -- free X of Y per day, editing one day or a
 * date range, and external-booking blocks shown on the calendar and removable.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerRoomCalendar } from './PartnerRoomCalendar'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    getRoomInventory: vi.fn(),
    getBlocks: vi.fn(),
    createRoomInventory: vi.fn(),
    updateRoomInventory: vi.fn(),
    bulkSetRoomInventory: vi.fn(),
    createBlock: vi.fn(),
    deleteBlock: vi.fn(),
  },
}))

// A fixed month keeps the tests independent of today's date
const MONTH = '2030-03'
const day = (n: number) => `2030-03-${String(n).padStart(2, '0')}`
const cell = (container: HTMLElement, date: string) =>
  container.querySelector(`[data-date="${date}"]`) as HTMLElement

describe('PartnerRoomCalendar', () => {
  beforeEach(() => {
    vi.mocked(partnerAdapter.getRoomInventory).mockResolvedValue({
      data: [
        { id: 1, room_type: 7, date: day(10), available_rooms: 5, booked_rooms: 2, remaining_rooms: 3, is_available: true },
      ],
      error: null,
    })
    vi.mocked(partnerAdapter.getBlocks).mockResolvedValue({
      data: [
        { id: 9, room_type: 7, date_from: day(15), date_to: day(17), rooms: 2, note: 'Booking.com', created_by: 3, created_at: '2030-02-01T00:00:00Z' },
      ],
      error: null,
    })
  })

  it('shows the room type name and free/total for a day with inventory', async () => {
    render(<PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />)

    expect(await screen.findByRole('heading', { name: 'Calendar for Deluxe King' })).toBeInTheDocument()
    expect(await screen.findByText('3 / 5')).toBeInTheDocument()
  })

  it('shows a block note on the calendar and lists it below with a Remove button', async () => {
    render(<PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />)

    expect(await screen.findAllByText('Booking.com')).not.toHaveLength(0)
    expect(screen.getByRole('button', { name: /Remove block Booking\.com/ })).toBeInTheDocument()
  })

  it('clicking a day with no inventory row opens the panel defaulted to full capacity, and Save creates a row', async () => {
    const { container } = render(
      <PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />,
    )
    await screen.findByText('3 / 5')
    vi.mocked(partnerAdapter.createRoomInventory).mockResolvedValue({
      data: { id: 2, room_type: 7, date: day(20), available_rooms: 5, booked_rooms: 0, remaining_rooms: 5, is_available: true },
      error: null,
    })

    fireEvent.click(cell(container, day(20)))
    expect(await screen.findByRole('heading', { name: 'Editing Wed, Mar 20' })).toBeInTheDocument()
    expect(screen.getByLabelText(/Available rooms/)).toHaveValue(5)

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(partnerAdapter.createRoomInventory).toHaveBeenCalledWith({
      room_type: 7, date: day(20), available_rooms: 5, is_available: true,
    }))
  })

  it('clicking a day with an existing row pre-fills the panel, and Save updates it', async () => {
    const { container } = render(
      <PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />,
    )
    await screen.findByText('3 / 5')
    vi.mocked(partnerAdapter.updateRoomInventory).mockResolvedValue({
      data: { id: 1, room_type: 7, date: day(10), available_rooms: 4, booked_rooms: 2, remaining_rooms: 2, is_available: true },
      error: null,
    })

    fireEvent.click(cell(container, day(10)))
    expect(screen.getByLabelText(/Available rooms/)).toHaveValue(5)

    fireEvent.change(screen.getByLabelText(/Available rooms/), { target: { value: '4' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(partnerAdapter.updateRoomInventory).toHaveBeenCalledWith(1, {
      available_rooms: 4, is_available: true,
    }))
  })

  it('clicking two days opens the range panel, and Save calls the bulk endpoint', async () => {
    const { container } = render(
      <PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />,
    )
    await screen.findByText('3 / 5')
    vi.mocked(partnerAdapter.bulkSetRoomInventory).mockResolvedValue({ data: [], error: null })

    fireEvent.click(cell(container, day(20)))
    fireEvent.click(cell(container, day(23)))
    expect(await screen.findByRole('heading', { name: 'Editing Wed, Mar 20 to Fri, Mar 22' })).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Save' }))

    await waitFor(() => expect(partnerAdapter.bulkSetRoomInventory).toHaveBeenCalledWith({
      room_type: 7, date_from: day(20), date_to: day(23), available_rooms: 5, is_available: true,
    }))
  })

  it('External booking opens a modal that creates a block', async () => {
    render(<PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />)
    await screen.findByText('3 / 5')
    vi.mocked(partnerAdapter.createBlock).mockResolvedValue({
      data: { id: 10, room_type: 7, date_from: day(1), date_to: day(2), rooms: 1, note: 'phone', created_by: 3, created_at: '2030-03-01T00:00:00Z' },
      error: null,
    })

    fireEvent.click(screen.getByRole('button', { name: 'External booking for Deluxe King' }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('From *'), { target: { value: day(1) } })
    fireEvent.change(screen.getByLabelText('To (exclusive) *'), { target: { value: day(2) } })
    fireEvent.change(screen.getByLabelText('Rooms *'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('Note *'), { target: { value: 'phone' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create block' }))

    await waitFor(() => expect(partnerAdapter.createBlock).toHaveBeenCalledWith({
      room_type: 7, date_from: day(1), date_to: day(2), rooms: 1, note: 'phone',
    }))
  })

  it('Remove on a block confirms, then deletes it', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<PartnerRoomCalendar roomTypeId={7} roomTypeName="Deluxe King" totalRooms={5} initialMonth={MONTH} />)
    await screen.findAllByText('Booking.com')
    vi.mocked(partnerAdapter.deleteBlock).mockResolvedValue({ data: null, error: null })

    fireEvent.click(screen.getByRole('button', { name: /Remove block Booking\.com/ }))

    await waitFor(() => expect(partnerAdapter.deleteBlock).toHaveBeenCalledWith(9))
  })
})
