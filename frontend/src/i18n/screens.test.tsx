import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { I18nProvider } from './I18nContext'
import { AuthProvider } from '../contexts/AuthContext'
import { Footer } from '../components/Footer'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import type { Language } from './options'

// Each migrated screen is rendered in Uzbek and Russian: a string left in English shows up here.
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { getCurrentUser: vi.fn().mockResolvedValue({ success: false }) },
}))

async function renderIn(language: Language, element: React.ReactElement) {
  localStorage.setItem('tickbron.language', language)
  render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter>{element}</MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  )
  await act(async () => {})
}

describe('migrated screens in uz and ru', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => localStorage.clear())

  it('footer', async () => {
    await renderIn('uz', <Footer />)
    expect(screen.getByText('Yordam markazi')).toBeInTheDocument()
    expect(screen.queryByText('Help Center')).not.toBeInTheDocument()
  })

  it('footer in Russian', async () => {
    await renderIn('ru', <Footer />)
    expect(screen.getByText('Центр помощи')).toBeInTheDocument()
  })

  it('login page', async () => {
    await renderIn('uz', <LoginPage />)
    expect(screen.getByRole('heading', { name: 'Xush kelibsiz' })).toBeInTheDocument()
    expect(screen.getByLabelText('Parol', { selector: 'input' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Telefon va SMS-kod' })).toBeInTheDocument()
    expect(screen.queryByText('Welcome Back')).not.toBeInTheDocument()
  })

  it('register page in Russian', async () => {
    await renderIn('ru', <RegisterPage />)
    expect(screen.getByRole('heading', { name: 'Создать аккаунт' })).toBeInTheDocument()
    expect(screen.getByLabelText('Полное имя')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Показать подтверждение пароля' })).toBeInTheDocument()
  })
})
