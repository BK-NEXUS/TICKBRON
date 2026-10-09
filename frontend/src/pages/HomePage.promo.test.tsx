import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HomePage } from './HomePage'
import { I18nProvider } from '../i18n/I18nContext'
import { promotionAdapter, type PromotedProperty } from '../adapters/promotionAdapter'
import { settle } from '../test/utils'

vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { getHomePromotions: vi.fn(), trackClick: vi.fn() },
}))

function banner(id: number, name: string): PromotedProperty {
  return {
    id,
    promotion_id: id * 10,
    translations: [{ id, language: 'en', name, description: '' }],
    city: 'Samarkand',
    country: 'Uzbekistan',
    base_price: 450000,
    currency: 'UZS',
  } as unknown as PromotedProperty
}

function renderHome() {
  render(
    <I18nProvider>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('HomePage promo banner', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows the banners between the hero and the destinations', async () => {
    vi.mocked(promotionAdapter.getHomePromotions).mockResolvedValue({
      data: [banner(1, 'Alpha'), banner(2, 'Beta')], error: null, code: null,
    })
    renderHome()
    const carousel = await screen.findByRole('region', { name: 'Featured hotels' })
    expect(carousel).toHaveTextContent('Alpha')
    const hero = document.querySelector('.hero') as HTMLElement
    const destinations = document.querySelector('.destinations') as HTMLElement
    expect(hero.compareDocumentPosition(carousel) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(carousel.compareDocumentPosition(destinations) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('asks the backend once', async () => {
    vi.mocked(promotionAdapter.getHomePromotions).mockResolvedValue({ data: [banner(1, 'Alpha')], error: null, code: null })
    renderHome()
    await settle()
    expect(promotionAdapter.getHomePromotions).toHaveBeenCalledTimes(1)
  })

  it('shows a skeleton while loading and no block when there is nothing to show', async () => {
    vi.mocked(promotionAdapter.getHomePromotions).mockResolvedValue({ data: [], error: null, code: null })
    renderHome()
    expect(screen.getByRole('status', { name: 'Loading featured hotels' })).toBeInTheDocument()
    await settle()
    expect(screen.queryByRole('status', { name: 'Loading featured hotels' })).toBeNull()
    expect(document.querySelector('.promo-carousel')).toBeNull()
  })

  it('hides the block and keeps the page working when the request fails', async () => {
    vi.mocked(promotionAdapter.getHomePromotions).mockResolvedValue({ data: [], error: 'offline', code: null })
    renderHome()
    await settle()
    expect(document.querySelector('.promo-carousel')).toBeNull()
    expect(screen.getByText('Find Your Perfect Stay')).toBeInTheDocument()
  })

  it('survives a rejected request', async () => {
    vi.mocked(promotionAdapter.getHomePromotions).mockRejectedValue(new Error('boom'))
    renderHome()
    await settle()
    expect(document.querySelector('.promo-carousel')).toBeNull()
    expect(screen.getByText('Find Your Perfect Stay')).toBeInTheDocument()
  })

  it('does not update after the page was left', async () => {
    let resolve: (value: Awaited<ReturnType<typeof promotionAdapter.getHomePromotions>>) => void = () => {}
    vi.mocked(promotionAdapter.getHomePromotions).mockReturnValue(new Promise(r => { resolve = r }))
    const view = render(
      <I18nProvider>
        <MemoryRouter>
          <HomePage />
        </MemoryRouter>
      </I18nProvider>,
    )
    view.unmount()
    resolve({ data: [banner(1, 'Late')], error: null, code: null })
    await settle()
    expect(document.querySelector('.promo-carousel')).toBeNull()
  })
})
