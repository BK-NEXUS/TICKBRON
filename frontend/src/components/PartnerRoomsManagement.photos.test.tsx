/**
 * Room photos: the room form asks for photos, uploads them after the room type is created, shows the photo manager
 * when an existing room type is edited, and the list says which room types still have no photo.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerRoomsManagement } from './PartnerRoomsManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    getRoomTypes: vi.fn(), createRoomType: vi.fn(), updateRoomType: vi.fn(),
    getRoomPhotos: vi.fn(), uploadRoomPhoto: vi.fn(), updateRoomPhoto: vi.fn(), deleteRoomPhoto: vi.fn(),
  },
}))

const adapter = vi.mocked(partnerAdapter)

const room = (over: object) => ({
  id: 7, property: 3, name: 'Deluxe King', slug: 'deluxe-king', description: 'Big', base_occupancy: 2, max_occupancy: 3,
  base_price: 95, currency: 'UZS', total_rooms: 4, bed_configuration: '1 King Bed', is_vip: false,
  photos_count: 0, cover_url: null, ...over,
}) as never

const image = (name: string) => new File(['x'], name, { type: 'image/png' })

async function openCreateForm() {
  render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" currency="UZS" />)
  fireEvent.click(await screen.findByRole('button', { name: 'Add new room type' }))
  await screen.findByRole('heading', { name: 'Create Room Type' })
}

function fillRoom(name = 'Suite') {
  fireEvent.change(document.getElementById('room_name') as HTMLInputElement, { target: { value: name } })
  fireEvent.change(document.getElementById('bed_configuration') as HTMLInputElement, { target: { value: '1 King' } })
}

describe('PartnerRoomsManagement photos', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    adapter.getRoomTypes.mockResolvedValue({
      data: [room({ photos_count: 2, cover_url: 'http://x/cover.jpg' }), room({ id: 8, name: 'Standard', slug: 'standard' })], error: null,
    })
    adapter.createRoomType.mockResolvedValue({ data: room({ id: 21, name: 'Suite' }), error: null })
    adapter.getRoomPhotos.mockResolvedValue({ data: [], error: null })
    adapter.uploadRoomPhoto.mockResolvedValue({ data: {} as never, error: null })
  })

  it('the list shows the cover and the number of photos, and flags a room type without photos', async () => {
    render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" currency="UZS" />)

    const withPhotos = (await screen.findByText('Deluxe King')).closest('.room-type-card') as HTMLElement
    expect(within(withPhotos).getByText('2 photos')).toBeInTheDocument()
    expect(withPhotos.querySelector('img')).toHaveAttribute('src', 'http://x/cover.jpg')
    const without = screen.getByText('Standard').closest('.room-type-card') as HTMLElement
    expect(within(without).getByRole('button', { name: 'Add photos to Standard' })).toHaveTextContent('No photos yet')
  })

  it('the flag opens the room type so the owner can add photos', async () => {
    render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" currency="UZS" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Add photos to Standard' }))

    expect(await screen.findByRole('heading', { name: 'Room photos' })).toBeInTheDocument()
    expect(adapter.getRoomPhotos).toHaveBeenCalledWith(8)
  })

  it('the create form asks for photos and shows the hotel currency instead of a currency choice', async () => {
    await openCreateForm()

    expect(screen.getByRole('group', { name: 'Photos' })).toBeInTheDocument()
    expect(screen.getByText('The currency of this hotel')).toBeInTheDocument()
    expect(screen.queryByLabelText('Currency')).toBeNull()
    expect(screen.getByText('UZS')).toBeInTheDocument()
  })

  it('does not ask for a web address: the server makes it from the name', async () => {
    await openCreateForm()

    expect(document.getElementById('room_slug')).toBeNull()
    expect(screen.queryByText(/slug/i)).toBeNull()
  })

  it('uploads the chosen photos right after the room type is created, in the order chosen', async () => {
    await openCreateForm()
    fillRoom()
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [image('bed.png'), image('bath.png')] } })
    expect(screen.getByText('2 of 20 photos chosen')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Create Room Type' }))

    await waitFor(() => expect(adapter.uploadRoomPhoto).toHaveBeenCalledTimes(2))
    expect(adapter.createRoomType).toHaveBeenCalledWith(expect.objectContaining({ name: 'Suite', currency: 'UZS' }))
    expect(adapter.createRoomType.mock.calls[0][0]).not.toHaveProperty('slug')
    expect(adapter.uploadRoomPhoto.mock.calls.map(call => [call[0], call[1].photo.name])).toEqual([[21, 'bed.png'], [21, 'bath.png']])
    expect(await screen.findByText('Room type created successfully')).toBeInTheDocument()
  })

  it('a chosen photo can be taken out before saving', async () => {
    await openCreateForm()
    fillRoom()
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [image('bed.png'), image('bath.png')] } })

    fireEvent.click(screen.getByRole('button', { name: 'Remove bed.png' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create Room Type' }))

    await waitFor(() => expect(adapter.uploadRoomPhoto).toHaveBeenCalledTimes(1))
    expect(adapter.uploadRoomPhoto.mock.calls[0][1].photo.name).toBe('bath.png')
  })

  it('a room type can be created without photos', async () => {
    await openCreateForm()
    fillRoom()

    fireEvent.click(screen.getByRole('button', { name: 'Create Room Type' }))

    expect(await screen.findByText('Room type created successfully')).toBeInTheDocument()
    expect(adapter.uploadRoomPhoto).not.toHaveBeenCalled()
  })

  it('when a photo does not upload, the saved room type stays open with the reason and the photo manager', async () => {
    adapter.uploadRoomPhoto
      .mockResolvedValueOnce({ data: {} as never, error: null })
      .mockResolvedValueOnce({ data: null, error: 'Image is too large.' })
    await openCreateForm()
    fillRoom()
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [image('bed.png'), image('huge.png')] } })

    fireEvent.click(screen.getByRole('button', { name: 'Create Room Type' }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('The room type was saved, but some photos did not upload:')
    expect(alert).toHaveTextContent('huge.png: Image is too large.')
    expect(await screen.findByRole('heading', { name: 'Room photos' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Edit Room Type' })).toBeInTheDocument()
  })

  it('editing a room type shows its photo manager', async () => {
    adapter.getRoomPhotos.mockResolvedValue({
      data: [{ id: 5, photo: 'http://x/a.jpg', photo_url: 'http://x/a.jpg', photo_type: 'other', caption: '', is_primary: true, display_order: 1, alt_text: '' }],
      error: null,
    })
    render(<PartnerRoomsManagement propertyId={3} propertyName="Tashkent" currency="UZS" />)

    fireEvent.click(await screen.findByRole('button', { name: 'Edit Deluxe King' }))

    expect(await screen.findByRole('heading', { name: 'Room photos' })).toBeInTheDocument()
    expect(await screen.findByText('Cover')).toBeInTheDocument()
    expect(adapter.getRoomPhotos).toHaveBeenCalledWith(7)
  })
})
