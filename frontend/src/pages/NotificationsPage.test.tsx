import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { NotificationsPage } from './NotificationsPage'
import { notificationAdapter, type AppNotification } from '../adapters/notificationAdapter'
import { useAuth } from '../contexts/AuthContext'
import { I18nProvider } from '../i18n/I18nContext'
import { settle } from '../test/utils'

vi.mock('../adapters/notificationAdapter')
vi.mock('../contexts/AuthContext', () => ({ useAuth: vi.fn() }))

const notice = (over: Partial<AppNotification>): AppNotification => ({
  id: 1, code: 'new_booking', params: { booking_id: 5, booking_reference: 'AB12CD', check_in: '2026-11-06', check_out: '2026-11-08' },
  title: 'New booking AB12CD', message: 'A guest booked 2026-11-06 - 2026-11-08 (booking AB12CD).',
  is_read: false, booking: 5, created_at: '2026-10-27T10:00:00Z', ...over,
})

function show() {
  return render(<MemoryRouter><I18nProvider><NotificationsPage /></I18nProvider></MemoryRouter>)
}

describe('NotificationsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('tickbron.language', 'en')
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, isLoading: false } as never)
    vi.mocked(notificationAdapter.list).mockResolvedValue({ data: { items: [notice({})], hasMore: false }, error: null })
    vi.mocked(notificationAdapter.markRead).mockResolvedValue({ data: notice({ is_read: true }), error: null })
    vi.mocked(notificationAdapter.markAllRead).mockResolvedValue({ data: { marked_as_read: 1 }, error: null })
  })

  it('asks a visitor to sign in', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: false, isLoading: false } as never)
    show()
    await settle()
    expect(screen.getByRole('heading', { level: 1, name: 'Sign in required' })).toBeInTheDocument()
    expect(notificationAdapter.list).not.toHaveBeenCalled()
  })

  it('shows the notice in the page language, from its code and params', async () => {
    show()
    expect(await screen.findByText('New booking AB12CD')).toBeInTheDocument()
    expect(screen.getByText('A guest booked 2026-11-06 - 2026-11-08 (booking AB12CD).')).toBeInTheDocument()
  })

  it('writes the notice in Uzbek when the page is in Uzbek', async () => {
    localStorage.setItem('tickbron.language', 'uz')
    show()
    expect(await screen.findByText('Yangi bron AB12CD')).toBeInTheDocument()
  })

  it('shows the English text of a code the site has no text for', async () => {
    vi.mocked(notificationAdapter.list).mockResolvedValue({
      data: { items: [notice({ code: 'something_new', title: 'Something new', message: 'Fallback words' })], hasMore: false },
      error: null,
    })
    show()
    expect(await screen.findByText('Fallback words')).toBeInTheDocument()
  })

  it('marks a notice as read when it is opened', async () => {
    show()
    fireEvent.click(await screen.findByRole('button', { name: /New booking AB12CD/ }))
    await waitFor(() => expect(notificationAdapter.markRead).toHaveBeenCalledWith(1))
  })

  it('does not ask the server again for a notice that is already read', async () => {
    vi.mocked(notificationAdapter.list).mockResolvedValue({ data: { items: [notice({ is_read: true })], hasMore: false }, error: null })
    show()
    fireEvent.click(await screen.findByRole('button', { name: /New booking AB12CD/ }))
    await settle()
    expect(notificationAdapter.markRead).not.toHaveBeenCalled()
  })

  it('marks everything as read with one button', async () => {
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Mark all as read' }))
    await waitFor(() => expect(notificationAdapter.markAllRead).toHaveBeenCalled())
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Mark all as read' })).not.toBeInTheDocument())
  })

  it('has an empty state', async () => {
    vi.mocked(notificationAdapter.list).mockResolvedValue({ data: { items: [], hasMore: false }, error: null })
    show()
    expect(await screen.findByText('No notifications yet')).toBeInTheDocument()
  })

  it('shows the error and lets the visitor try again', async () => {
    vi.mocked(notificationAdapter.list).mockResolvedValue({ data: null, error: 'Server down' })
    show()
    expect(await screen.findByRole('alert')).toHaveTextContent('Server down')
  })

  it('shows more notices when the server has another page, and hides the button at the end', async () => {
    vi.mocked(notificationAdapter.list)
      .mockResolvedValueOnce({ data: { items: [notice({ id: 1 })], hasMore: true }, error: null })
      .mockResolvedValueOnce({
        data: { items: [notice({ id: 2, params: { booking_id: 6, booking_reference: 'ZZ99YY', check_in: '2026-12-01', check_out: '2026-12-03' } })], hasMore: false },
        error: null,
      })
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Show more' }))

    expect(await screen.findByText('New booking ZZ99YY')).toBeInTheDocument()
    expect(notificationAdapter.list).toHaveBeenLastCalledWith(2)
    expect(screen.getByText('New booking AB12CD')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Show more' })).not.toBeInTheDocument()
  })

  it('has no Show more button when everything fits on the first page', async () => {
    show()
    await screen.findByText('New booking AB12CD')
    expect(screen.queryByRole('button', { name: 'Show more' })).not.toBeInTheDocument()
  })

  it('keeps the notices and shows the error when the next page fails', async () => {
    vi.mocked(notificationAdapter.list)
      .mockResolvedValueOnce({ data: { items: [notice({ id: 1 })], hasMore: true }, error: null })
      .mockResolvedValueOnce({ data: null, error: 'Server down' })
    show()
    fireEvent.click(await screen.findByRole('button', { name: 'Show more' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Server down')
    expect(screen.getByText('New booking AB12CD')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Show more' })).toBeInTheDocument()
  })
})
