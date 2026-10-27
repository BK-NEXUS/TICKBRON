import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { ChatThread } from './ChatThread'
import type { ChatApi, ChatMessage } from '../adapters/chatAdapter'

const message = (id: number, from_staff: boolean, text = `m${id}`): ChatMessage => ({ id, text, from_staff, created_at: '2026-10-20T09:00:00Z' })
const ok = <T,>(data: T) => ({ data, error: null, code: null })

function makeApi(overrides: Partial<ChatApi> = {}): ChatApi {
  return {
    load: vi.fn().mockResolvedValue(ok({ messages: [], unread: 0 })),
    send: vi.fn(),
    markRead: vi.fn().mockResolvedValue(null),
    ...overrides,
  }
}

const flush = () => act(async () => { await Promise.resolve() })

describe('ChatThread', () => {
  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('shows the empty text when there are no messages', async () => {
    render(<ChatThread api={makeApi()} side="guest" emptyText="Nothing yet" />)
    await flush()
    expect(screen.getByText('Nothing yet')).toBeInTheDocument()
  })

  it('shows messages and marks the thread read when the other side wrote', async () => {
    const api = makeApi({ load: vi.fn().mockResolvedValue(ok({ messages: [message(1, true, 'Hello guest')] })) })
    const onSeen = vi.fn()
    render(<ChatThread api={api} side="guest" onSeen={onSeen} emptyText="-" />)
    await flush()
    expect(screen.getByText('Hello guest')).toBeInTheDocument()
    expect(api.markRead).toHaveBeenCalledTimes(1)
    expect(onSeen).toHaveBeenCalled()
  })

  it('does not mark read when only the own side wrote', async () => {
    const api = makeApi({ load: vi.fn().mockResolvedValue(ok({ messages: [message(1, false, 'mine')] })) })
    render(<ChatThread api={api} side="guest" emptyText="-" />)
    await flush()
    expect(api.markRead).not.toHaveBeenCalled()
  })

  it('asks only for newer messages on the next poll', async () => {
    const load = vi.fn()
      .mockResolvedValueOnce(ok({ messages: [message(5, true)] }))
      .mockResolvedValue(ok({ messages: [message(6, true, 'new one')] }))
    render(<ChatThread api={makeApi({ load })} side="guest" emptyText="-" />)
    await flush()
    await act(async () => { await vi.advanceTimersByTimeAsync(4000) })
    expect(load).toHaveBeenLastCalledWith(5)
    expect(screen.getByText('new one')).toBeInTheDocument()
  })

  it('backs off after a failed poll and says so', async () => {
    const load = vi.fn().mockResolvedValue({ data: null, error: 'x', code: null })
    render(<ChatThread api={makeApi({ load })} side="guest" emptyText="-" />)
    await flush()
    expect(screen.getByRole('alert')).toHaveTextContent('cannot be loaded')
    await act(async () => { await vi.advanceTimersByTimeAsync(4000) })
    expect(load).toHaveBeenCalledTimes(1)
    await act(async () => { await vi.advanceTimersByTimeAsync(4000) })
    expect(load).toHaveBeenCalledTimes(2)
  })

  it('sends a trimmed message, shows it and clears the box', async () => {
    const send = vi.fn().mockResolvedValue(ok(message(9, false, 'Hi team')))
    render(<ChatThread api={makeApi({ send })} side="guest" emptyText="-" />)
    await flush()
    fireEvent.change(screen.getByLabelText('Your message'), { target: { value: '  Hi team  ' } })
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /send/i })) })
    expect(send).toHaveBeenCalledWith('Hi team')
    expect(screen.getByText('Hi team')).toBeInTheDocument()
    expect(screen.getByLabelText('Your message')).toHaveValue('')
  })

  it('keeps the text and shows the translated reason when sending fails', async () => {
    const send = vi.fn().mockResolvedValue({ data: null, error: 'x', code: 'too_long' })
    render(<ChatThread api={makeApi({ send })} side="guest" emptyText="-" />)
    await flush()
    fireEvent.change(screen.getByLabelText('Your message'), { target: { value: 'long' } })
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: /send/i })) })
    expect(screen.getByRole('alert')).toHaveTextContent('too long')
    expect(screen.getByLabelText('Your message')).toHaveValue('long')
  })

  it('does not send an empty message', async () => {
    const send = vi.fn()
    render(<ChatThread api={makeApi({ send })} side="guest" emptyText="-" />)
    await flush()
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('puts the team side own messages on the right', async () => {
    const api = makeApi({ load: vi.fn().mockResolvedValue(ok({ messages: [message(1, true, 'staff says')] })) })
    render(<ChatThread api={api} side="team" emptyText="-" />)
    await flush()
    expect(screen.getByText('staff says').closest('.chat-bubble')).toHaveClass('chat-bubble--mine')
  })

  it('starts with the given text', async () => {
    render(<ChatThread api={makeApi()} side="guest" emptyText="-" initialText="Template" />)
    await flush()
    expect(screen.getByLabelText('Your message')).toHaveValue('Template')
  })
})
