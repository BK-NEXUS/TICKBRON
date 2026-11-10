import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { GeographyPicker } from './GeographyPicker'
import { I18nProvider } from '../i18n/I18nContext'
import { geographyAdapter } from '../adapters/geographyAdapter'

vi.mock('../adapters/geographyAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: { getCountries: vi.fn(), getRegions: vi.fn() },
}))

const names = (id: number, en: string, uz: string, ru: string) => ({ id, name_en: en, name_uz: uz, name_ru: ru, hotel_count: 1 })
const countries = [{ ...names(1, 'Uzbekistan', 'Oʻzbekiston', 'Узбекистан'), code: 'UZ', currency: 'UZS' }]
const regions = [names(10, 'Tashkent', 'Toshkent', 'Ташкент'), names(11, 'Samarkand', 'Samarqand', 'Самарканд')]

const empty = { country_ref: null, region_ref: null }

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
  })

  it('shows the countries first and keeps the region disabled; there is no city list', async () => {
    setup(empty, 'en')
    expect(await screen.findByRole('option', { name: 'Uzbekistan' })).toBeInTheDocument()
    expect(screen.getByLabelText('Region')).toBeDisabled()
    expect(screen.queryByLabelText('City')).not.toBeInTheDocument()
  })

  it('shows names in the page language', async () => {
    setup(empty, 'ru')
    expect(await screen.findByRole('option', { name: 'Узбекистан' })).toBeInTheDocument()
  })

  it('choosing a country reports it and clears the region', async () => {
    const onChange = setup({ country_ref: null, region_ref: 10 }, 'en')
    await screen.findByRole('option', { name: 'Uzbekistan' })
    fireEvent.change(screen.getByLabelText('Country'), { target: { value: '1' } })
    expect(onChange).toHaveBeenCalledWith({ country_ref: 1, region_ref: null }, { country: 'Uzbekistan', region: '' })
  })

  it('loads the regions of the chosen country by its code', async () => {
    setup({ country_ref: 1, region_ref: null }, 'en')
    expect(await screen.findByRole('option', { name: 'Samarkand' })).toBeInTheDocument()
    expect(geographyAdapter.getRegions).toHaveBeenCalledWith('UZ')
  })

  it('choosing a region reports it with the names of the chosen rows', async () => {
    const onChange = setup({ country_ref: 1, region_ref: null }, 'en')
    await screen.findByRole('option', { name: 'Samarkand' })
    fireEvent.change(screen.getByLabelText('Region'), { target: { value: '11' } })
    expect(onChange).toHaveBeenCalledWith({ country_ref: 1, region_ref: 11 }, { country: 'Uzbekistan', region: 'Samarkand' })
  })

  it('pickers mounted together share one request for the countries', async () => {
    localStorage.setItem('tickbron.language', 'en')
    render(
      <I18nProvider>
        {[1, 2, 3].map(key => <GeographyPicker key={key} value={empty} onChange={vi.fn()} />)}
      </I18nProvider>
    )
    expect(await screen.findAllByRole('option', { name: 'Uzbekistan' })).toHaveLength(3)
    expect(geographyAdapter.getCountries).toHaveBeenCalledTimes(1)
  })

  it('asks again for the countries when a picker is mounted later', async () => {
    setup(empty, 'en')
    await screen.findByRole('option', { name: 'Uzbekistan' })
    setup(empty, 'en')
    await waitFor(() => expect(geographyAdapter.getCountries).toHaveBeenCalledTimes(2))
  })

  it('shows an error with a retry button when the countries cannot be loaded', async () => {
    vi.mocked(geographyAdapter.getCountries).mockResolvedValueOnce({ data: null, error: 'boom' })
    setup(empty, 'en')
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load the list')
    fireEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('option', { name: 'Uzbekistan' })).toBeInTheDocument()
  })
})
