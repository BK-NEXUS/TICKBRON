import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { LoginPage } from './LoginPage'
import { AuthProvider } from '../contexts/AuthContext'
import { I18nProvider } from '../i18n/I18nContext'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    login: vi.fn(),
    loginTwoFactor: vi.fn(),
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

const login = vi.mocked(authAdapter.login)
const loginTwoFactor = vi.mocked(authAdapter.loginTwoFactor)
const USER = { id: 1, email: 'admin@example.com', two_factor_enabled: true } as never

async function renderLogin() {
  render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/" element={<div>Home page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  )
  await act(async () => {})
}

async function passPasswordStep() {
  login.mockResolvedValue({ success: true, twoFactorRequired: true })
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'admin@example.com' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Kitob7$yy' } })
  fireEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
  await screen.findByRole('heading', { name: 'Two-step sign-in' })
}

describe('LoginPage two-step sign-in', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('asks for the app code after a right password and hides the password form', async () => {
    await renderLogin()
    await passPasswordStep()

    expect(screen.getByLabelText('6-digit code')).toBeInTheDocument()
    expect(screen.queryByLabelText('Password')).not.toBeInTheDocument()
    expect(screen.queryByText(/Don't have an account/)).not.toBeInTheDocument()
  })

  it('signs in with the code and leaves the login page', async () => {
    loginTwoFactor.mockResolvedValue({ success: true, user: USER })
    await renderLogin()
    await passPasswordStep()

    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '123456' } })
    fireEvent.click(screen.getByRole('button', { name: 'Verify' }))

    await waitFor(() => expect(document.body).toHaveTextContent('Home page'))
    expect(loginTwoFactor).toHaveBeenCalledWith({ code: '123456' })
  })

  it('shows the refusal and stays on the code step', async () => {
    loginTwoFactor.mockResolvedValue({ success: false, error: 'Invalid credentials.' })
    await renderLogin()
    await passPasswordStep()

    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '000000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Verify' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials.')
    expect(screen.getByLabelText('6-digit code')).toBeInTheDocument()
  })

  it('does not call the server with an empty code', async () => {
    await renderLogin()
    await passPasswordStep()

    fireEvent.click(screen.getByRole('button', { name: 'Verify' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the code.')
    expect(loginTwoFactor).not.toHaveBeenCalled()
  })

  it('switches to a backup code and sends it under its own name', async () => {
    loginTwoFactor.mockResolvedValue({ success: true, user: USER })
    await renderLogin()
    await passPasswordStep()

    fireEvent.click(screen.getByRole('button', { name: 'Use a backup code' }))
    fireEvent.change(screen.getByLabelText('Backup code'), { target: { value: 'ab12c-34d56' } })
    fireEvent.click(screen.getByRole('button', { name: 'Verify' }))

    await waitFor(() => expect(loginTwoFactor).toHaveBeenCalledWith({ backupCode: 'ab12c-34d56' }))
    expect(screen.queryByLabelText('6-digit code')).not.toBeInTheDocument()
  })

  it('goes back to the password form with the password cleared', async () => {
    await renderLogin()
    await passPasswordStep()

    fireEvent.click(screen.getByRole('button', { name: 'Back to sign in' }))

    expect(screen.getByLabelText('Password')).toHaveValue('')
    expect(screen.getByLabelText('Email')).toHaveValue('admin@example.com')
  })
})
