/** The home banner follows the country the guest opens under "Where to?": ads are not the same everywhere. */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { HomePage } from './HomePage'
import { I18nProvider } from '../i18n/I18nContext'
import { promotionAdapter, type PromotedProperty } from '../adapters/promotionAdapter'
import { geographyAdapter } from '../adapters/geographyAdapter'

vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: {
    searchProperties: vi.fn(() => new Promise(() => {})),
    getFilterOptions: vi.fn(() => new Promise(() => {})),
  },
}))
vi.mock('../adapters/promotionAdapter', () => ({
  promotionAdapter: { getHomePromotions: vi.fn(), trackClick: vi.fn() },
}))
vi.mock('../adapters/geographyAdapter', async importActual => {
  const actual = await importActual<typeof import('../adapters/geographyAdapter')>()
  return { ...actual, geographyAdapter: { getCountries: vi.fn(), getRegions: vi.fn() } }
})

const banner = (id: number, name: string) => ({
  id, promotion_id: id * 10, translations: [{ id, language: 'en', name, description: '' }], city: 'Samarkand',
  country: 'Uzbekistan', base_price: 450000, currency: 'UZS',
}) as unknown as PromotedProperty

const country = (id: number, code: string, en: string) => ({
  id, code, currency: 'UZS', name_uz: en, name_ru: en, name_en: en, hotel_count: 3, image_url: null,
})

function renderHome() {
  localStorage.setItem('tickbron.language', 'en')
  render(
    <I18nProvider>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </I18nProvider>,
  )
}

describe('HomePage banner by country', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(promotionAdapter.getHomePromotions).mockImplementation(async (countryId?: number) => ({
      data: [banner(countryId ?? 1, countryId === 2 ? 'Tashkent Grand' : 'Everywhere Inn')], error: null, code: null,
    }))
    vi.mocked(geographyAdapter.getCountries).mockResolvedValue({
      data: [country(2, 'UZ', 'Uzbekistan'), country(3, 'KZ', 'Kazakhstan')], error: null,
    } as never)
    vi.mocked(geographyAdapter.getRegions).mockResolvedValue({ data: [], error: null } as never)
  })

  it('shows the ads of every country first, without a place heading', async () => {
    renderHome()

    expect(await screen.findByText('Everywhere Inn')).toBeInTheDocument()
    expect(promotionAdapter.getHomePromotions).toHaveBeenCalledWith()
    expect(screen.queryByRole('heading', { name: /^Ads in/ })).toBeNull()
  })

  it('opening a country loads the ads of that country and names the place', async () => {
    renderHome()
    await screen.findByText('Everywhere Inn')

    fireEvent.click(await screen.findByRole('button', { name: /Uzbekistan/ }))

    await waitFor(() => expect(promotionAdapter.getHomePromotions).toHaveBeenLastCalledWith(2))
    expect(await screen.findByText('Tashkent Grand')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Ads in Uzbekistan' })).toBeInTheDocument()
  })

  it('going back to all countries brings back the ads of every country', async () => {
    renderHome()
    fireEvent.click(await screen.findByRole('button', { name: /Uzbekistan/ }))
    await screen.findByText('Tashkent Grand')

    fireEvent.click(screen.getByRole('button', { name: 'All countries' }))

    expect(await screen.findByText('Everywhere Inn')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: /^Ads in/ })).toBeNull()
  })
})
