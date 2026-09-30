/**
 * Every admin screen shows exactly one breadcrumb: the layout's (Back + Home › ...).
 * The admin dashboard used to render a second, older one-level breadcrumb under its nav.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { BreadcrumbProvider, Breadcrumbs } from '../components/Breadcrumbs'
import { AdminDashboardPage } from './AdminDashboardPage'
import { SupportLookupPage } from './SupportLookupPage'
import AdminCustomerProfile from '../components/AdminCustomerProfile'
import { settle } from '../test/utils'

const { admin, adapterStub } = vi.hoisted(() => {
  // Every adapter call answers with an error, so each screen renders without data
  const failing = () => vi.fn().mockResolvedValue({ data: null, error: 'Not loaded in this test' })
  return {
    admin: {
      id: 1, email: 'admin@example.com', first_name: 'Admin', last_name: 'User', full_name: 'Admin User',
      is_staff: true, is_superuser: true, is_active: true, date_joined: '2024-01-01T00:00:00Z',
    },
    adapterStub: () => new Proxy({} as Record<string, unknown>, {
      get: (target, key: string) => (target[key] ??= failing()),
    }),
  }
})

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: admin, isAuthenticated: true, isLoading: false }),
}))
vi.mock('../adapters/adminAdapter', () => ({ adminAdapter: adapterStub() }))
vi.mock('../adapters/statusAdapter', () => ({ statusAdapter: adapterStub() }))

function renderAt(path: string) {
  render(
    <MemoryRouter initialEntries={[path]}>
      <BreadcrumbProvider>
        <Breadcrumbs />
        <Routes>
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/admin/support" element={<SupportLookupPage />} />
          <Route path="/admin/customers/:customerId" element={<AdminCustomerProfile />} />
        </Routes>
      </BreadcrumbProvider>
    </MemoryRouter>,
  )
}

const breadcrumbs = () => screen.getAllByRole('navigation', { name: 'Breadcrumb' })
// Older nav items start with an emoji icon: match the label at the end of the name
const navButton = (label: string) => screen.getByRole('button', { name: new RegExp(`(^|\\s)${label}$`) })

describe('admin pages have exactly one breadcrumb', () => {
  beforeEach(() => vi.clearAllMocks())

  it.each(['Properties', 'Amenities', 'Users', 'Customers', 'Statistics', 'Status'])(
    'dashboard view: %s', async (view) => {
      renderAt('/admin')
      await settle()
      fireEvent.click(navButton(view))
      await settle()
      await waitFor(() => expect(breadcrumbs()).toHaveLength(1))
      expect(breadcrumbs()[0].textContent).toContain('Admin Dashboard')
    })

  it('Status screens: countries list', async () => {
    renderAt('/admin')
    await settle()
    fireEvent.click(navButton('Status'))
    fireEvent.click(screen.getByRole('button', { name: /^Countries/ }))
    await screen.findByRole('alert')
    expect(breadcrumbs()).toHaveLength(1)
    expect(breadcrumbs()[0].textContent).toContain('Admin Dashboard›Status›Countries')
  })

  it('Create Owner', async () => {
    renderAt('/admin')
    await settle()
    fireEvent.click(navButton('Create Owner'))
    await settle()
    await waitFor(() => expect(breadcrumbs()).toHaveLength(1))
  })

  it('Support lookup page', async () => {
    renderAt('/admin/support')
    await settle()
    await waitFor(() => expect(breadcrumbs()).toHaveLength(1))
    expect(breadcrumbs()[0].textContent).toContain('Support Lookup')
  })

  it('Customer profile page', async () => {
    renderAt('/admin/customers/5')
    await settle()
    await waitFor(() => expect(breadcrumbs()).toHaveLength(1))
    expect(breadcrumbs()[0].textContent).toContain('Customer')
  })
})
