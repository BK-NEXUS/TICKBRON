/** The photos of one ad: up to 10, what the site accepts, add and remove, read-only for staff. */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { PromotionPhotosDialog } from './PromotionPhotosDialog'
import { I18nProvider } from '../i18n/I18nContext'
import { promotionAdapter, type AdPhoto, type AdminPromotion } from '../adapters/promotionAdapter'

vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { getPromotionPhotos: vi.fn(), uploadPromotionPhoto: vi.fn(), deletePromotionPhoto: vi.fn() },
}))

const adapter = vi.mocked(promotionAdapter)
const photo = (id: number): AdPhoto => ({ id, photo_url: `/media/promotions/1/${id}.jpg`, display_order: id })
const promotion = (photos: AdPhoto[]) => ({
  id: 1, property: { id: 10, name: 'Registan Plaza', city: 'Samarkand', status: 'active' }, photos, photos_count: photos.length,
}) as unknown as AdminPromotion
const image = (name: string, type = 'image/png', size = 1000) => {
  const file = new File(['x'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

function open(photos: AdPhoto[], props: { canEdit?: boolean; justCreated?: boolean } = {}) {
  const onChanged = vi.fn()
  const onClose = vi.fn()
  localStorage.setItem('tickbron.language', 'en')
  render(
    <I18nProvider>
      <PromotionPhotosDialog promotion={promotion(photos)} canEdit={props.canEdit ?? true} justCreated={props.justCreated}
        onClose={onClose} onChanged={onChanged} />
    </I18nProvider>,
  )
  return { onChanged, onClose }
}

describe('PromotionPhotosDialog', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    adapter.getPromotionPhotos.mockResolvedValue({ data: [], error: null, code: null })
    adapter.uploadPromotionPhoto.mockResolvedValue({ data: photo(9), error: null, code: null })
    adapter.deletePromotionPhoto.mockResolvedValue({ data: null, error: null, code: null })
  })

  it('shows the photos, how many of ten, and what the site accepts', () => {
    open([photo(1), photo(2)])

    expect(screen.getByRole('dialog', { name: 'Photos of the ad: Registan Plaza' })).toBeInTheDocument()
    expect(screen.getByText('2 of 10 photos')).toBeInTheDocument()
    expect(document.querySelectorAll('.promotion-photo-item img')).toHaveLength(2)
    const help = screen.getByText(/JPG, PNG, WebP or GIF, up to 10 MB each/)
    expect(help).toHaveTextContent('at most 40 megapixels')
    expect(help).toHaveTextContent('1920 × 720 px')
  })

  it('says the ad uses the hotel photos until it has its own', () => {
    open([])

    expect(screen.getByText(/the banner shows the hotel's own photos/)).toBeInTheDocument()
  })

  it('asks for photos right after the ad was created', () => {
    open([], { justCreated: true })

    expect(screen.getByRole('status')).toHaveTextContent('The ad is saved. Add its photos now (up to 10).')
  })

  it('uploads the chosen pictures one by one, then reads the list again and tells the screen behind it', async () => {
    adapter.getPromotionPhotos.mockResolvedValue({ data: [photo(1), photo(2)], error: null, code: null })
    const { onChanged } = open([])

    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [image('a.png'), image('b.png')] } })

    await waitFor(() => expect(adapter.uploadPromotionPhoto).toHaveBeenCalledTimes(2))
    expect(adapter.uploadPromotionPhoto.mock.calls.map(call => [call[0], call[1].name])).toEqual([[1, 'a.png'], [1, 'b.png']])
    await waitFor(() => expect(screen.getByText('2 of 10 photos')).toBeInTheDocument())
    expect(onChanged).toHaveBeenCalled()
  })

  it('never sends more than ten: only the places that are left are used', async () => {
    const full = Array.from({ length: 9 }, (_, i) => photo(i + 1))
    adapter.getPromotionPhotos.mockResolvedValue({ data: full, error: null, code: null })
    open(full)

    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [image('a.png'), image('b.png'), image('c.png')] } })

    await waitFor(() => expect(adapter.uploadPromotionPhoto).toHaveBeenCalledTimes(1))
  })

  it('with ten photos the picker is off', () => {
    open(Array.from({ length: 10 }, (_, i) => photo(i + 1)))

    expect(screen.getByLabelText('Add photos')).toBeDisabled()
  })

  it('refuses a wrong type or a too big file before sending it, and says which', async () => {
    open([])

    fireEvent.change(screen.getByLabelText('Add photos'), {
      target: { files: [image('note.txt', 'text/plain'), image('huge.png', 'image/png', 11 * 1024 * 1024)] },
    })

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('note.txt')
    expect(alert).toHaveTextContent('huge.png')
    expect(adapter.uploadPromotionPhoto).not.toHaveBeenCalled()
  })

  it('shows the reason when the server refuses a picture', async () => {
    adapter.uploadPromotionPhoto.mockResolvedValue({ data: null, error: 'x', code: 'too_many_photos' })
    open([])

    fireEvent.change(screen.getByLabelText('Add photos'), { target: { files: [image('a.png')] } })

    expect(await screen.findByRole('alert')).toHaveTextContent('a.png: An ad can have at most 10 photos.')
  })

  it('removes a photo after a confirmation and reads the list again', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    adapter.getPromotionPhotos.mockResolvedValue({ data: [photo(2)], error: null, code: null })
    open([photo(1), photo(2)])

    fireEvent.click(screen.getByRole('button', { name: 'Remove photo 1' }))

    await waitFor(() => expect(adapter.deletePromotionPhoto).toHaveBeenCalledWith(1, 1))
    await waitFor(() => expect(screen.getByText('1 of 10 photos')).toBeInTheDocument())
  })

  it('keeps the photo when the confirmation is declined', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    open([photo(1)])

    fireEvent.click(screen.getByRole('button', { name: 'Remove photo 1' }))

    expect(adapter.deletePromotionPhoto).not.toHaveBeenCalled()
  })

  it('staff can only look: no picker and no remove buttons', () => {
    open([photo(1)], { canEdit: false })

    expect(screen.queryByLabelText('Add photos')).toBeNull()
    expect(screen.queryByRole('button', { name: /Remove photo/ })).toBeNull()
    expect(screen.getByText('You can look at the photos; only a super admin can change them.')).toBeInTheDocument()
  })

  it('closes', () => {
    const { onClose } = open([])

    fireEvent.click(within(screen.getByRole('dialog')).getByRole('button', { name: 'Close' }))

    expect(onClose).toHaveBeenCalled()
  })
})
