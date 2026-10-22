/**
 * Home "Where to?": countries with their pictures, then the regions of the chosen country, then the search.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { HomeWhereTo } from './HomeWhereTo'
import { I18nProvider } from '../i18n/I18nContext'
import { geographyAdapter } from '../adapters/geographyAdapter'

vi.mock('../adapters/geographyAdapter', async importOriginal => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: { getCountries: vi.fn(), getRegions: vi.fn() },
}))
const api = vi.mocked(geographyAdapter)

const names = (en: string, uz: string, ru: string) => ({ name_en: en, name_uz: uz, name_ru: ru })
const COUNTRIES = [
  { id: 1, code: 'UZ', currency: 'UZS', ...names('Uzbekistan', 'Oʻzbekiston', 'Узбекистан'), hotel_count: 5, image_url: '/media/geography/countries/uz.png' },
  { id: 2, code: 'KZ', currency: 'KZT', ...names('Kazakhstan', 'Qozogʻiston', 'Казахстан'), hotel_count: 0, image_url: null },
]
const REGIONS = [
  { id: 10, ...names('Samarkand', 'Samarqand', 'Самарканд'), hotel_count: 3, image_url: '/media/geography/regions/sam.png' },
  { id: 11, ...names('Bukhara', 'Buxoro', 'Бухара'), hotel_count: 1, image_url: null },
]

function renderIt(language = 'en') {
  localStorage.setItem('tickbron.language', language)
  return render(<I18nProvider><MemoryRouter><HomeWhereTo /></MemoryRouter></I18nProvider>)
}

describe('HomeWhereTo', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetAllMocks()
    api.getCountries.mockResolvedValue({ data: COUNTRIES, error: null })
    api.getRegions.mockResolvedValue({ data: REGIONS, error: null })
  })

  it('shows a loading status, then every country with its name, picture and hotel count', async () => {
    api.getCountries.mockReturnValueOnce(new Promise(() => {}))
    const { unmount } = renderIt()
    expect(screen.getByRole('status')).toHaveTextContent('Loading destinations...')
    unmount()
    renderIt()
    const uz = await screen.findByRole('button', { name: /Uzbekistan/ })
    expect(within(uz).getByText('5 properties')).toBeInTheDocument()
    expect(uz.querySelector('img')).toHaveAttribute('src', expect.stringContaining('/media/geography/countries/uz.png'))
    const kz = screen.getByRole('button', { name: /Kazakhstan/ })
    expect(kz.querySelector('img')).toBeNull()
    expect(within(kz).getByText('0 properties')).toBeInTheDocument()
  })

  it('names follow the page language', async () => {
    renderIt('ru')
    expect(await screen.findByRole('button', { name: /Узбекистан/ })).toBeInTheDocument()
  })

  it('opens the regions of the chosen country as links to the search, and goes back', async () => {
    renderIt()
    fireEvent.click(await screen.findByRole('button', { name: /Uzbekistan/ }))
    expect(api.getRegions).toHaveBeenCalledWith('UZ')
    const link = await screen.findByRole('link', { name: /Samarkand/ })
    expect(link).toHaveAttribute('href', '/search?destination=Samarkand')
    expect(screen.getByRole('heading', { name: 'Uzbekistan' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Kazakhstan/ })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'All countries' }))
    expect(await screen.findByRole('button', { name: /Kazakhstan/ })).toBeInTheDocument()
  })

  it('a region link carries the name in the page language', async () => {
    renderIt('uz')
    fireEvent.click(await screen.findByRole('button', { name: /Oʻzbekiston/ }))
    expect(await screen.findByRole('link', { name: /Samarqand/ })).toHaveAttribute('href', `/search?destination=${encodeURIComponent('Samarqand')}`)
  })

  it('a country with no regions says so', async () => {
    api.getRegions.mockResolvedValue({ data: [], error: null })
    renderIt()
    fireEvent.click(await screen.findByRole('button', { name: /Kazakhstan/ }))
    expect(await screen.findByText('No regions here yet.')).toBeInTheDocument()
  })

  it('shows an error with a retry when the countries cannot be loaded', async () => {
    api.getCountries.mockResolvedValueOnce({ data: null, error: 'Network error' })
    renderIt()
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load destinations.')
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByRole('button', { name: /Uzbekistan/ })).toBeInTheDocument()
  })

  it('shows an error with a retry when the regions cannot be loaded, and the way back stays', async () => {
    api.getRegions.mockResolvedValueOnce({ data: null, error: 'boom' })
    renderIt()
    fireEvent.click(await screen.findByRole('button', { name: /Uzbekistan/ }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load destinations.')
    fireEvent.click(screen.getByRole('button', { name: 'Try Again' }))
    expect(await screen.findByRole('link', { name: /Samarkand/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'All countries' })).toBeInTheDocument()
  })

  it('renders nothing when there is no active country', async () => {
    api.getCountries.mockResolvedValue({ data: [], error: null })
    const { container } = renderIt()
    await waitFor(() => expect(container.querySelector('section')).toBeNull())
  })
})
