import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { AdminUserManagement } from './AdminUserManagement'
import { I18nProvider } from '../i18n/I18nContext'
import { adminAdapter, type AdminUser } from '../adapters/adminAdapter'
import { useAuth } from '../contexts/AuthContext'

vi.mock('../adapters/adminAdapter', () => ({
  adminAdapter: { getUsers: vi.fn(), resetTwoFactor: vi.fn() },
}))
vi.mock('../contexts/AuthContext', () => ({ useAuth: vi.fn() }))

const getUsers = vi.mocked(adminAdapter.getUsers)
const resetTwoFactor = vi.mocked(adminAdapter.resetTwoFactor)

const account = (extra: Partial<AdminUser>): AdminUser => ({
  id: 1, email: 'a@example.com', first_name: 'A', last_name: 'B', full_name: 'A B', is_active: true, is_staff: false,
  is_superuser: false, role: '', date_joined: '2026-01-01T00:00:00Z', two_factor_enabled: false, ...extra,
})

const MODERATOR = account({ id: 2, email: 'moderator@example.com', full_name: 'Moderator', is_staff: true, two_factor_enabled: true })
const BOSS = account({ id: 3, email: 'boss@example.com', full_name: 'Boss', is_staff: true, is_superuser: true, two_factor_enabled: true })
const GUEST = account({ id: 4, email: 'guest@example.com', full_name: 'Guest' })

function renderList(viewer: { is_superuser: boolean }) {
  vi.mocked(useAuth).mockReturnValue({ user: { id: 99, ...viewer } } as never)
  render(<I18nProvider><AdminUserManagement /></I18nProvider>)
}

const card = (email: string) => screen.getByText(email).closest('.user-card') as HTMLElement

describe('AdminUserManagement two-step sign-in', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getUsers.mockResolvedValue({ data: [MODERATOR, BOSS, GUEST], error: null })
  })

  it('shows on every account whether two-step sign-in is on', async () => {
    renderList({ is_superuser: true })
    await screen.findByText('moderator@example.com')

    expect(within(card('moderator@example.com')).getByText('Two-step sign-in: on')).toBeInTheDocument()
    expect(within(card('guest@example.com')).getByText('Two-step sign-in: off')).toBeInTheDocument()
  })

  it('offers the reset to a super admin only for accounts that have it on and are not super admins', async () => {
    renderList({ is_superuser: true })
    await screen.findByText('moderator@example.com')

    expect(within(card('moderator@example.com')).getByRole('button', { name: 'Reset two-step sign-in' })).toBeInTheDocument()
    expect(within(card('boss@example.com')).queryByRole('button', { name: 'Reset two-step sign-in' })).not.toBeInTheDocument()
    expect(within(card('guest@example.com')).queryByRole('button', { name: 'Reset two-step sign-in' })).not.toBeInTheDocument()
  })

  it('does not offer the reset to staff', async () => {
    renderList({ is_superuser: false })
    await screen.findByText('moderator@example.com')

    expect(screen.queryByRole('button', { name: 'Reset two-step sign-in' })).not.toBeInTheDocument()
  })

  it('asks for the super admin\'s own code, then resets and shows the account as off', async () => {
    resetTwoFactor.mockResolvedValue({ data: { ...MODERATOR, two_factor_enabled: false }, error: null })
    renderList({ is_superuser: true })
    await screen.findByText('moderator@example.com')

    fireEvent.click(within(card('moderator@example.com')).getByRole('button', { name: 'Reset two-step sign-in' }))
    fireEvent.change(screen.getByLabelText('Your own 6-digit code'), { target: { value: '123456' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }))

    await waitFor(() => expect(resetTwoFactor).toHaveBeenCalledWith(2, '123456'))
    expect(await screen.findByRole('status')).toHaveTextContent('Two-step sign-in was reset for moderator@example.com.')
    expect(within(card('moderator@example.com')).getByText('Two-step sign-in: off')).toBeInTheDocument()
  })

  it('does not call the server without a code', async () => {
    renderList({ is_superuser: true })
    await screen.findByText('moderator@example.com')

    fireEvent.click(within(card('moderator@example.com')).getByRole('button', { name: 'Reset two-step sign-in' }))
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter your own 6-digit code.')
    expect(resetTwoFactor).not.toHaveBeenCalled()
  })

  it('shows the refusal and keeps the account as it was', async () => {
    resetTwoFactor.mockResolvedValue({ data: null, error: 'Enter your own current two-step code.' })
    renderList({ is_superuser: true })
    await screen.findByText('moderator@example.com')

    fireEvent.click(within(card('moderator@example.com')).getByRole('button', { name: 'Reset two-step sign-in' }))
    fireEvent.change(screen.getByLabelText('Your own 6-digit code'), { target: { value: '000000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Reset' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter your own current two-step code.')
    expect(within(card('moderator@example.com')).getByText('Two-step sign-in: on')).toBeInTheDocument()
  })

  it('closes the question with Cancel', async () => {
    renderList({ is_superuser: true })
    await screen.findByText('moderator@example.com')

    fireEvent.click(within(card('moderator@example.com')).getByRole('button', { name: 'Reset two-step sign-in' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))

    expect(screen.queryByLabelText('Your own 6-digit code')).not.toBeInTheDocument()
  })
})
