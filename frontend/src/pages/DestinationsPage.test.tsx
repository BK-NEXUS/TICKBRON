import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { DestinationsPage } from './DestinationsPage'
import { I18nProvider } from '../i18n/I18nContext'
import { geographyAdapter } from '../adapters/geographyAdapter'

vi.mock('../adapters/geographyAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: { getCountries: vi.fn(), getRegions: vi.fn(), getCities: vi.fn() },
}))

const place = (id: number, en: string, uz: string, ru: string, hotel_count: number) =>
  ({ id, name_en: en, name_uz: uz, name_ru: ru, hotel_count })

const api = vi.mocked(geographyAdapter)

function renderPage(language?: string) {
  if (language) localStorage.setItem('tickbron.language', language)
  return render(
    <I18nProvider><MemoryRouter><DestinationsPage /></MemoryRouter></I18nProvider>,
  )
}

describe('DestinationsPage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.clearAllMocks()
    api.getCountries.mockResolvedValue({ data: [
      { ...place(1, 'Uzbekistan', 'Oʻzbekiston', 'Узбекистан', 5), code: 'UZ', currency: 'UZS' },
      { ...place(2, 'Kazakhstan', 'Qozogʻiston', 'Казахстан', 0), code: 'KZ', currency: 'KZT' },
    ], error: null })
    api.getRegions.mockResolvedValue({ data: [
      place(10, 'Samarkand', 'Samarqand', 'Самарканд', 3),
      place(11, 'Bukhara', 'Buxoro', 'Бухара', 0),
    ], error: null })
    api.getCities.mockResolvedValue({ data: [
      place(100, 'Samarkand', 'Samarqand', 'Самарканд', 2),
      place(101, 'Shahrisabz', 'Shahrisabz', 'Шахрисабз', 1),
    ], error: null })
  })

  it('lists the cities that have hotels, grouped by country, linking to a search for the city', async () => {
    renderPage('en')
    const link = await screen.findByRole('link', { name: /Shahrisabz/ })
    expect(link).toHaveAttribute('href', '/search?destination=Shahrisabz')
    expect(screen.getByRole('heading', { name: 'Uzbekistan' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /^Samarkand/ })).toHaveTextContent('2 properties')
  })

  it('asks only for the places that have hotels', async () => {
    renderPage('en')
    await screen.findByRole('link', { name: /Shahrisabz/ })
    expect(api.getRegions).toHaveBeenCalledTimes(1)
    expect(api.getRegions).toHaveBeenCalledWith('UZ')
    expect(api.getCities).toHaveBeenCalledTimes(1)
    expect(api.getCities).toHaveBeenCalledWith(10)
  })

  it('shows names in the page language and searches by that name', async () => {
    renderPage('ru')
    const link = await screen.findByRole('link', { name: /Шахрисабз/ })
    expect(link).toHaveAttribute('href', `/search?destination=${encodeURIComponent('Шахрисабз')}`)
    expect(screen.getByRole('heading', { name: 'Узбекистан' })).toBeInTheDocument()
  })

  it('shows the region next to the city', async () => {
    renderPage('en')
    const link = await screen.findByRole('link', { name: /Shahrisabz/ })
    expect(within(link).getByText(/Samarkand/)).toBeInTheDocument()
  })

  it('shows a loading state, then the empty state when no place has hotels', async () => {
    api.getCountries.mockResolvedValue({ data: [], error: null })
    renderPage('en')
    expect(screen.getByRole('status')).toHaveTextContent('Loading destinations')
    expect(await screen.findByText('No destinations yet.')).toBeInTheDocument()
  })

  it('shows an error when a list cannot be loaded', async () => {
    api.getCities.mockResolvedValue({ data: null, error: 'boom' })
    renderPage('en')
    expect(await screen.findByRole('alert')).toHaveTextContent('boom')
  })
})
