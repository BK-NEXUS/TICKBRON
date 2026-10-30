/** The banner shows the several pictures of an ad one after another and says where the ads are for. */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { PromoCarousel } from './PromoCarousel'
import { I18nProvider } from '../i18n/I18nContext'
import type { PromotedProperty } from '../adapters/promotionAdapter'

vi.mock('../adapters/promotionAdapter', () => ({ promotionAdapter: { trackClick: vi.fn() } }))

const urls = (count: number, prefix = 'ad') => Array.from({ length: count }, (_, i) => `/media/${prefix}-${i + 1}.jpg`)

function hotel(id: number, name: string, promoPhotos?: string[]): PromotedProperty {
  return {
    id, promotion_id: id * 10, translations: [{ id, language: 'en', name, description: '' }], city: 'Samarkand',
    country: 'Uzbekistan', base_price: 450000, currency: 'UZS', average_rating: 9.1, review_count: 12,
    primary_photo: { id, photo: `/media/primary-${id}.jpg`, photo_type: 'exterior', is_primary: true, display_order: 0 },
    promo_photos: promoPhotos,
  } as unknown as PromotedProperty
}

function renderCarousel(items: PromotedProperty[], placeName?: string) {
  localStorage.setItem('tickbron.language', 'en')
  return render(
    <I18nProvider>
      <MemoryRouter>
        <PromoCarousel items={items} placeName={placeName} />
      </MemoryRouter>
    </I18nProvider>,
  )
}

const activeSlide = () => document.querySelector('.promo-slide--active') as HTMLElement
const shownPhoto = () => activeSlide().querySelector('.promo-slide-photo--on')?.getAttribute('src')
const activeName = () => activeSlide().querySelector('.promo-slide-name')?.textContent

function setReducedMotion(reduce: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: reduce && query.includes('prefers-reduced-motion'), media: query, addEventListener: vi.fn(),
    removeEventListener: vi.fn(), addListener: vi.fn(), removeListener: vi.fn(), dispatchEvent: vi.fn(), onchange: null,
  }))
}

describe('PromoCarousel photos', () => {
  beforeEach(() => { vi.useFakeTimers(); setReducedMotion(false); localStorage.clear() })
  afterEach(() => { vi.useRealTimers() })

  it('shows the first picture of the ad and has every picture ready', () => {
    renderCarousel([hotel(1, 'Alpha', urls(4))])

    expect(activeSlide().querySelectorAll('img')).toHaveLength(4)
    expect(shownPhoto()).toBe('/media/ad-1.jpg')
  })

  it('moves through the pictures by itself, one after the other, and starts over', () => {
    renderCarousel([hotel(1, 'Alpha', urls(3))])

    act(() => { vi.advanceTimersByTime(1800) })
    expect(shownPhoto()).toBe('/media/ad-2.jpg')
    act(() => { vi.advanceTimersByTime(1800) })
    expect(shownPhoto()).toBe('/media/ad-3.jpg')
    act(() => { vi.advanceTimersByTime(1800) })
    expect(shownPhoto()).toBe('/media/ad-1.jpg')
  })

  it('keeps the hotel photos of an ad without its own pictures: the cover alone, nothing to move', () => {
    renderCarousel([hotel(1, 'Alpha', [])])

    expect(activeSlide().querySelectorAll('img')).toHaveLength(1)
    expect(shownPhoto()).toBe('/media/primary-1.jpg')
    act(() => { vi.advanceTimersByTime(1800) })
    expect(shownPhoto()).toBe('/media/primary-1.jpg')
  })

  it('stays on a banner long enough to show all its pictures, but never longer than 12 seconds', () => {
    renderCarousel([hotel(1, 'Alpha', urls(6)), hotel(2, 'Beta', urls(10, 'beta'))])

    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Alpha')
    act(() => { vi.advanceTimersByTime(5800) })
    expect(activeName()).toBe('Beta')
    act(() => { vi.advanceTimersByTime(11900) })
    expect(activeName()).toBe('Beta')
    act(() => { vi.advanceTimersByTime(200) })
    expect(activeName()).toBe('Alpha')
  })

  it('starts the next banner on its first picture', () => {
    renderCarousel([hotel(1, 'Alpha', urls(2)), hotel(2, 'Beta', urls(2, 'beta'))])

    act(() => { vi.advanceTimersByTime(5000) })

    expect(activeName()).toBe('Beta')
    expect(shownPhoto()).toBe('/media/beta-1.jpg')
  })

  it('stops moving the pictures while the pointer is over the banner', () => {
    renderCarousel([hotel(1, 'Alpha', urls(3))])
    fireEvent.mouseEnter(screen.getByRole('region', { name: 'Featured hotels' }))

    act(() => { vi.advanceTimersByTime(10000) })

    expect(shownPhoto()).toBe('/media/ad-1.jpg')
  })

  it('does not move the pictures for visitors who prefer reduced motion', () => {
    setReducedMotion(true)
    renderCarousel([hotel(1, 'Alpha', urls(3))])

    act(() => { vi.advanceTimersByTime(10000) })

    expect(shownPhoto()).toBe('/media/ad-1.jpg')
  })

  it('says where the ads are for when it knows the place', () => {
    renderCarousel([hotel(1, 'Alpha')], 'Samarkand region')

    expect(screen.getByRole('heading', { name: 'Ads in Samarkand region' })).toBeInTheDocument()
  })

  it('has no place heading without a place', () => {
    renderCarousel([hotel(1, 'Alpha')])

    expect(screen.queryByRole('heading')).toBeNull()
  })
})
