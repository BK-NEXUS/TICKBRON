import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { PromoCarousel } from './PromoCarousel'
import { I18nProvider } from '../i18n/I18nContext'
import type { PromotedProperty } from '../adapters/promotionAdapter'

const trackClick = vi.fn()
vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { trackClick: (id: number) => trackClick(id) },
}))

function hotel(id: number, name: string, extra: Partial<PromotedProperty> = {}): PromotedProperty {
  return {
    id,
    promotion_id: id * 10,
    translations: [{ id, language: 'en', name, description: '' }],
    city: 'Samarkand',
    country: 'Uzbekistan',
    base_price: 450000,
    currency: 'UZS',
    average_rating: 9.1,
    review_count: 12,
    primary_photo: { id, photo: `/media/${id}.jpg`, photo_type: 'exterior', is_primary: true, display_order: 0 },
    ...extra,
  } as unknown as PromotedProperty
}

const THREE = [hotel(1, 'Alpha'), hotel(2, 'Beta'), hotel(3, 'Gamma')]

function renderCarousel(items: PromotedProperty[], props: { loading?: boolean } = {}) {
  return render(
    <I18nProvider>
      <MemoryRouter>
        <PromoCarousel items={items} {...props} />
      </MemoryRouter>
    </I18nProvider>,
  )
}

function activeName() {
  const active = document.querySelector('.promo-slide--active')
  return active?.querySelector('.promo-slide-name')?.textContent
}

// jsdom has no PointerEvent: a MouseEvent with the pointer event name carries clientX the same way
function pointer(target: HTMLElement, type: 'pointerdown' | 'pointerup', clientX: number) {
  fireEvent(target, new MouseEvent(type, { clientX, bubbles: true }))
}

function setReducedMotion(reduce: boolean) {
  window.matchMedia = vi.fn().mockImplementation((query: string) => ({
    matches: reduce && query.includes('prefers-reduced-motion'),
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
    dispatchEvent: vi.fn(),
    onchange: null,
  }))
}

