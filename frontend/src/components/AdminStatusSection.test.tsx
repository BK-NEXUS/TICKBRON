import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { AdminStatusSection } from './AdminStatusSection'
import { BreadcrumbProvider, Breadcrumbs } from './Breadcrumbs'
import { statusAdapter } from '../adapters/statusAdapter'

vi.mock('../adapters/statusAdapter', () => ({
  statusAdapter: {
    getCountries: vi.fn(),
    getRegions: vi.fn(),
    getHotels: vi.fn(),
    getHotelDetail: vi.fn(),
    getUsers: vi.fn(),
  },
}))

const mocked = vi.mocked(statusAdapter)

const pageOf = <T,>(results: T[], extra: Record<string, unknown> = {}) => ({
  data: { count: results.length, next: null, previous: null, results, period: 'all', ...extra },
  error: null,
})

const COUNTRIES = [
  { rank: 1, country: 'Uzbekistan', hotels: 7, bookings: 1234, guests: 56,
    revenue: [{ currency: 'EUR', amount: '60.00' }, { currency: 'USD', amount: '98765.40' }] },
  { rank: 2, country: 'Kazakhstan', hotels: 2, bookings: 3, guests: 3, revenue: [{ currency: 'KZT', amount: '50000.00' }] },
]
const REGIONS = [
  { rank: 1, region: 'Tashkent', hotels: 3, bookings: 900, guests: 40, revenue: [{ currency: 'USD', amount: '70000.00' }] },
  { rank: 2, region: 'Unspecified', hotels: 1, bookings: 0, guests: 0, revenue: [] },
]
const HOTELS = [
  { rank: 1, id: 11, name: 'Alpha Hotel', city: 'Tashkent', status: 'active', bookings: 500, guests: 30,
    revenue: [{ currency: 'USD', amount: '45000.00' }] },
]
const months = Array.from({ length: 12 }, (_, i) => ({
  month: `2026-${String(i + 1).padStart(2, '0')}`,
  bookings: i === 3 ? 2 : 0,
  guests: i === 3 ? 2 : 0,
  revenue: i === 3 ? [{ currency: 'USD', amount: '350.00' }] : [],
}))
const DETAIL = {
  hotel: {
    id: 11, name: 'Alpha Hotel', status: 'active', address: '1 Alpha Street, Tashkent, Uzbekistan',
    city: 'Tashkent', region: 'Tashkent', country: 'Uzbekistan', registered_at: '2025-01-15T09:00:00Z',
    owner: { id: 5, name: 'Olim Owner', email: 'owner1@example.com', phone: '+998901111111' },
  },
  period: 'all',
  totals: { bookings: 1500, guests: 30, revenue: [{ currency: 'USD', amount: '45000.00' }] },
  year: 2026,
  available_years: [2025, 2026],
  monthly: months,
}

function renderSection(onExit = vi.fn()) {
  render(
    <MemoryRouter initialEntries={['/admin']}>
      <BreadcrumbProvider>
        <Breadcrumbs />
        <AdminStatusSection onExit={onExit} />
      </BreadcrumbProvider>
    </MemoryRouter>,
  )
  return { onExit }
}

const trailText = () => screen.getByRole('navigation', { name: 'Breadcrumb' }).textContent

async function openCountries() {
  fireEvent.click(screen.getByRole('button', { name: /Countries/ }))
  await screen.findByRole('button', { name: 'Uzbekistan' })
}

