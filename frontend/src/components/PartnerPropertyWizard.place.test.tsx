/**
 * An owner whose account has a place (set by the super admin) cannot choose another one.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerPropertyWizard } from './PartnerPropertyWizard'
import { partnerAdapter } from '../adapters/partnerAdapter'
import { nameTheHotel, settle } from '../test/utils'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    createProperty: vi.fn(),
    getAssignedPlace: vi.fn(),
    getPropertyTypes: vi.fn().mockResolvedValue({ data: [{ id: 1, name: 'Hotel', slug: 'hotel' }], error: null }),
  },
}))
vi.mock('../adapters/geographyAdapter', async importOriginal => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: {
    getCountries: vi.fn().mockResolvedValue({ data: [{ id: 1, code: 'UZ', currency: 'UZS', name_uz: 'Oʻzbekiston', name_ru: 'Узбекистан', name_en: 'Uzbekistan', hotel_count: 1, image_url: null }], error: null }),
    getRegions: vi.fn().mockResolvedValue({ data: [{ id: 10, name_uz: 'Toshkent', name_ru: 'Ташкент', name_en: 'Tashkent', hotel_count: 1, image_url: null }], error: null }),
  },
}))

const api = vi.mocked(partnerAdapter)

async function toLocationStep() {
  fireEvent.change(screen.getByLabelText('Max Guests *'), { target: { value: '4' } })
  fireEvent.change(screen.getByLabelText('Bedrooms *'), { target: { value: '2' } })
  fireEvent.change(screen.getByLabelText('Bathrooms *'), { target: { value: '1' } })
  fireEvent.click(screen.getByText('Next'))
  await screen.findByText('Location Details')
}

describe('PartnerPropertyWizard assigned place', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    api.createProperty.mockResolvedValue({ data: { id: 1, city: 'Tashkent' } as never, error: null })
  })

  it('shows the assigned place, locked, with a note', async () => {
    api.getAssignedPlace.mockResolvedValue({ data: { country_ref: 1, region_ref: 10 }, error: null })
    render(<PartnerPropertyWizard />)
    await settle()
    nameTheHotel()
    await toLocationStep()
    expect(await screen.findByText('The place of your hotels is set by the administrator.')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByLabelText('Region')).toHaveValue('10'))
    expect(screen.getByLabelText('Country')).toBeDisabled()
    expect(screen.getByLabelText('Region')).toBeDisabled()
    // The town is typed by the owner even when the place is set by the administrator
    expect(screen.getByLabelText('City *')).toBeEnabled()
  })

  it('creates the hotel in the assigned place without picking anything', async () => {
    api.getAssignedPlace.mockResolvedValue({ data: { country_ref: 1, region_ref: 10 }, error: null })
    render(<PartnerPropertyWizard />)
    await settle()
    nameTheHotel()
    await toLocationStep()
    fireEvent.change(screen.getByLabelText('Address Line 1 *'), { target: { value: '123 Test St' } })
    await waitFor(() => expect(screen.getByLabelText('Region')).toHaveValue('10'))
    fireEvent.change(screen.getByLabelText('City *'), { target: { value: 'Chilanzar' } })
    fireEvent.click(screen.getByText('Next'))
    await screen.findByText('Amenities & Features')
    fireEvent.click(screen.getByText('Next'))
    await screen.findByText('Pricing')
    fireEvent.click(screen.getByText('Next'))
    fireEvent.click(await screen.findByRole('button', { name: /Create Property|Submit/i }))
    await waitFor(() => expect(api.createProperty).toHaveBeenCalledWith(expect.objectContaining({
      country_ref: 1, region_ref: 10, city: 'Chilanzar',
    })))
  })

  it('an owner without an assigned place still picks the place', async () => {
    api.getAssignedPlace.mockResolvedValue({ data: { country_ref: null, region_ref: null }, error: null })
    render(<PartnerPropertyWizard />)
    await settle()
    nameTheHotel()
    await toLocationStep()
    await screen.findByRole('option', { name: 'Uzbekistan' })
    expect(screen.getByLabelText('Country')).toBeEnabled()
    expect(screen.queryByText('The place of your hotels is set by the administrator.')).not.toBeInTheDocument()
  })
})
