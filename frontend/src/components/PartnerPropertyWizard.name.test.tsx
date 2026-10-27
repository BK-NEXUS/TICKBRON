import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PartnerPropertyWizard } from './PartnerPropertyWizard'
import { partnerAdapter } from '../adapters/partnerAdapter'
import { nameTheHotel, settle } from '../test/utils'

vi.mock('../adapters/partnerAdapter', () => ({
  partnerAdapter: {
    createProperty: vi.fn(),
    getPropertyTypes: vi.fn().mockResolvedValue({ data: [{ id: 1, name: 'Hotel', slug: 'hotel' }], error: null }),
    getAssignedPlace: vi.fn().mockResolvedValue({ data: { country_ref: 1, region_ref: 10, city_ref: 100 }, error: null }),
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

describe('PartnerPropertyWizard hotel name', () => {
  it('asks for the name in uz, ru and en on the first step', async () => {
    render(<PartnerPropertyWizard />)
    await settle()
    for (const language of ['Oʻzbekcha', 'Русский', 'English']) {
      expect(screen.getByLabelText(`Hotel name (${language})`)).toBeInTheDocument()
      expect(screen.getByLabelText(`Description (${language})`)).toBeInTheDocument()
    }
  })

  it('does not leave the first step without a name in some language', async () => {
    render(<PartnerPropertyWizard />)
    await settle()
    fireEvent.click(screen.getByText('Next'))
    expect(screen.getByRole('alert')).toHaveTextContent('Give the hotel a name in at least one language.')
    expect(screen.queryByText('Location Details')).not.toBeInTheDocument()
  })

  it('a name of spaces is no name', async () => {
    render(<PartnerPropertyWizard />)
    await settle()
    nameTheHotel('   ')
    fireEvent.click(screen.getByText('Next'))
    expect(screen.getByRole('alert')).toHaveTextContent('Give the hotel a name')
  })

  it('a name in one language is enough and goes to the API with its description', async () => {
    vi.mocked(partnerAdapter.createProperty).mockResolvedValue({ data: { id: 5 } as never, error: null })
    const onSuccess = vi.fn()
    render(<PartnerPropertyWizard onSuccess={onSuccess} />)
    await settle()
    fireEvent.change(screen.getByLabelText('Hotel name (Oʻzbekcha)'), { target: { value: ' Oltin Vodiy ' } })
    fireEvent.change(screen.getByLabelText('Description (Oʻzbekcha)'), { target: { value: 'Markazda' } })
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
    expect(partnerAdapter.createProperty).toHaveBeenCalledWith(expect.objectContaining({
      translations: { uz: { name: 'Oltin Vodiy', description: 'Markazda' } },
    }))
  })
})
