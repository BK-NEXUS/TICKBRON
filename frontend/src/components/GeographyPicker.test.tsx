import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { GeographyPicker } from './GeographyPicker'
import { I18nProvider } from '../i18n/I18nContext'
import { geographyAdapter } from '../adapters/geographyAdapter'

vi.mock('../adapters/geographyAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: { getCountries: vi.fn(), getRegions: vi.fn(), getCities: vi.fn() },
}))

const names = (id: number, en: string, uz: string, ru: string) => ({ id, name_en: en, name_uz: uz, name_ru: ru, hotel_count: 1 })
const countries = [{ ...names(1, 'Uzbekistan', 'Oʻzbekiston', 'Узбекистан'), code: 'UZ', currency: 'UZS' }]
const regions = [names(10, 'Tashkent', 'Toshkent', 'Ташкент'), names(11, 'Samarkand', 'Samarqand', 'Самарканд')]
const cities = [names(100, 'Chilanzar', 'Chilonzor', 'Чиланзар')]

const empty = { country_ref: null, region_ref: null, city_ref: null }

function setup(value = empty, language?: string) {
  if (language) localStorage.setItem('tickbron.language', language)
  const onChange = vi.fn()
  render(<I18nProvider><GeographyPicker value={value} onChange={onChange} /></I18nProvider>)
  return onChange
}

describe('GeographyPicker', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(geographyAdapter.getCountries).mockResolvedValue({ data: countries, error: null })
    vi.mocked(geographyAdapter.getRegions).mockResolvedValue({ data: regions, error: null })
    vi.mocked(geographyAdapter.getCities).mockResolvedValue({ data: cities, error: null })
  })

  it('shows the countries first and keeps region and city disabled', async () => {
    setup(empty, 'en')
    expect(await screen.findByRole('option', { name: 'Uzbekistan' })).toBeInTheDocument()
    expect(screen.getByLabelText('Region')).toBeDisabled()
    expect(screen.getByLabelText('City')).toBeDisabled()
  })

  it('shows names in the page language', async () => {
    setup(empty, 'ru')
    expect(await screen.findByRole('option', { name: 'Узбекистан' })).toBeInTheDocument()
  })

  it('choosing a country reports it and clears region and city', async () => {
    const onChange = setup({ country_ref: null, region_ref: 10, city_ref: 100 }, 'en')
    await screen.findByRole('option', { name: 'Uzbekistan' })
    fireEvent.change(screen.getByLabelText('Country'), { target: { value: '1' } })
    expect(onChange).toHaveBeenCalledWith({ country_ref: 1, region_ref: null, city_ref: null }, { country: 'Uzbekistan', region: '', city: '' })
  })

  it('loads the regions of the chosen country by its code', async () => {
    setup({ country_ref: 1, region_ref: null, city_ref: null }, 'en')
    expect(await screen.findByRole('option', { name: 'Samarkand' })).toBeInTheDocument()
    expect(geographyAdapter.getRegions).toHaveBeenCalledWith('UZ')
  })

  it('choosing a region clears the city', async () => {
    const onChange = setup({ country_ref: 1, region_ref: null, city_ref: 100 }, 'en')
    await screen.findByRole('option', { name: 'Samarkand' })
    fireEvent.change(screen.getByLabelText('Region'), { target: { value: '11' } })
    expect(onChange).toHaveBeenCalledWith({ country_ref: 1, region_ref: 11, city_ref: null }, { country: 'Uzbekistan', region: 'Samarkand', city: '' })
  })

  it('loads the cities of the chosen region and reports the city', async () => {
    const onChange = setup({ country_ref: 1, region_ref: 10, city_ref: null }, 'en')
    await screen.findByRole('option', { name: 'Chilanzar' })
    // the region list loads in its own request; the reported region name needs it
    await screen.findByRole('option', { name: 'Tashkent' })
    expect(geographyAdapter.getCities).toHaveBeenCalledWith(10)
    fireEvent.change(screen.getByLabelText('City'), { target: { value: '100' } })
    expect(onChange).toHaveBeenCalledWith({ country_ref: 1, region_ref: 10, city_ref: 100 }, { country: 'Uzbekistan', region: 'Tashkent', city: 'Chilanzar' })
  })

  it('shows an error with a retry button when the countries cannot be loaded', async () => {
    vi.mocked(geographyAdapter.getCountries).mockResolvedValueOnce({ data: null, error: 'boom' })
    setup(empty, 'en')
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load the list')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('option', { name: 'Uzbekistan' })).toBeInTheDocument()
  })

  it('says so when a region has no cities', async () => {
    vi.mocked(geographyAdapter.getCities).mockResolvedValue({ data: [], error: null })
    setup({ country_ref: 1, region_ref: 10, city_ref: null }, 'en')
    await waitFor(() => expect(screen.getByText('No cities available for this region yet.')).toBeInTheDocument())
  })
})
