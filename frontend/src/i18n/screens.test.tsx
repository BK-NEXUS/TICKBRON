import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
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
import { RoomSelection } from '../components/RoomSelection'
import { DateRangeCalendar } from '../components/DateRangeCalendar'
import { PropertyPoliciesDetail } from '../components/PropertyPoliciesDetail'
import { PropertyAmenitiesDetail } from '../components/PropertyAmenitiesDetail'
import { RatePlanCard } from '../components/RatePlanCard'
import { FavoriteButton } from '../components/FavoriteButton'
import { PropertyDetailPage } from '../pages/PropertyDetailPage'
import { ReviewForm } from '../components/ReviewForm'
import { ReviewCard } from '../components/ReviewCard'
import { RatingBreakdown } from '../components/RatingBreakdown'
import type { Language } from './options'

// Each migrated screen is rendered in Uzbek and Russian: a string left in English shows up here.
vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { getCurrentUser: vi.fn().mockResolvedValue({ success: false }) },
}))
vi.mock('../adapters/propertyAdapter', () => ({
  propertyAdapter: {
    getFilterOptions: vi.fn().mockResolvedValue({ data: { property_types: [], features: [], amenities: [] } }),
    searchProperties: vi.fn().mockResolvedValue({ data: { results: [], count: 0 } }),
    getPropertyById: vi.fn().mockResolvedValue({ error: 'Property not found' }),
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

  it('room selection and rate plan card in Russian', async () => {
    const room = {
      id: 1, name: 'Deluxe', description: '', base_price: 450000, currency: 'UZS', base_occupancy: 2,
      max_occupancy: 3, bed_configuration: '1 king', room_size: 30, total_rooms: 4, rate_plans: [],
    }
    await renderIn('ru', <RoomSelection roomTypes={[room] as never} propertyId={1} />)
    expect(screen.getByRole('heading', { name: 'Выберите номер' })).toBeInTheDocument()
    expect(screen.getByText('Вместимость')).toBeInTheDocument()
    expect(screen.getByText('2–3 чел.')).toBeInTheDocument()
    expect(screen.getByText('за ночь')).toBeInTheDocument()
  })

  it('rate plan card: night plurals in Russian', async () => {
    const plan = {
      id: 1, name: 'Flex', rate_type: 'early_bird', description: '', base_price: 100, currency: 'USD',
      min_nights: 2, max_nights: 21, cancellation_policy: '', advance_booking_days: 5,
    }
    await renderIn('ru', <RatePlanCard ratePlan={plan as never} isSelected />)
    expect(screen.getByText('Раннее бронирование')).toBeInTheDocument()
    expect(screen.getByText('2 ночи')).toBeInTheDocument()
    expect(screen.getByText('21 ночь')).toBeInTheDocument()
    expect(screen.getByText('5 дней')).toBeInTheDocument()
    expect(screen.getByText('Выбрано')).toBeInTheDocument()
  })

  it('calendar weekdays and month in the page language', async () => {
    await renderIn('ru', <DateRangeCalendar checkIn="2026-10-05" checkOut={null} onChange={() => {}} />)
    expect(screen.getByRole('heading', { level: 3 })).toHaveTextContent('октябрь 2026')
    expect(screen.getByText('пн')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Предыдущий месяц' })).toBeInTheDocument()
  })

  it('policies, amenities and the favourite heart in Uzbek', async () => {
    await renderIn('uz', (
      <>
        <PropertyPoliciesDetail policies={[{ policy_type: 'cancellation', title: 'Flex', description: 'x', is_strict: true }] as never} />
        <PropertyAmenitiesDetail amenities={[]} />
        <FavoriteButton propertyId={1} propertyName="Hotel" />
      </>
    ))
    expect(screen.getByRole('heading', { name: 'Qoidalar' })).toBeInTheDocument()
    expect(screen.getByText('Bekor qilish qoidalari')).toBeInTheDocument()
    expect(screen.getByText("Qulayliklar haqida ma'lumot yo'q")).toBeInTheDocument()
    expect(screen.getByRole('button', { name: "Hotel ni sevimlilarga qo'shish" })).toBeInTheDocument()
  })

  it('property page error state in Russian', async () => {
    localStorage.setItem('tickbron.language', 'ru')
    render(
      <I18nProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={['/property/9']}>
            <Routes><Route path="/property/:id" element={<PropertyDetailPage />} /></Routes>
          </MemoryRouter>
        </AuthProvider>
      </I18nProvider>,
    )
    expect(await screen.findByRole('heading', { name: 'Объект не найден' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Вернуться к результатам поиска' })).toBeInTheDocument()
  })

  it('review form in Uzbek', async () => {
    await renderIn('uz', <ReviewForm propertyId={1} bookingId={2} onCancel={() => {}} />)
    expect(screen.getByRole('heading', { name: 'Sharh yozish' })).toBeInTheDocument()
    expect(screen.getAllByLabelText(/^Umumiy baho: \d yulduz$/)).toHaveLength(5)
    expect(screen.getByLabelText('Sarlavha (ixtiyoriy)')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Bekor qilish' })).toBeInTheDocument()
  })

  it('review card date and rating breakdown plurals in Russian', async () => {
    const review = { id: 1, overall_rating: 4, created_at: '2026-10-09T10:00:00Z', status: 'pending', cleanliness_rating: 5 }
    await renderIn('ru', (
      <>
        <ReviewCard review={review as never} />
        <RatingBreakdown propertyScores={{ average_rating: 4.5, total_reviews: 22, category_scores: { cleanliness_rating: 4.5 } } as never} />
      </>
    ))
    expect(screen.getByText('9 октября 2026 г.')).toBeInTheDocument()
    expect(screen.getByText('Ожидает одобрения')).toBeInTheDocument()
    expect(screen.getByText('22 отзыва')).toBeInTheDocument()
    expect(screen.getAllByText('Чистота').length).toBeGreaterThan(0)
  })
})
