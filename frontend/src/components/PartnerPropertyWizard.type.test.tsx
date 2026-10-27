import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerPropertyWizard } from './PartnerPropertyWizard'
import { partnerAdapter } from '../adapters/partnerAdapter'
import { nameTheHotel, settle } from '../test/utils'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    createProperty: vi.fn(),
    getAssignedPlace: vi.fn().mockResolvedValue({ data: { country_ref: 1, region_ref: 10, city_ref: 100 }, error: null }),
    getPropertyTypes: vi.fn().mockResolvedValue({
      data: [{ id: 7, name: 'Apartment', slug: 'apartment' }, { id: 3, name: 'Hotel', slug: 'hotel' }],
      error: null,
    }),
  },
}))

vi.mock('../adapters/geographyAdapter', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: {
    getCountries: vi.fn().mockResolvedValue({ data: [{ id: 1, code: 'UZ', currency: 'UZS', name_uz: 'Oʻzbekiston', name_ru: 'Узбекистан', name_en: 'Uzbekistan', hotel_count: 1 }], error: null }),
    getRegions: vi.fn().mockResolvedValue({ data: [{ id: 10, name_uz: 'Toshkent', name_ru: 'Ташкент', name_en: 'Tashkent', hotel_count: 1 }], error: null }),
    getCities: vi.fn().mockResolvedValue({ data: [{ id: 100, name_uz: 'Chilonzor', name_ru: 'Чиланзар', name_en: 'Chilanzar', hotel_count: 1 }], error: null }),
  },
}))

describe('PartnerPropertyWizard property type', () => {
  it('lets the owner pick the type from the list the server gave, not a fixed id', async () => {
    vi.mocked(partnerAdapter.createProperty).mockResolvedValue({ data: { id: 5 } as never, error: null })
    const onSuccess = vi.fn()
    render(<PartnerPropertyWizard onSuccess={onSuccess} />)
    await settle()
    const select = await screen.findByLabelText('Property type')
    expect(Array.from((select as HTMLSelectElement).options).map(option => option.text)).toEqual(['Apartment', 'Hotel'])
    fireEvent.change(select, { target: { value: '3' } })
    nameTheHotel('Oltin Vodiy')
    fireEvent.click(screen.getByText('Next'))
    await screen.findByText('Location Details')
    fireEvent.change(screen.getByLabelText('Address Line 1 *'), { target: { value: '123 Test St' } })
    await waitFor(() => expect(screen.getByLabelText('City')).toHaveValue('100'))
    fireEvent.click(screen.getByText('Next'))
    await screen.findByText('Amenities & Features')
    fireEvent.click(screen.getByText('Next'))
    await screen.findByText('Pricing')
    fireEvent.click(screen.getByText('Next'))
    fireEvent.click(await screen.findByRole('button', { name: /Create Property/i }))
    await waitFor(() => expect(onSuccess).toHaveBeenCalled())
    expect(partnerAdapter.createProperty).toHaveBeenCalledWith(expect.objectContaining({ property_type: 3 }))
  })

  it('does not leave the first step when there is no type to choose', async () => {
    vi.mocked(partnerAdapter.getPropertyTypes).mockResolvedValueOnce({ data: [], error: null })
    render(<PartnerPropertyWizard />)
    await settle()
    nameTheHotel('Oltin Vodiy')
    fireEvent.click(screen.getByText('Next'))
    expect(screen.getByRole('alert')).toHaveTextContent('Choose the property type.')
    expect(screen.queryByText('Location Details')).not.toBeInTheDocument()
  })
})
