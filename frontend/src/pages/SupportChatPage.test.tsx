import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import SupportChatPage from './SupportChatPage'
import { useAuth } from '../contexts/AuthContext'
import { settle } from '../test/utils'

vi.mock('../adapters/chatAdapter', () => ({
  chatAdapter: {
    mine: () => ({
      load: vi.fn().mockResolvedValue({ data: { messages: [], unread: 0 }, error: null, code: null }),
      send: vi.fn(),
      markRead: vi.fn(),
    }),
  },
}))
vi.mock('../contexts/AuthContext', () => ({ useAuth: vi.fn() }))

const mockUseAuth = useAuth as ReturnType<typeof vi.fn>

const renderAt = (url: string) => render(<MemoryRouter initialEntries={[url]}><SupportChatPage /></MemoryRouter>)

describe('SupportChatPage', () => {
  beforeEach(() => vi.clearAllMocks())

  it('asks anonymous visitors to sign in', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: false, user: null })
    renderAt('/support')
    await settle()
    expect(screen.getByRole('link', { name: 'Sign In' })).toHaveAttribute('href', '/login')
    expect(screen.queryByLabelText('Your message')).not.toBeInTheDocument()
  })

  it('shows the chat to a guest without the advertising shortcut', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user: { id: 1, role: 'customer' } })
    renderAt('/support')
    await settle()
    expect(screen.getByRole('heading', { level: 1, name: 'Chat with TICKBRON' })).toBeInTheDocument()
    expect(screen.queryByText(/advertise your hotel/i)).not.toBeInTheDocument()
  })

  it('offers an owner the advertising request and fills the template', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user: { id: 2, role: 'hotel-owner' } })
    renderAt('/support?topic=ads')
    await settle()
    expect((screen.getByLabelText('Your message') as HTMLTextAreaElement).value).toContain('advertise my hotel')
  })

  it('links an owner to the advertising shortcut', async () => {
    mockUseAuth.mockReturnValue({ isAuthenticated: true, user: { id: 2, role: 'hotel-owner' } })
    renderAt('/support')
    await settle()
    expect(screen.getByRole('link', { name: /advertise your hotel/i })).toHaveAttribute('href', '/support?topic=ads')
  })
})
