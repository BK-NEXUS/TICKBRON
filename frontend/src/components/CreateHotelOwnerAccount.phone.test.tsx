/**
 * A hotel-owner account is created with a phone number (stored only, no SMS).
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CreateHotelOwnerAccount } from './CreateHotelOwnerAccount'
import { adminAdapter } from '../adapters/adminAdapter'

vi.mock('../adapters/adminAdapter')

function fill(phone: string) {
  fireEvent.change(screen.getByLabelText('Email Address:'), { target: { value: 'owner@example.com' } })
  fireEvent.change(screen.getByLabelText('First Name:'), { target: { value: 'Olim' } })
  fireEvent.change(screen.getByLabelText('Last Name:'), { target: { value: 'Karimov' } })
  fireEvent.change(screen.getByLabelText('Phone number'), { target: { value: phone } })
  fireEvent.change(screen.getByLabelText('Password:', { exact: true }), { target: { value: 'Owner#Secret2026' } })
  fireEvent.change(screen.getByLabelText('Confirm Password:'), { target: { value: 'Owner#Secret2026' } })
}

describe('CreateHotelOwnerAccount phone number', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(adminAdapter.createHotelOwner).mockResolvedValue({
      data: { id: 9, email: 'owner@example.com', first_name: 'Olim', last_name: 'Karimov' } as never, error: null,
    })
  })

  it('asks for the number and marks it required', () => {
    render(<CreateHotelOwnerAccount />)
    const box = screen.getByLabelText('Phone number')
    expect(box).toBeRequired()
    expect(box).toHaveAttribute('type', 'tel')
  })

  it('keeps only digits and a leading plus while typing', () => {
    render(<CreateHotelOwnerAccount />)
    const box = screen.getByLabelText('Phone number')
    fireEvent.change(box, { target: { value: '+998 (90) 12x' } })
    expect(box).toHaveValue('+9989012')
  })

  it('sends the number with the account', async () => {
    render(<CreateHotelOwnerAccount />)
    fill('+998901234567')
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    await waitFor(() => expect(adminAdapter.createHotelOwner).toHaveBeenCalledWith(expect.objectContaining({ phone_number: '+998901234567' })))
  })

  it('refuses an invalid number before calling the server', async () => {
    render(<CreateHotelOwnerAccount />)
    fill('12345')
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a valid phone number in international format')
    expect(adminAdapter.createHotelOwner).not.toHaveBeenCalled()
  })
})