describe('PromoCarousel', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    trackClick.mockReset()
    setReducedMotion(false)
    localStorage.clear()
  })
  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders nothing when there are no banners', () => {
    const { container } = renderCarousel([])
    expect(container).toBeEmptyDOMElement()
  })

  it('shows a skeleton of the same block while loading', () => {
    renderCarousel([], { loading: true })
    expect(screen.getByRole('status', { name: 'Loading featured hotels' })).toBeInTheDocument()
    expect(document.querySelector('.promo-carousel--loading')).not.toBeNull()
  })

  it('is a labelled carousel region', () => {
    renderCarousel(THREE)
    const region = screen.getByRole('region', { name: 'Featured hotels' })
    expect(region).toHaveAttribute('aria-roledescription', 'carousel')
  })

  it('shows one big banner with name, city, rating, price and the Ad badge', () => {
    renderCarousel(THREE)
    expect(activeName()).toBe('Alpha')
    const slide = document.querySelector('.promo-slide--active') as HTMLElement
    expect(slide).toHaveTextContent('Samarkand')
    expect(slide).toHaveTextContent('9.1')
    expect(slide).toHaveTextContent('450')
    expect(slide.querySelector('.promo-slide-badge')).toHaveTextContent('Ad')
    expect(slide.querySelector('img')).toHaveAttribute('src', '/media/1.jpg')
  })

  it('links the banner to the hotel page', () => {
    renderCarousel(THREE)
    const link = document.querySelector('.promo-slide--active a') as HTMLAnchorElement
    expect(link.getAttribute('href')).toBe('/property/1')
  })

  it('counts a click without blocking the navigation', () => {
    renderCarousel(THREE)
    fireEvent.click(document.querySelector('.promo-slide--active a') as HTMLElement)
    expect(trackClick).toHaveBeenCalledWith(10)
    expect(trackClick).toHaveBeenCalledTimes(1)
  })

  it('falls back to an icon when the hotel has no photo', () => {
    renderCarousel([hotel(4, 'NoPhoto', { primary_photo: undefined })])
    expect(document.querySelector('.promo-slide--active img')).toBeNull()
    expect(screen.getByTestId('promo-image-placeholder')).toBeInTheDocument()
  })

  it('omits the rating when the hotel has none', () => {
    renderCarousel([hotel(5, 'Unrated', { average_rating: null })])
    expect(document.querySelector('.promo-slide-rating')).toBeNull()
  })

  it('goes to the next and previous banner with the buttons, wrapping around', () => {
    renderCarousel(THREE)
    fireEvent.click(screen.getByRole('button', { name: 'Next banner' }))
    expect(activeName()).toBe('Beta')
    fireEvent.click(screen.getByRole('button', { name: 'Previous banner' }))
    fireEvent.click(screen.getByRole('button', { name: 'Previous banner' }))
    expect(activeName()).toBe('Gamma')
    fireEvent.click(screen.getByRole('button', { name: 'Next banner' }))
    expect(activeName()).toBe('Alpha')
  })

  it('has one dot per banner and the dots select a banner', () => {
    renderCarousel(THREE)
    const dots = screen.getAllByRole('tab')
    expect(dots).toHaveLength(3)
    expect(dots[0]).toHaveAttribute('aria-selected', 'true')
    fireEvent.click(screen.getByRole('tab', { name: 'Show banner 3' }))
    expect(activeName()).toBe('Gamma')
    expect(screen.getByRole('tab', { name: 'Show banner 3' })).toHaveAttribute('aria-selected', 'true')
  })

  it('supports the arrow keys', () => {
    renderCarousel(THREE)
    const region = screen.getByRole('region', { name: 'Featured hotels' })
    fireEvent.keyDown(region, { key: 'ArrowRight' })
    expect(activeName()).toBe('Beta')
    fireEvent.keyDown(region, { key: 'ArrowLeft' })
    expect(activeName()).toBe('Alpha')
  })

  it('rotates by itself every 5 seconds', () => {
    renderCarousel(THREE)
    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Beta')
    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Gamma')
    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Alpha')
  })

  it('pauses while the pointer is over it and resumes after', () => {
    renderCarousel(THREE)
    const region = screen.getByRole('region', { name: 'Featured hotels' })
    fireEvent.mouseEnter(region)
    act(() => { vi.advanceTimersByTime(20000) })
    expect(activeName()).toBe('Alpha')
    fireEvent.mouseLeave(region)
    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Beta')
  })

  it('pauses while a control inside has keyboard focus', () => {
    renderCarousel(THREE)
    fireEvent.focus(screen.getByRole('button', { name: 'Next banner' }))
    act(() => { vi.advanceTimersByTime(20000) })
    expect(activeName()).toBe('Alpha')
    fireEvent.blur(screen.getByRole('button', { name: 'Next banner' }))
    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Beta')
  })

  it('has a pause/play button that stops the rotation', () => {
    renderCarousel(THREE)
    fireEvent.click(screen.getByRole('button', { name: 'Pause rotation' }))
    act(() => { vi.advanceTimersByTime(20000) })
    expect(activeName()).toBe('Alpha')
    fireEvent.click(screen.getByRole('button', { name: 'Resume rotation' }))
    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Beta')
  })

  it('pauses while the browser tab is hidden', () => {
    renderCarousel(THREE)
    Object.defineProperty(document, 'hidden', { configurable: true, value: true })
    act(() => { document.dispatchEvent(new Event('visibilitychange')) })
    act(() => { vi.advanceTimersByTime(20000) })
    expect(activeName()).toBe('Alpha')
    Object.defineProperty(document, 'hidden', { configurable: true, value: false })
    act(() => { document.dispatchEvent(new Event('visibilitychange')) })
    act(() => { vi.advanceTimersByTime(5000) })
    expect(activeName()).toBe('Beta')
  })

  it('does not rotate by itself when the visitor prefers reduced motion, buttons still work', () => {
    setReducedMotion(true)
    renderCarousel(THREE)
    act(() => { vi.advanceTimersByTime(30000) })
    expect(activeName()).toBe('Alpha')
    expect(screen.queryByRole('button', { name: 'Pause rotation' })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'Next banner' }))
    expect(activeName()).toBe('Beta')
  })

  it('swiping left shows the next banner and swiping right the previous', () => {
    renderCarousel(THREE)
    const track = document.querySelector('.promo-carousel-viewport') as HTMLElement
    pointer(track, 'pointerdown', 300)
    pointer(track, 'pointerup', 150)
    expect(activeName()).toBe('Beta')
    pointer(track, 'pointerdown', 100)
    pointer(track, 'pointerup', 260)
    expect(activeName()).toBe('Alpha')
  })

  it('a tiny pointer movement is a tap, not a swipe', () => {
    renderCarousel(THREE)
    const track = document.querySelector('.promo-carousel-viewport') as HTMLElement
    pointer(track, 'pointerdown', 300)
    pointer(track, 'pointerup', 290)
    expect(activeName()).toBe('Alpha')
  })

  it('a single banner has no arrows, dots or pause button and never rotates', () => {
    renderCarousel([hotel(1, 'Solo')])
    expect(screen.queryByRole('button', { name: 'Next banner' })).toBeNull()
    expect(screen.queryAllByRole('tab')).toHaveLength(0)
    expect(screen.queryByRole('button', { name: 'Pause rotation' })).toBeNull()
    act(() => { vi.advanceTimersByTime(20000) })
    expect(activeName()).toBe('Solo')
  })

  it('only the active banner is reachable for assistive technology', () => {
    renderCarousel(THREE)
    const slides = document.querySelectorAll('.promo-slide')
    expect(slides).toHaveLength(3)
    expect(slides[0]).toHaveAttribute('aria-hidden', 'false')
    expect(slides[1]).toHaveAttribute('aria-hidden', 'true')
    expect(slides[1].querySelector('a')).toHaveAttribute('tabindex', '-1')
  })

  it('keeps the active index valid when the list gets shorter', () => {
    const { rerender } = renderCarousel(THREE)
    fireEvent.click(screen.getByRole('tab', { name: 'Show banner 3' }))
    rerender(
      <I18nProvider>
        <MemoryRouter>
          <PromoCarousel items={THREE.slice(0, 1)} />
        </MemoryRouter>
      </I18nProvider>,
    )
    expect(activeName()).toBe('Alpha')
  })
})
