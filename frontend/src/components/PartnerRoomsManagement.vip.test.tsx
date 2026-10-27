/**
 * R9: the hotel owner alone switches a room type VIP on or off; VIP shows on the owner's cards.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerRoomsManagement } from './PartnerRoomsManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: { getRoomTypes: vi.fn(), createRoomType: vi.fn(), updateRoomType: vi.fn(), getRoomPhotos: vi.fn() },
}))

const room = (over: object) => ({
  id: 7, property: 3, name: 'Deluxe King', slug: 'deluxe-king', description: 'Big', base_occupancy: 2, max_occupancy: 3,
  base_price: 95, currency: 'USD', total_rooms: 4, bed_configuration: '1 King Bed', photos_count: 0, cover_url: null, ...over,
}) as never

describe('PartnerRoomsManagement VIP switch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(partnerAdapter.getRoomTypes).mockResolvedValue({
      data: [room({ is_vip: true }), room({ id: 8, name: 'Standard', slug: 'standard', is_vip: false })], error: null,
    })
    vi.mocked(partnerAdapter.updateRoomType).mockResolvedValue({ data: room({}), error: null })
    vi.mocked(partnerAdapter.createRoomType).mockResolvedValue({ data: room({}), error: null })
    vi.mocked(partnerAdapter.getRoomPhotos).mockResolvedValue({ data: [], error: null })
  })

  it('marks only the VIP room type on the owner list', async () => {
    render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" />)
    await screen.findByText('Deluxe King')
    expect(screen.getAllByLabelText('VIP room')).toHaveLength(1)
  })

  it('loads the current value on edit and sends is_vip false when the owner switches it off', async () => {
    render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" />)
    fireEvent.click(await screen.findByRole('button', { name: 'Edit Deluxe King' }))
    const box = screen.getByRole('checkbox', { name: /VIP/ })
    expect(box).toBeChecked()
    fireEvent.click(box)
    fireEvent.click(screen.getByRole('button', { name: 'Update Room Type' }))
    await waitFor(() => expect(partnerAdapter.updateRoomType).toHaveBeenCalled())
    expect(vi.mocked(partnerAdapter.updateRoomType).mock.calls[0][1]).toMatchObject({ is_vip: false })
  })

  it('creates a room type as VIP when the owner ticks the box', async () => {
    render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" />)
    fireEvent.click(await screen.findByRole('button', { name: /room type/i }))
    fireEvent.change(document.getElementById('room_name') as HTMLInputElement, { target: { value: 'Suite' } })
    fireEvent.change(document.getElementById('bed_configuration') as HTMLInputElement, { target: { value: '1 King' } })
    const box = screen.getByRole('checkbox', { name: /VIP/ })
    expect(box).not.toBeChecked()
    fireEvent.click(box)
    fireEvent.click(screen.getByRole('button', { name: 'Create Room Type' }))
    await waitFor(() => expect(partnerAdapter.createRoomType).toHaveBeenCalled())
    expect(vi.mocked(partnerAdapter.createRoomType).mock.calls[0][0]).toMatchObject({ is_vip: true })
  })
})
