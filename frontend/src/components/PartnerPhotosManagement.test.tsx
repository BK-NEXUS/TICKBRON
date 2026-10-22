/**
 * Owner photo management: list with the cover marked, upload, make cover, caption, delete.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PartnerPhotosManagement } from './PartnerPhotosManagement'
import { partnerAdapter } from '../adapters/partnerAdapter'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    getPropertyPhotos: vi.fn(),
    uploadPropertyPhoto: vi.fn(),
    updatePropertyPhoto: vi.fn(),
    deletePropertyPhoto: vi.fn(),
  },
}))

const photo = (id: number, over: object = {}) => ({
  id, photo: `/media/${id}.jpg`, photo_url: `/media/${id}.jpg`, photo_type: 'other', caption: null,
  is_primary: false, display_order: id, alt_text: null, ...over,
})
const file = (name: string) => new File(['x'], name, { type: 'image/jpeg' })
const api = vi.mocked(partnerAdapter)

describe('PartnerPhotosManagement', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.getPropertyPhotos.mockResolvedValue({ data: [photo(1, { is_primary: true, caption: 'Lobby' }), photo(2)], error: null })
    api.updatePropertyPhoto.mockResolvedValue({ data: photo(2), error: null })
    api.deletePropertyPhoto.mockResolvedValue({ data: null, error: null })
    api.uploadPropertyPhoto.mockResolvedValue({ data: photo(3), error: null })
  })
  afterEach(() => vi.restoreAllMocks())

  it('shows a loading status, then the photos with exactly one cover badge', async () => {
    render(<PartnerPhotosManagement propertyId={5} />)
    expect(screen.getByRole('status')).toHaveTextContent('Loading photos...')
    expect(await screen.findAllByRole('img')).toHaveLength(2)
    expect(screen.getAllByText('Cover')).toHaveLength(1)
    expect(screen.getByText('2 of 50 photos')).toBeInTheDocument()
    expect(api.getPropertyPhotos).toHaveBeenCalledWith(5)
  })

  it('shows an empty state that explains the cover rule', async () => {
    api.getPropertyPhotos.mockResolvedValue({ data: [], error: null })
    render(<PartnerPhotosManagement propertyId={5} />)
    expect(await screen.findByText('No photos yet')).toBeInTheDocument()
    expect(screen.getByText(/first one becomes the cover/i)).toBeInTheDocument()
  })

  it('shows the error and retries', async () => {
    api.getPropertyPhotos.mockResolvedValueOnce({ data: null, error: 'Network error' })
    render(<PartnerPhotosManagement propertyId={5} />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Network error')
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findAllByRole('img')).toHaveLength(2)
  })

  it('uploads each chosen file, then reloads the list', async () => {
    render(<PartnerPhotosManagement propertyId={5} />)
    await screen.findAllByRole('img')
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [file('a.jpg'), file('b.jpg')] } })
    await waitFor(() => expect(api.uploadPropertyPhoto).toHaveBeenCalledTimes(2))
    expect(api.uploadPropertyPhoto.mock.calls[0][0]).toBe(5)
    expect(api.uploadPropertyPhoto.mock.calls[0][1]).toMatchObject({ photo_type: 'other' })
    await waitFor(() => expect(api.getPropertyPhotos).toHaveBeenCalledTimes(2))
  })

  it('names the file whose upload failed and keeps uploading the rest', async () => {
    api.uploadPropertyPhoto
      .mockResolvedValueOnce({ data: null, error: 'File size exceeds maximum allowed size of 10.0MB' })
      .mockResolvedValueOnce({ data: photo(3), error: null })
    render(<PartnerPhotosManagement propertyId={5} />)
    await screen.findAllByRole('img')
    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [file('big.jpg'), file('ok.jpg')] } })
    expect(await screen.findByRole('alert')).toHaveTextContent('big.jpg: File size exceeds maximum allowed size of 10.0MB')
    expect(api.uploadPropertyPhoto).toHaveBeenCalledTimes(2)
  })

  it('refuses to start more uploads than the 50 photo limit allows', async () => {
    api.getPropertyPhotos.mockResolvedValue({ data: Array.from({ length: 50 }, (_, i) => photo(i + 1, { is_primary: i === 0 })), error: null })
    render(<PartnerPhotosManagement propertyId={5} />)
    await screen.findAllByRole('img')
    expect(screen.getByLabelText('Add photos')).toBeDisabled()
  })

  it('makes a photo the cover and reloads; the cover itself has no such button', async () => {
    render(<PartnerPhotosManagement propertyId={5} />)
    await screen.findAllByRole('img')
    expect(screen.getAllByRole('button', { name: 'Make cover' })).toHaveLength(1)
    fireEvent.click(screen.getByRole('button', { name: 'Make cover' }))
    await waitFor(() => expect(api.updatePropertyPhoto).toHaveBeenCalledWith(5, 2, { is_primary: true }))
    await waitFor(() => expect(api.getPropertyPhotos).toHaveBeenCalledTimes(2))
  })

  it('saves an edited caption', async () => {
    render(<PartnerPhotosManagement propertyId={5} />)
    await screen.findAllByRole('img')
    const input = screen.getAllByLabelText('Caption')[0]
    expect(input).toHaveValue('Lobby')
    fireEvent.change(input, { target: { value: 'Reception' } })
    fireEvent.click(screen.getAllByRole('button', { name: 'Save caption' })[0])
    await waitFor(() => expect(api.updatePropertyPhoto).toHaveBeenCalledWith(5, 1, { caption: 'Reception' }))
  })

  it('deletes only after the owner confirms', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true)
    render(<PartnerPhotosManagement propertyId={5} />)
    await screen.findAllByRole('img')
    const del = screen.getAllByRole('button', { name: 'Delete' })[1]
    fireEvent.click(del)
    expect(api.deletePropertyPhoto).not.toHaveBeenCalled()
    fireEvent.click(del)
    await waitFor(() => expect(api.deletePropertyPhoto).toHaveBeenCalledWith(5, 2))
    expect(confirm).toHaveBeenCalledTimes(2)
  })

  it('shows a failed action next to the list instead of dropping it', async () => {
    api.deletePropertyPhoto.mockResolvedValue({ data: null, error: 'Resource not found' })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    render(<PartnerPhotosManagement propertyId={5} />)
    await screen.findAllByRole('img')
    fireEvent.click(screen.getAllByRole('button', { name: 'Delete' })[0])
    const alert = await screen.findByRole('alert')
    expect(within(alert).getByText('Resource not found')).toBeInTheDocument()
    expect(screen.getAllByRole('img')).toHaveLength(2)
  })
})
