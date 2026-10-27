import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { CreateHotelOwnerAccount } from './CreateHotelOwnerAccount'
import { adminAdapter } from '../adapters/adminAdapter'

vi.mock('../adapters/adminAdapter')

const created = { id: 9, email: 'new.admin@example.com', first_name: 'Aziza', last_name: 'Karimova', full_name: 'Aziza Karimova', is_staff: true, is_superuser: false, is_active: true } as never

function fill() {
  fireEvent.change(screen.getByLabelText('Email Address:'), { target: { value: 'new.admin@example.com' } })
  fireEvent.change(screen.getByLabelText('First Name:'), { target: { value: 'Aziza' } })
  fireEvent.change(screen.getByLabelText('Last Name:'), { target: { value: 'Karimova' } })
  fireEvent.change(screen.getByLabelText('Phone number'), { target: { value: '+998901234567' } })
  fireEvent.change(screen.getByLabelText('Password:'), { target: { value: 'Long-Enough-Pass#2026' } })
  fireEvent.change(screen.getByLabelText('Confirm Password:'), { target: { value: 'Long-Enough-Pass#2026' } })
}

describe('CreateHotelOwnerAccount as the administrator form', () => {
  beforeEach(() => vi.clearAllMocks())

  it('has no place to pick and says it creates an administrator', () => {
    render(<CreateHotelOwnerAccount kind="admin" />)
    expect(screen.getByRole('heading', { name: 'Create Administrator Account' })).toBeInTheDocument()
    expect(screen.queryByLabelText('Country')).not.toBeInTheDocument()
  })

  it('sends the person to the administrator endpoint, without a place', async () => {
    vi.mocked(adminAdapter.createAdmin).mockResolvedValue({ data: created, error: null })
    const onSuccess = vi.fn()
    render(<CreateHotelOwnerAccount kind="admin" onSuccess={onSuccess} />)
    fill()
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    await waitFor(() => expect(onSuccess).toHaveBeenCalled())
    expect(adminAdapter.createHotelOwner).not.toHaveBeenCalled()
    expect(adminAdapter.createAdmin).toHaveBeenCalledWith({
      email: 'new.admin@example.com', first_name: 'Aziza', last_name: 'Karimova', phone_number: '+998901234567',
      password: 'Long-Enough-Pass#2026', password_confirm: 'Long-Enough-Pass#2026',
    })
    expect(screen.getByText('Administrator Account Created Successfully')).toBeInTheDocument()
  })

  it('shows what the server refused', async () => {
    vi.mocked(adminAdapter.createAdmin).mockResolvedValue({ data: null, error: 'A user with this email already exists.' })
    render(<CreateHotelOwnerAccount kind="admin" />)
    fill()
    fireEvent.click(screen.getByRole('button', { name: /Create Account/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('A user with this email already exists.')
  })
})
