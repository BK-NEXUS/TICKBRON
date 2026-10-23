/** The advertising panel by region: counts and hotels per region, and the list limited to one region. */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent, within } from '@testing-library/react'
import { AdminPromotions } from './AdminPromotions'
import { I18nProvider } from '../i18n/I18nContext'
import { promotionAdapter, type PromotionRegion } from '../adapters/promotionAdapter'

vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: {
    listPromotions: vi.fn(), searchHotels: vi.fn(), createPromotion: vi.fn(), getRegionPanel: vi.fn(),
    getPromotionPhotos: vi.fn(), pausePromotion: vi.fn(), resumePromotion: vi.fn(), markPromotionPaid: vi.fn(),
    cancelPromotion: vi.fn(), getPromotionStats: vi.fn(), uploadPromotionPhoto: vi.fn(), deletePromotionPhoto: vi.fn(),
  },
}))

const adapter = vi.mocked(promotionAdapter)

const region = (id: number, en: string, uz: string, running: number, waiting: number, hotels: string[]): PromotionRegion => ({
  id, country_code: 'UZ', name_en: en, name_ru: en, name_uz: uz, running, waiting,
  hotels: hotels.map((name, index) => ({ id: id * 10 + index, name })),
})

const REGIONS = [
  region(1, 'Samarkand', 'Samarqand', 2, 1, ['Registan Plaza', 'Silk Inn']),
  region(2, 'Bukhara', 'Buxoro', 0, 0, []),
  region(3, 'Khiva', 'Xiva', 0, 2, []),
]

const empty = { data: { count: 0, next: null, previous: null, results: [] }, error: null, code: null }

function renderScreen() {
  render(
    <I18nProvider>
      <AdminPromotions isSuperAdmin />
    </I18nProvider>,
  )
}

describe('AdminPromotions regions', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    localStorage.setItem('tickbron.language', 'en')
    adapter.listPromotions.mockResolvedValue(empty)
    adapter.getRegionPanel.mockResolvedValue({ data: REGIONS, error: null, code: null })
  })

  it('lists every region with the ads running and waiting and the hotels that run them', async () => {
    renderScreen()

    const samarkand = (await screen.findByRole('button', { name: /Samarkand/ }))
    expect(samarkand).toHaveTextContent('2 running')
    expect(samarkand).toHaveTextContent('1 waiting')
    expect(samarkand).toHaveTextContent('Registan Plaza, Silk Inn')
    expect(screen.getByRole('button', { name: /Bukhara/ })).toHaveTextContent('No ads')
    expect(screen.getByRole('button', { name: /Khiva/ })).toHaveTextContent('2 waiting')
  })

  it('names the regions in the page language', async () => {
    localStorage.setItem('tickbron.language', 'uz')
    renderScreen()

    expect(await screen.findByRole('button', { name: /Samarqand/ })).toBeInTheDocument()
  })

  it('choosing a region limits the list to it, choosing it again or "All regions" lifts the limit', async () => {
    renderScreen()
    await waitFor(() => expect(adapter.listPromotions).toHaveBeenCalledWith(expect.objectContaining({ region: undefined })))

    fireEvent.click(await screen.findByRole('button', { name: /Samarkand/ }))

    await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ region: 1, page: 1 })))
    expect(screen.getByRole('button', { name: /Samarkand/ })).toHaveAttribute('aria-pressed', 'true')

    fireEvent.click(screen.getByRole('button', { name: /Samarkand/ }))
    await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ region: undefined })))

    fireEvent.click(screen.getByRole('button', { name: /Bukhara/ }))
    await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ region: 2 })))
    fireEvent.click(screen.getByRole('button', { name: 'All regions' }))
    await waitFor(() => expect(adapter.listPromotions).toHaveBeenLastCalledWith(expect.objectContaining({ region: undefined })))
  })

  it('shows an error with a retry when the regions cannot be loaded', async () => {
    adapter.getRegionPanel.mockResolvedValueOnce({ data: null, error: 'x', code: null })
    renderScreen()

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('The regions could not be loaded.')
    fireEvent.click(within(alert).getByRole('button', { name: 'Try Again' }))

    expect(await screen.findByRole('button', { name: /Samarkand/ })).toBeInTheDocument()
  })

  it('the region panel is read again when an ad was created', async () => {
    adapter.searchHotels.mockResolvedValue({ data: [{ id: 7, name: 'Registan Plaza', city: 'Samarkand', status: 'active', has_running_promotion: false }], error: null, code: null })
    adapter.createPromotion.mockResolvedValue({
      data: { id: 5, property: { id: 7, name: 'Registan Plaza', city: 'Samarkand', status: 'active' }, status: 'scheduled', photos: [], photos_count: 0 } as never,
      error: null, code: null,
    })
    renderScreen()
    await screen.findByRole('button', { name: /Samarkand/ })
    const before = adapter.getRegionPanel.mock.calls.length

    fireEvent.change(screen.getByLabelText('Find a hotel by name'), { target: { value: 'Reg' } })
    fireEvent.click(await screen.findByRole('button', { name: 'Promote Registan Plaza' }))
    const dialog = await screen.findByRole('dialog')
    fireEvent.change(within(dialog).getByLabelText('Start date'), { target: { value: '2026-10-10' } })
    fireEvent.change(within(dialog).getByLabelText('End date'), { target: { value: '2026-10-16' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Create promotion' }))

    await waitFor(() => expect(adapter.getRegionPanel.mock.calls.length).toBeGreaterThan(before))
  })
})
