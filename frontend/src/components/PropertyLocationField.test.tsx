import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PropertyLocationField } from './PropertyLocationField'
import { statusAdapter } from '../adapters/statusAdapter'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: { setPropertyLocation: vi.fn() },
}))

vi.mock('../adapters/geographyAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: {
    getCountries: vi.fn().mockResolvedValue({ data: [{ id: 1, code: 'UZ', currency: 'UZS', name_uz: 'Oʻzbekiston', name_ru: 'Узбекистан', name_en: 'Uzbekistan', hotel_count: 1 }], error: null }),
    getRegions: vi.fn().mockResolvedValue({ data: [
      { id: 10, name_uz: 'Toshkent', name_ru: 'Ташкент', name_en: 'Tashkent', hotel_count: 1 },
      { id: 11, name_uz: 'Samarqand', name_ru: 'Самарканд', name_en: 'Samarkand', hotel_count: 1 },
    ], error: null }),
  },
}))

const setLocation = vi.mocked(statusAdapter.setPropertyLocation)
const none = { country_ref: null, region_ref: null }
const tashkent = { country_ref: 1, region_ref: 10 }
// The two lists load independently: wait until the saved location shows in both
const tashkentLoaded = () => waitFor(() => {
  expect(screen.getByLabelText('Country')).toHaveValue('1')
  expect(screen.getByLabelText('Region')).toHaveValue('10')
})
const saveButton = () => screen.getByRole('button', { name: 'Save location' })

describe('PropertyLocationField', () => {
  beforeEach(() => setLocation.mockReset())

  it('shows the current location', async () => {
    render(<PropertyLocationField propertyId={1} location={tashkent} />)
    await tashkentLoaded()
  })

  it('shows nothing chosen for a property without a location', async () => {
    render(<PropertyLocationField propertyId={2} location={none} />)
    await screen.findByRole('option', { name: 'Uzbekistan' })
    expect(screen.getByLabelText('Country')).toHaveValue('')
  })

  it('Save is disabled until the location changes', async () => {
    render(<PropertyLocationField propertyId={1} location={tashkent} />)
    await tashkentLoaded()
    expect(saveButton()).toBeDisabled()
  })

  it('saves the new country and region ids', async () => {
    setLocation.mockResolvedValue({ data: { id: 1, ...tashkent, region_ref: 11 }, error: null })
    const onSaved = vi.fn()
    render(<PropertyLocationField propertyId={1} location={tashkent} onSaved={onSaved} />)
    await tashkentLoaded()

    fireEvent.change(screen.getByLabelText('Region'), { target: { value: '11' } })
    fireEvent.click(saveButton())

    expect(await screen.findByRole('status')).toHaveTextContent('Location saved')
    expect(setLocation).toHaveBeenCalledWith(1, { country_ref: 1, region_ref: 11 })
    expect(onSaved).toHaveBeenCalledWith({ country_ref: 1, region_ref: 11 })
  })

  it('does not save a half location (a country without a region)', async () => {
    render(<PropertyLocationField propertyId={1} location={tashkent} />)
    await tashkentLoaded()
    fireEvent.change(screen.getByLabelText('Country'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('Region'), { target: { value: '' } })
    expect(saveButton()).toBeDisabled()
  })

  it('clearing the country clears the location (Unspecified)', async () => {
    setLocation.mockResolvedValue({ data: { id: 1, ...none }, error: null })
    const onSaved = vi.fn()
    render(<PropertyLocationField propertyId={1} location={tashkent} onSaved={onSaved} />)
    await tashkentLoaded()

    fireEvent.change(screen.getByLabelText('Country'), { target: { value: '' } })
    fireEvent.click(saveButton())

    await waitFor(() => expect(setLocation).toHaveBeenCalledWith(1, none))
    expect(onSaved).toHaveBeenCalledWith(none)
  })

  it('shows the server error', async () => {
    setLocation.mockResolvedValue({ data: null, error: 'The region does not belong to the country.' })
    render(<PropertyLocationField propertyId={1} location={none} />)
    await screen.findByRole('option', { name: 'Uzbekistan' })
    fireEvent.change(screen.getByLabelText('Country'), { target: { value: '1' } })
    fireEvent.change(await screen.findByLabelText('Region'), { target: { value: '10' } })
    fireEvent.click(saveButton())

    expect(await screen.findByRole('alert')).toHaveTextContent('does not belong')
  })

  it('keeps the "Location saved" message when the new location comes back through the props', async () => {
    setLocation.mockResolvedValue({ data: { id: 1, ...tashkent }, error: null })
    const { rerender } = render(<PropertyLocationField propertyId={1} location={none} />)
    await screen.findByRole('option', { name: 'Uzbekistan' })
    fireEvent.change(screen.getByLabelText('Country'), { target: { value: '1' } })
    fireEvent.change(await screen.findByLabelText('Region'), { target: { value: '10' } })
    fireEvent.click(saveButton())
    await screen.findByRole('status')

    rerender(<PropertyLocationField propertyId={1} location={tashkent} />)
    expect(screen.getByRole('status')).toHaveTextContent('Location saved')
  })
})