describe('AdminStatusSection', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    mocked.getCountries.mockResolvedValue(pageOf(COUNTRIES))
    mocked.getRegions.mockResolvedValue(pageOf(REGIONS, { country: 'Uzbekistan' }))
    mocked.getHotels.mockResolvedValue(pageOf(HOTELS, { country: 'Uzbekistan', region: 'Tashkent' }))
    mocked.getHotelDetail.mockResolvedValue({ data: DETAIL, error: null })
  })

  it('opens on the Countries tile', () => {
    renderSection()

    expect(screen.getByRole('heading', { name: 'Status' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Countries/ })).toBeInTheDocument()
    expect(trailText()).toContain('Admin Dashboard›Status')
    expect(mocked.getCountries).not.toHaveBeenCalled()
  })

  it('lists countries with thousand separators and per-currency revenue', async () => {
    renderSection()
    await openCountries()

    expect(mocked.getCountries).toHaveBeenCalledWith({ period: 'all', search: '', page: 1 })
    const row = screen.getByRole('button', { name: 'Uzbekistan' }).closest('tr')!
    expect(within(row).getByText('1,234')).toBeInTheDocument()
    expect(within(row).getByText('€60.00 · $98,765.40')).toBeInTheDocument()
    expect(trailText()).toContain('Status›Countries')
  })

  it('drills down country > region > hotel > detail with breadcrumbs', async () => {
    renderSection()
    await openCountries()

    fireEvent.click(screen.getByRole('button', { name: 'Uzbekistan' }))
    await screen.findByRole('button', { name: 'Tashkent' })
    expect(mocked.getRegions).toHaveBeenCalledWith('Uzbekistan', { period: 'all', search: '', page: 1 })
    expect(trailText()).toContain('Status›Countries›Uzbekistan')

    fireEvent.click(screen.getByRole('button', { name: 'Tashkent' }))
    await screen.findByRole('button', { name: 'Alpha Hotel' })
    expect(mocked.getHotels).toHaveBeenCalledWith('Uzbekistan', 'Tashkent', { period: 'all', search: '', page: 1 })

    fireEvent.click(screen.getByRole('button', { name: 'Alpha Hotel' }))
    await screen.findByRole('heading', { name: 'Alpha Hotel' })
    expect(trailText()).toContain('Status›Countries›Uzbekistan›Tashkent›Alpha Hotel')

    // A breadcrumb goes back to that level
    fireEvent.click(screen.getByRole('button', { name: 'Tashkent' }))
    expect(await screen.findByRole('button', { name: 'Alpha Hotel' })).toBeInTheDocument()
  })

  it('Back steps up one level', async () => {
    renderSection()
    await openCountries()
    fireEvent.click(screen.getByRole('button', { name: 'Uzbekistan' }))
    await screen.findByRole('button', { name: 'Tashkent' })

    fireEvent.click(screen.getByRole('button', { name: 'Back' }))

    expect(await screen.findByRole('button', { name: 'Uzbekistan' })).toBeInTheDocument()
  })

  it('Back from the tiles leaves the Status section', () => {
    const { onExit } = renderSection()
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(onExit).toHaveBeenCalled()
  })

  it('the period applies to the list and is kept while drilling down', async () => {
    renderSection()
    await openCountries()

    fireEvent.change(screen.getByLabelText('Period'), { target: { value: 'year' } })
    await waitFor(() => expect(mocked.getCountries).toHaveBeenLastCalledWith(
      expect.objectContaining({ period: String(new Date().getFullYear()), page: 1 })))

    fireEvent.click(await screen.findByRole('button', { name: 'Uzbekistan' }))
    await waitFor(() => expect(mocked.getRegions).toHaveBeenCalledWith(
      'Uzbekistan', expect.objectContaining({ period: String(new Date().getFullYear()) })))
  })

  it('searches only inside the current list, and a new level starts without a search', async () => {
    renderSection()
    await openCountries()

    fireEvent.change(screen.getByLabelText('Search countries'), { target: { value: 'kaz' } })
    await waitFor(() => expect(mocked.getCountries).toHaveBeenLastCalledWith({ period: 'all', search: 'kaz', page: 1 }))

    fireEvent.click(screen.getByRole('button', { name: 'Uzbekistan' }))
    await screen.findByRole('button', { name: 'Tashkent' })
    expect(screen.getByLabelText('Search regions')).toHaveValue('')
    expect(mocked.getRegions).toHaveBeenLastCalledWith('Uzbekistan', { period: 'all', search: '', page: 1 })
  })

  it('paginates', async () => {
    mocked.getCountries.mockResolvedValue({
      data: { count: 45, next: 'http://x/?page=2', previous: null, results: COUNTRIES, period: 'all' }, error: null,
    })
    renderSection()
    await openCountries()

    expect(screen.getByText('Page 1 of 3')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Next page' }))

    await waitFor(() => expect(mocked.getCountries).toHaveBeenLastCalledWith({ period: 'all', search: '', page: 2 }))
  })

  it('shows an empty state', async () => {
    mocked.getCountries.mockResolvedValue(pageOf([]))
    renderSection()
    fireEvent.click(screen.getByRole('button', { name: /Countries/ }))

    expect(await screen.findByText('No countries found for this period.')).toBeInTheDocument()
  })

  it('shows an error state', async () => {
    mocked.getCountries.mockResolvedValue({ data: null, error: 'Admin or staff role required' })
    renderSection()
    fireEvent.click(screen.getByRole('button', { name: /Countries/ }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Admin or staff role required')
  })

  it('hotel detail: info, owner, totals, year selector and monthly chart', async () => {
    renderSection()
    await openCountries()
    fireEvent.click(screen.getByRole('button', { name: 'Uzbekistan' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Tashkent' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Alpha Hotel' }))
    await screen.findByRole('heading', { name: 'Alpha Hotel' })

    expect(screen.getByText('1 Alpha Street, Tashkent, Uzbekistan')).toBeInTheDocument()
    expect(screen.getByText(/Olim Owner/)).toBeInTheDocument()
    expect(screen.getByText('+998901111111')).toBeInTheDocument()
    expect(screen.getByText('owner1@example.com')).toBeInTheDocument()
    expect(screen.getByText('1,500')).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /Revenue \(USD\) per month in 2026/ })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: /Guests per month in 2026/ })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Chart year'), { target: { value: '2025' } })
    await waitFor(() => expect(mocked.getHotelDetail).toHaveBeenLastCalledWith(11, { period: 'all', year: 2025 }))
  })

  describe('Users', () => {
    const USERS = [
      { rank: 1, id: 42, full_name: 'Madina Nazarova', first_name: 'Madina', last_name: 'Nazarova',
        phone: '+998903330002', email: 'guest2@example.com', bookings: 1250,
        total_spent: [{ currency: 'USD', amount: '12345.60' }], last_booking_date: '2026-04-12' },
    ]

    function renderWithProfileRoute() {
      render(
        <MemoryRouter initialEntries={['/admin']}>
          <BreadcrumbProvider>
            <Breadcrumbs />
            <Routes>
              <Route path="/admin" element={<AdminStatusSection onExit={vi.fn()} />} />
              <Route path="/admin/customers/:customerId" element={<h1>Customer profile page</h1>} />
            </Routes>
          </BreadcrumbProvider>
        </MemoryRouter>,
      )
    }

    beforeEach(() => {
      mocked.getUsers.mockResolvedValue(pageOf(USERS))
    })

    it('the home screen has a Users tile next to Countries', () => {
      renderSection()
      expect(screen.getByRole('button', { name: /Countries/ })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Users/ })).toBeInTheDocument()
    })

    it('lists guests with their numbers', async () => {
      renderSection()
      fireEvent.click(screen.getByRole('button', { name: /Users/ }))

      const link = await screen.findByRole('button', { name: 'Madina Nazarova' })
      const row = link.closest('tr')!
      expect(within(row).getByText('+998903330002')).toBeInTheDocument()
      expect(within(row).getByText('guest2@example.com')).toBeInTheDocument()
      expect(within(row).getByText('1,250')).toBeInTheDocument()
      expect(within(row).getByText('$12,345.60')).toBeInTheDocument()
      expect(within(row).getByText('Apr 12, 2026')).toBeInTheDocument()
      expect(mocked.getUsers).toHaveBeenCalledWith({ period: 'all', search: '', page: 1 })
      expect(trailText()).toContain('Status›Users')
    })

    it('searches users', async () => {
      renderSection()
      fireEvent.click(screen.getByRole('button', { name: /Users/ }))
      await screen.findByRole('button', { name: 'Madina Nazarova' })

      fireEvent.change(screen.getByLabelText('Search users'), { target: { value: '99890333' } })

      await waitFor(() => expect(mocked.getUsers).toHaveBeenLastCalledWith({ period: 'all', search: '99890333', page: 1 }))
    })

    it('clicking a row opens the existing customer profile', async () => {
      renderWithProfileRoute()
      fireEvent.click(screen.getByRole('button', { name: /Users/ }))
      const row = (await screen.findByRole('button', { name: 'Madina Nazarova' })).closest('tr')!

      fireEvent.click(within(row).getByText('guest2@example.com'))

      expect(await screen.findByRole('heading', { name: 'Customer profile page' })).toBeInTheDocument()
    })
  })
})
