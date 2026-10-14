import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ForgotPasswordPage } from './ForgotPasswordPage'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { requestPasswordReset: vi.fn() },
}))

const requestPasswordReset = vi.mocked(authAdapter.requestPasswordReset)

const renderPage = () =>
  render(
    <MemoryRouter>
      <ForgotPasswordPage />
    </MemoryRouter>
  )

const submit = (email: string) => {
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: email } })
  fireEvent.click(screen.getByRole('button', { name: 'Send reset link' }))
}

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows the e-mail form with a way back to sign in', () => {
    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'Reset your password' })).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Back to sign in' })).toHaveAttribute('href', '/login')
  })

  it('asks for the link and then shows the same notice whatever the address', async () => {
    requestPasswordReset.mockResolvedValue({ success: true })
    renderPage()

    submit('guest@example.com')

    expect(await screen.findByRole('status')).toHaveTextContent('If this address is registered')
    expect(requestPasswordReset).toHaveBeenCalledWith('guest@example.com')
    expect(screen.queryByLabelText('Email')).not.toBeInTheDocument()
  })

  it('disables the form and shows progress while the request is running', async () => {
    let finish: (value: { success: boolean }) => void = () => {}
    requestPasswordReset.mockReturnValue(new Promise((resolve) => { finish = resolve }))
    renderPage()

    submit('guest@example.com')

    expect(await screen.findByRole('button', { name: 'Sending...' })).toBeDisabled()
    expect(screen.getByLabelText('Email')).toBeDisabled()
    finish({ success: true })
    await waitFor(() => expect(screen.getByRole('status')).toBeInTheDocument())
  })

  it('shows the error and keeps the form when the request fails', async () => {
    requestPasswordReset.mockResolvedValue({ success: false, error: 'Too many requests. Please wait a moment and try again.' })
    renderPage()

    submit('guest@example.com')

    expect(await screen.findByRole('alert')).toHaveTextContent('Too many requests')
    expect(screen.getByLabelText('Email')).toHaveValue('guest@example.com')
  })
})
