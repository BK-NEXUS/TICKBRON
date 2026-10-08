import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { act, render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { RegisterPage } from './RegisterPage'
import { AuthProvider } from '../contexts/AuthContext'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    login: vi.fn(),
    register: vi.fn(),
    requestOTP: vi.fn(),
    verifyOTP: vi.fn(),
    getCurrentUser: vi.fn(),
  },
}))

const user = { id: 1, email: 'guest@example.com', full_name: 'Guest', phone_number: '+998901234567', role: 'guest' }

async function renderAt(path: string) {
  const result = render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<div>Home</div>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>
  )
  await act(async () => {})
  return result
}

describe('auth pages', () => {
  beforeEach(() => {
    vi.mocked(authAdapter.getCurrentUser).mockResolvedValue({ success: false })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it.each(['/login', '/register'])('redirects a logged-in user from %s without console errors', async (path) => {
    vi.mocked(authAdapter.getCurrentUser).mockResolvedValue({ success: true, user } as never)
    const errors = vi.spyOn(console, 'error').mockImplementation(() => {})

    await renderAt(path)

    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(errors).not.toHaveBeenCalled()
  })

  it.each(['/login', '/register'])('puts the form in one centred card on %s', async (path) => {
    const { container } = await renderAt(path)
    expect(container.querySelectorAll('.auth-container')).toHaveLength(1)
    expect(container.querySelector('.auth-container')?.closest('.container')).not.toBeNull()
  })

  it('switches between sign in and create account', async () => {
    await renderAt('/login')
    expect(screen.getByRole('tab', { name: 'Log in' })).toHaveAttribute('aria-selected', 'true')
    fireEvent.click(screen.getByRole('tab', { name: 'Register' }))
    expect(await screen.findByRole('heading', { name: 'Create Account' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Register' })).toHaveAttribute('aria-selected', 'true')
    fireEvent.click(screen.getByRole('tab', { name: 'Log in' }))
    expect(await screen.findByRole('heading', { name: 'Welcome Back' })).toBeInTheDocument()
  })

  it('lets the keyboard reach the password visibility toggle and names it', async () => {
    await renderAt('/login')
    const toggle = screen.getByRole('button', { name: 'Show password' })
    expect(toggle).not.toHaveAttribute('tabindex', '-1')
    fireEvent.click(toggle)
    expect(screen.getByLabelText('Password')).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: 'Hide password' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('shows the submit button as busy while signing in', async () => {
    vi.mocked(authAdapter.login).mockReturnValue(new Promise(() => {}))
    await renderAt('/login')
    fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'a@b.co' } })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'secret-pass-123' } })
    await act(async () => { fireEvent.submit(screen.getByRole('button', { name: 'Sign In' }).closest('form')!) })
    expect(screen.getByRole('button', { name: /signing in/i })).toHaveAttribute('aria-busy', 'true')
  })

  it('keeps the register fields as they are: name, email, phone and both passwords are required', async () => {
    await renderAt('/register')
    for (const label of ['Full Name', 'Email', 'Phone Number', 'Password', 'Confirm Password']) {
      expect(screen.getByLabelText(label)).toBeRequired()
    }
  })
})
