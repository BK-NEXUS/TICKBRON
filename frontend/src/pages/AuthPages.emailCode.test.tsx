import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router'
import { LoginPage } from './LoginPage'
import { RegisterPage } from './RegisterPage'
import { AuthProvider } from '../contexts/AuthContext'
import { I18nProvider } from '../i18n/I18nContext'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    login: vi.fn(), register: vi.fn(), loginEmailCode: vi.fn(), resendLoginCode: vi.fn(),
    verifyRegistration: vi.fn(), resendRegistrationCode: vi.fn(),
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

const adapter = vi.mocked(authAdapter)
const USER = { id: 1, email: 'guest@example.com' } as never

async function renderAt(path: string) {
  localStorage.setItem('tickbron.language', 'en')
  render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={[path]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/" element={<div>Home page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  )
  await act(async () => {})
}

describe('sign-in with a mailed code', () => {
  beforeEach(() => { vi.clearAllMocks() })

  async function passwordStep() {
    adapter.login.mockResolvedValue({ success: true, emailCodeRequired: true, emailHint: 'g***@example.com', resendAfter: 60 })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'guest@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Kitob7$yy' } })
    fireEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
    await screen.findByRole('heading', { name: 'Check your e-mail' })
  }

  it('shows the code step with the hint of the address and hides the password form', async () => {
    await renderAt('/login')
    await passwordStep()

    expect(screen.getByText(/g\*\*\*@example.com/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Password')).not.toBeInTheDocument()
  })

  it('signs in with the code and leaves the page', async () => {
    adapter.loginEmailCode.mockResolvedValue({ success: true, user: USER })
    await renderAt('/login')
    await passwordStep()
    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '123456' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm and sign in' }))

    expect(await screen.findByText('Home page')).toBeInTheDocument()
    expect(adapter.loginEmailCode).toHaveBeenCalledWith('123456')
  })

  it('shows the answer for a wrong code and stays', async () => {
    adapter.loginEmailCode.mockResolvedValue({ success: false, error: 'Invalid credentials.' })
    await renderAt('/login')
    await passwordStep()
    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '000000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm and sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials.')
    expect(screen.queryByText('Home page')).not.toBeInTheDocument()
  })

  it('goes back to the password form with the password cleared', async () => {
    await renderAt('/login')
    await passwordStep()
    fireEvent.click(screen.getAllByRole('button', { name: 'Back' }).at(-1) as HTMLElement)  // the page's own breadcrumb is also a Back

    expect(await screen.findByLabelText('Password')).toHaveValue('')
  })

  it('asks the server for a new code when the wait is over', async () => {
    adapter.resendLoginCode.mockResolvedValue({ success: true, emailCodeRequired: true, resendAfter: 60 })
    adapter.login.mockResolvedValue({ success: true, emailCodeRequired: true, emailHint: 'g***@example.com', resendAfter: 0 })
    await renderAt('/login')
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'guest@example.com' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Kitob7$yy' } })
    fireEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
    fireEvent.click(await screen.findByRole('button', { name: 'Send a new code' }))

    await waitFor(() => expect(adapter.resendLoginCode).toHaveBeenCalled())
  })
})

describe('sign-up with a mailed code', () => {
  beforeEach(() => { vi.clearAllMocks() })

  async function fillAndSubmit() {
    adapter.register.mockResolvedValue({ success: true, emailCodeRequired: true, email: 'new@example.com', resendAfter: 60 })
    fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'New Guest' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'new@example.com' } })
    fireEvent.change(screen.getByLabelText('Phone number'), { target: { value: '+998901234567' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Kitob7$yy' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'Kitob7$yy' } })
    fireEvent.click(screen.getByRole('button', { name: /^create account$/i }))
    await screen.findByRole('heading', { name: 'Check your e-mail' })
  }

  it('shows the code step with the address and keeps the confirm-password field on the form', async () => {
    await renderAt('/register')
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
    await fillAndSubmit()

    expect(screen.getByText(/new@example.com/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Full name')).not.toBeInTheDocument()
  })

  it('makes the account with the right code and leaves the page', async () => {
    adapter.verifyRegistration.mockResolvedValue({ success: true, user: USER })
    await renderAt('/register')
    await fillAndSubmit()
    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '654321' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm and create account' }))

    expect(await screen.findByText('Home page')).toBeInTheDocument()
    expect(adapter.verifyRegistration).toHaveBeenCalledWith('new@example.com', '654321')
  })

  it('shows the answer for a wrong code', async () => {
    adapter.verifyRegistration.mockResolvedValue({ success: false, error: 'The code is wrong or has expired.' })
    await renderAt('/register')
    await fillAndSubmit()
    fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value: '000000' } })
    fireEvent.click(screen.getByRole('button', { name: 'Confirm and create account' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('The code is wrong or has expired.')
  })

  it('goes back to the form with what was typed still in it', async () => {
    await renderAt('/register')
    await fillAndSubmit()
    fireEvent.click(screen.getAllByRole('button', { name: 'Back' }).at(-1) as HTMLElement)  // the page's own breadcrumb is also a Back

    expect(await screen.findByLabelText('Email')).toHaveValue('new@example.com')
  })

  it('still makes the account at once when the server does not ask for a code', async () => {
    adapter.register.mockResolvedValue({ success: true, user: USER })
    await renderAt('/register')
    fireEvent.change(screen.getByLabelText('Full Name'), { target: { value: 'New Guest' } })
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'new@example.com' } })
    fireEvent.change(screen.getByLabelText('Phone number'), { target: { value: '+998901234567' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'Kitob7$yy' } })
    fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: 'Kitob7$yy' } })
    fireEvent.click(screen.getByRole('button', { name: /^create account$/i }))

    expect(await screen.findByText('Home page')).toBeInTheDocument()
  })
})
