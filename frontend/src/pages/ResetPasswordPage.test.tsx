import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { ResetPasswordPage } from './ResetPasswordPage'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { confirmPasswordReset: vi.fn() },
}))

const confirmPasswordReset = vi.mocked(authAdapter.confirmPasswordReset)
const PASSWORD = 'Fresh9Grape#Tower42'

const renderPage = (query = '?uid=MQ&token=abc-123') =>
  render(
    <MemoryRouter initialEntries={[`/reset-password${query}`]}>
      <ResetPasswordPage />
    </MemoryRouter>
  )

const fill = (password: string, confirmation: string) => {
  fireEvent.change(screen.getByLabelText('New password'), { target: { value: password } })
  fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: confirmation } })
  fireEvent.click(screen.getByRole('button', { name: 'Save password' }))
}

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows the new password form for a link with uid and token', () => {
    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'Choose a new password' })).toBeInTheDocument()
    expect(screen.getByLabelText('New password')).toBeInTheDocument()
    expect(screen.getByText('Must be at least 12 characters')).toBeInTheDocument()
  })

  it('an empty password is reported by the site, not by the browser, and nothing is sent', () => {
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Save password' }))

    expect(screen.getByRole('alert')).toHaveTextContent('New password is required.')
    expect(confirmPasswordReset).not.toHaveBeenCalled()
  })

  it.each(['', '?uid=MQ', '?token=abc'])('shows the invalid-link state for "%s"', (query) => {
    renderPage(query)

    expect(screen.getByRole('alert')).toHaveTextContent('This link is invalid or has expired.')
    expect(screen.getByRole('link', { name: 'Request a new link' })).toHaveAttribute('href', '/forgot-password')
    expect(screen.queryByLabelText('New password')).not.toBeInTheDocument()
  })

  it('sends the uid, token and password and then offers to sign in', async () => {
    confirmPasswordReset.mockResolvedValue({ success: true })
    renderPage()

    fill(PASSWORD, PASSWORD)

    expect(await screen.findByRole('status')).toHaveTextContent('Your password was changed')
    expect(confirmPasswordReset).toHaveBeenCalledWith({
      uid: 'MQ', token: 'abc-123', password: PASSWORD, password_confirm: PASSWORD,
    })
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/login')
  })

  it('does not call the server when the two passwords differ or are too short', () => {
    renderPage()

    fill(PASSWORD, 'something else')
    expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match')

    fill('Short#1abc', 'Short#1abc')
    expect(screen.getByRole('alert')).toHaveTextContent('at least 12 characters')
    expect(confirmPasswordReset).not.toHaveBeenCalled()
  })

  it('shows the server message when the password breaks a rule and keeps the form', async () => {
    confirmPasswordReset.mockResolvedValue({ success: false, error: 'Password: Password contains common patterns and is not secure.' })
    renderPage()

    fill(PASSWORD, PASSWORD)

    expect(await screen.findByRole('alert')).toHaveTextContent('common patterns')
    expect(screen.getByLabelText('New password')).toBeInTheDocument()
  })

  it('switches to the invalid-link state when the server rejects the link', async () => {
    confirmPasswordReset.mockResolvedValue({ success: false, error: 'invalid', code: 'invalid_reset_link' })
    renderPage()

    fill(PASSWORD, PASSWORD)

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('This link is invalid or has expired.'))
    expect(screen.queryByLabelText('New password')).not.toBeInTheDocument()
  })
})
