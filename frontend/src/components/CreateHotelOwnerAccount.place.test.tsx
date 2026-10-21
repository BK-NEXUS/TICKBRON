/**
 * The super admin chooses where the hotels of a new account will appear (country > region > city).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CreateHotelOwnerAccount } from './CreateHotelOwnerAccount'
import { adminAdapter } from '../adapters/adminAdapter'

vi.mock('../adapters/adminAdapter')
vi.mock('../adapters/geographyAdapter', async importOriginal => ({
  ...(await importOriginal<typeof import('../adapters/geographyAdapter')>()),
  geographyAdapter: {
    getCountries: vi.fn().mockResolvedValue({ data: [{ id: 1, code: 'UZ', currency: 'UZS', name_uz: 'Oʻzbekiston', name_ru: 'Узбекистан', name_en: 'Uzbekistan', hotel_count: 1, image_url: null }], error: null }),
    getRegions: vi.fn().mockResolvedValue({ data: [{ id: 10, name_uz: 'Toshkent', name_ru: 'Ташкент', name_en: 'Tashkent', hotel_count: 1, image_url: null }], error: null }),
    getCities: vi.fn().mockResolvedValue({ data: [{ id: 100, name_uz: 'Chilonzor', name_ru: 'Чиланзар', name_en: 'Chilanzar', hotel_count: 1 }], error: null }),
  },
}))

function fillAccount() {
  fireEvent.change(screen.getByLabelText('Email Address:'), { target: { value: 'owner@example.com' } })
  fireEvent.change(screen.getByLabelText('First Name:'), { target: { value: 'Olim' } })
  fireEvent.change(screen.getByLabelText('Last Name:'), { target: { value: 'Karimov' } })
  fireEvent.change(screen.getByLabelText('Password:'), { target: { value: 'Owner#Secret2026' } })
  fireEvent.change(screen.getByLabelText('Confirm Password:'), { target: { value: 'Owner#Secret2026' } })
}

async function pickPlace() {
  await screen.findByRole('option', { name: 'Uzbekistan' })
  fireEvent.change(screen.getByLabelText('Country'), { target: { value: '1' } })
  await screen.findByRole('option', { name: 'Tashkent' })
  fireEvent.change(screen.getByLabelText('Region'), { target: { value: '10' } })
  await screen.findByRole('option', { name: 'Chilanzar' })
  fireEvent.change(screen.getByLabelText('City'), { target: { value: '100' } })
}

describe('CreateHotelOwnerAccount place', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(adminAdapter.createHotelOwner).mockResolvedValue({
      data: { id: 9, email: 'owner@example.com', first_name: 'Olim', last_name: 'Karimov' } as never, error: null,
    })
  })

  it('asks where the hotel will appear and refuses to create the account without a place', async () => {
    render(<CreateHotelOwnerAccount />)
    expect(await screen.findByText('Where will the hotel appear?')).toBeInTheDocument()
    fillAccount()
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Choose where the hotel will appear')
    expect(adminAdapter.createHotelOwner).not.toHaveBeenCalled()
  })

  it('refuses a half-chosen place (country and region, no city)', async () => {
    render(<CreateHotelOwnerAccount />)
    fillAccount()
    await screen.findByRole('option', { name: 'Uzbekistan' })
    fireEvent.change(screen.getByLabelText('Country'), { target: { value: '1' } })
    await screen.findByRole('option', { name: 'Tashkent' })
    fireEvent.change(screen.getByLabelText('Region'), { target: { value: '10' } })
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Choose where the hotel will appear')
    expect(adminAdapter.createHotelOwner).not.toHaveBeenCalled()
  })

  it('sends the three place ids with the account', async () => {
    render(<CreateHotelOwnerAccount />)
    fillAccount()
    await pickPlace()
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    await waitFor(() => expect(adminAdapter.createHotelOwner).toHaveBeenCalledWith(expect.objectContaining({
      email: 'owner@example.com', country_ref: 1, region_ref: 10, city_ref: 100,
    })))
  })

  it('shows the server error for a place that does not fit', async () => {
    vi.mocked(adminAdapter.createHotelOwner).mockResolvedValue({ data: null, error: 'This region is not in the chosen country.' })
    render(<CreateHotelOwnerAccount />)
    fillAccount()
    await pickPlace()
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('This region is not in the chosen country.')
  })
})
