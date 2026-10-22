/**
 * What cannot be valid is never typed: no digits in names, no letters in number boxes.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { CreateHotelOwnerAccount } from './CreateHotelOwnerAccount'
import { RegisterPage } from '../pages/RegisterPage'
import { AuthProvider } from '../contexts/AuthContext'
import { useNumberKeyGuard } from '../hooks/useNumberKeyGuard'

vi.mock('../adapters/adminAdapter', () => ({ adminAdapter: { createHotelOwner: vi.fn() } }))
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { login: vi.fn(), register: vi.fn(), getCurrentUser: vi.fn().mockResolvedValue({ data: null, error: 'x' }) },
}))

const typeInto = (el: HTMLElement, value: string) => fireEvent.change(el, { target: { value } })

describe('name fields', () => {
  it('hotel owner account: first and last name take no digits', () => {
    render(<CreateHotelOwnerAccount />)
    const first = screen.getByLabelText(/first name/i)
    const last = screen.getByLabelText(/last name/i)
    typeInto(first, 'Olim7')
    typeInto(last, '5Karimov')
    expect(first).toHaveValue('Olim')
    expect(last).toHaveValue('Karimov')
  })

  it('register: full name takes no digits', async () => {
    render(<AuthProvider><MemoryRouter><RegisterPage /></MemoryRouter></AuthProvider>)
    const name = await screen.findByLabelText(/full name/i)
    typeInto(name, 'Ali 99 Valiyev')
    expect(name).toHaveValue('Ali  Valiyev')
  })
})

describe('number boxes', () => {
  function Boxes() {
    useNumberKeyGuard()
    return <><input type="number" aria-label="n" /><input type="text" aria-label="t" /></>
  }

  it('refuse e, E, + and - but accept digits; text boxes are untouched', () => {
    render(<Boxes />)
    const n = screen.getByLabelText('n')
    expect(fireEvent.keyDown(n, { key: 'e' })).toBe(false)
    expect(fireEvent.keyDown(n, { key: '-' })).toBe(false)
    expect(fireEvent.keyDown(n, { key: '5' })).toBe(true)
    expect(fireEvent.keyDown(screen.getByLabelText('t'), { key: 'e' })).toBe(true)
  })
})
