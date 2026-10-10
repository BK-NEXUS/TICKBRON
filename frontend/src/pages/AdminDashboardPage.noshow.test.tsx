import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { AdminDashboardPage } from './AdminDashboardPage'
import { useAuth } from '../contexts/AuthContext'
import { noShowAdapter } from '../adapters/noShowAdapter'

vi.mock('../contexts/AuthContext')
vi.mock('../adapters/noShowAdapter', () => ({
  noShowAdapter: { listReports: vi.fn() },
}))

const admin = {
  id: 1, email: 'admin@example.com', first_name: 'Admin', last_name: 'User', full_name: 'Admin User',
  is_staff: true, is_superuser: true, is_active: true, date_joined: '2024-01-01T00:00:00Z',
}

describe('AdminDashboardPage no-show reports', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(noShowAdapter.listReports).mockResolvedValue({
      data: { count: 0, next: null, previous: null, results: [] }, error: null, code: null, fieldErrors: null,
    })
  })

  it.each([
    ['super-admin', admin],
    ['staff', { ...admin, is_superuser: false }],
  ])('%s can open the no-show queue from the navigation', async (_name, user) => {
    vi.mocked(useAuth).mockReturnValue({ user, isAuthenticated: true } as unknown as ReturnType<typeof useAuth>)
    render(
      <MemoryRouter>
        <AdminDashboardPage />
      </MemoryRouter>,
    )
    const nav = screen.getByRole('button', { name: 'No-show reports' })
    expect(nav.textContent).toBe('No-show reports')
    fireEvent.click(nav)
    expect(nav).toHaveAttribute('aria-current', 'page')
    expect(await screen.findByText('No reports here.')).toBeInTheDocument()
  })
})
