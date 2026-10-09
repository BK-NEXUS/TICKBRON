import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { I18nProvider } from './I18nContext'
import { AuthProvider } from '../contexts/AuthContext'
import { Footer } from '../components/Footer'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { HomePage } from '../pages/HomePage'
import { SearchResultsPage } from '../pages/SearchResultsPage'
import { DestinationsPage } from '../pages/DestinationsPage'
import { PropertyCard } from '../components/PropertyCard'
import { Breadcrumbs } from '../components/Breadcrumbs'
import type { Property } from '../adapters/propertyAdapter'
import type { Language } from './options'

// Each migrated screen is rendered in Uzbek and Russian: a string left in English shows up here.
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { getCurrentUser: vi.fn().mockResolvedValue({ success: false }) },
}))
vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: {
    getFilterOptions: vi.fn().mockResolvedValue({ data: { property_types: [], features: [], amenities: [] } }),
    searchProperties: vi.fn().mockResolvedValue({ data: { results: [], count: 0 } }),
  },
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

  it('home page', async () => {
    await renderIn('uz', <HomePage />)
    expect(screen.getByRole('heading', { name: "O'zingizga mos joyni toping" })).toBeInTheDocument()
    expect(screen.getByText("Mashhur yo'nalishlar")).toBeInTheDocument()
    expect(screen.getByText('Mamnun mehmonlar')).toBeInTheDocument()
    expect(screen.queryByText('Popular Destinations')).not.toBeInTheDocument()
  })

  it('search form and filters in Russian', async () => {
    await renderIn('ru', <SearchResultsPage />)
    expect(await screen.findByRole('heading', { name: 'Фильтры' })).toBeInTheDocument()
    expect(screen.getByLabelText('Заезд')).toBeInTheDocument()
    expect(screen.getByText('Сортировка:')).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Цена: по возрастанию' })).toBeInTheDocument()
    expect(await screen.findByText('Объекты не найдены')).toBeInTheDocument()
    expect(screen.queryByText('Filters')).not.toBeInTheDocument()
  })

  it('property card with Russian plural forms', async () => {
    const property = {
      id: 1, translations: [{ name: 'Hotel Samarkand' }], city: 'Samarkand', country: 'Uzbekistan',
      max_guests: 2, bedrooms: 5, bathrooms: 21, base_price: 450000, currency: 'UZS',
    } as unknown as Property
    await renderIn('ru', <PropertyCard property={property} />)
    expect(screen.getByText('2 гостя')).toBeInTheDocument()
    expect(screen.getByText('5 спален')).toBeInTheDocument()
    expect(screen.getByText('21 ванная')).toBeInTheDocument()
    expect(screen.getByText('Подробнее')).toBeInTheDocument()
  })

  it('breadcrumbs and the destinations page', async () => {
    localStorage.setItem('tickbron.language', 'uz')
    render(
      <I18nProvider>
        <MemoryRouter initialEntries={['/destinations']}><Breadcrumbs /><DestinationsPage /></MemoryRouter>
      </I18nProvider>,
    )
    await act(async () => {})
    expect(screen.getByRole('button', { name: 'Orqaga' })).toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: "Sahifa yo'li" })).toHaveTextContent('Bosh sahifa')
    expect(screen.getByText('Hozircha yo\'nalishlar yo\'q.')).toBeInTheDocument()
  })
})
