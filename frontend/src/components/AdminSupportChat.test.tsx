import { describe, it, expect, vi, beforeEach } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { AdminSupportChat } from './AdminSupportChat'
import { chatAdapter, type InboxRow } from '../adapters/chatAdapter'
import { settle } from '../test/utils'

vi.mock('../adapters/chatAdapter', () => ({
  chatAdapter: { inbox: vi.fn(), thread: vi.fn() },
}))

const adapter = chatAdapter as unknown as { inbox: ReturnType<typeof vi.fn>; thread: ReturnType<typeof vi.fn> }

const row = (id: number, name: string, unread = 0): InboxRow => ({
  id,
  user: { id, name, email: `${name.toLowerCase()}@example.com`, role: id === 2 ? 'hotel-owner' : 'customer' },
  last_message: { text: `hello from ${name}`, from_staff: false, created_at: '2026-10-20T09:00:00Z' },
  unread,
  last_message_at: '2026-10-20T09:00:00Z',
})

const page = (results: InboxRow[], next: string | null = null) => ({ data: { count: results.length, next, previous: null, results }, error: null, code: null })

describe('AdminSupportChat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    adapter.thread.mockReturnValue({
      load: vi.fn().mockResolvedValue({ data: { messages: [], user: undefined }, error: null, code: null }),
      send: vi.fn(),
      markRead: vi.fn().mockResolvedValue(null),
    })
  })

  it('lists conversations with the unread count and the role', async () => {
    adapter.inbox.mockResolvedValue(page([row(1, 'Alice', 3), row(2, 'Bob')]))
    render(<AdminSupportChat />)
    expect(await screen.findByText('Alice')).toBeInTheDocument()
    expect(screen.getByLabelText('Unread: 3')).toHaveTextContent('3')
    expect(screen.getByText('Hotel owner')).toBeInTheDocument()
    expect(screen.getByText('Guest')).toBeInTheDocument()
  })

  it('says so when there are no conversations', async () => {
    adapter.inbox.mockResolvedValue(page([]))
    render(<AdminSupportChat />)
    expect(await screen.findByText('No conversations.')).toBeInTheDocument()
  })

  it('shows an error when the inbox cannot be loaded', async () => {
    adapter.inbox.mockResolvedValue({ data: null, error: 'boom', code: null })
    render(<AdminSupportChat />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })

  it('opens a conversation and its chat window', async () => {
    adapter.inbox.mockResolvedValue(page([row(1, 'Alice', 1)]))
    render(<AdminSupportChat />)
    fireEvent.click(await screen.findByRole('button', { name: /Alice/ }))
    expect(adapter.thread).toHaveBeenCalledWith(1)
    expect(await screen.findByRole('heading', { level: 3, name: 'Alice' })).toBeInTheDocument()
    await settle()
  })

  it('searches by name or email and filters unread', async () => {
    adapter.inbox.mockResolvedValue(page([row(1, 'Alice')]))
    render(<AdminSupportChat />)
    await screen.findByText('Alice')
    fireEvent.change(screen.getByLabelText('Search by name or email'), { target: { value: 'ali' } })
    fireEvent.submit(screen.getByRole('search'))
    await waitFor(() => expect(adapter.inbox).toHaveBeenLastCalledWith({ q: 'ali', unread: false, page: 1 }))
    fireEvent.click(screen.getByLabelText('Only unread'))
    await waitFor(() => expect(adapter.inbox).toHaveBeenLastCalledWith({ q: 'ali', unread: true, page: 1 }))
  })

  it('pages through the inbox', async () => {
    adapter.inbox.mockResolvedValue(page([row(1, 'Alice')], 'next-url'))
    render(<AdminSupportChat />)
    await screen.findByText('Alice')
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    await waitFor(() => expect(adapter.inbox).toHaveBeenLastCalledWith({ q: '', unread: false, page: 2 }))
  })
})
