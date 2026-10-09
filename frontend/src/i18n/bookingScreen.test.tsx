import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { I18nProvider } from './I18nContext'
import { BookingPage } from '../pages/BookingPage'

// One stable object: a new user on every render would re-run the page's effects forever
const auth = vi.hoisted(() => ({ user: { id: 1, email: 'a@b.uz', full_name: 'Test User' }, isAuthenticated: true, isLoading: false }))
vi.mock('../contexts/AuthContext', () => ({ useAuth: () => auth }))

describe('booking page in Russian', () => {
  beforeEach(() => localStorage.setItem('tickbron.language', 'ru'))
  afterEach(() => localStorage.clear())

  it('shows its own error text translated when the booking details are missing', async () => {
    render(<I18nProvider><MemoryRouter><BookingPage /></MemoryRouter></I18nProvider>)
    await act(async () => {})
    expect(screen.getByRole('heading', { name: 'Ошибка бронирования' })).toBeInTheDocument()
    expect(screen.getByText('Не хватает данных бронирования. Выберите номер и попробуйте ещё раз.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Вернуться на страницу объекта' })).toBeInTheDocument()
  })
})
