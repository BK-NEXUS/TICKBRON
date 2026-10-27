import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, act } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { LoginPage } from './LoginPage'
import { RegisterPage } from './RegisterPage'
import { ForgotPasswordPage } from './ForgotPasswordPage'
import { AuthProvider } from '../contexts/AuthContext'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: {
    login: vi.fn(),
    register: vi.fn(),
    requestPasswordReset: vi.fn(),
    getCurrentUser: vi.fn().mockResolvedValue({ success: false }),
  },
}))

async function open(page: React.ReactElement) {
  const view = render(
    <AuthProvider>
      <MemoryRouter>{page}</MemoryRouter>
    </AuthProvider>
  )
  await act(async () => {})
  return view
}

const submit = (container: HTMLElement) => {
  fireEvent.submit(container.querySelector('form') as HTMLFormElement)
}

const type = (label: RegExp | string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } })

// QA F11: the browser's own "Please fill out this field." follows the browser's language, not the site's
describe('sign-in and sign-up forms word their own problems in the page language', () => {
  beforeEach(() => vi.clearAllMocks())

  it.each([
    ['login', <LoginPage />],
    ['register', <RegisterPage />],
    ['forgot password', <ForgotPasswordPage />],
  ])('the %s form leaves checking to the site', async (_name, page) => {
    const { container } = await open(page)
    expect(container.querySelector('form')).toHaveAttribute('novalidate')
  })

  it('login: empty fields get the site message and nothing is sent', async () => {
    const { container } = await open(<LoginPage />)
    submit(container)
    expect(await screen.findByRole('alert')).toHaveTextContent('Please fill in all the fields.')
    expect(authAdapter.login).not.toHaveBeenCalled()
  })

  it('login: a malformed address gets the e-mail message', async () => {
    const { container } = await open(<LoginPage />)
    type(/email/i, 'not-an-address')
    type(/^password/i, 'secret')
    submit(container)
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a valid email address.')
    expect(authAdapter.login).not.toHaveBeenCalled()
  })

  it('register: empty fields get the site message and nothing is sent', async () => {
    const { container } = await open(<RegisterPage />)
    submit(container)
    expect(await screen.findByRole('alert')).toHaveTextContent('Please fill in all the fields.')
    expect(authAdapter.register).not.toHaveBeenCalled()
  })

  it('forgot password: an empty or malformed address gets the site message', async () => {
    const { container } = await open(<ForgotPasswordPage />)
    submit(container)
    expect(await screen.findByRole('alert')).toHaveTextContent('Please fill in all the fields.')
    type(/email/i, 'nope')
    submit(container)
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter a valid email address.')
    expect(authAdapter.requestPasswordReset).not.toHaveBeenCalled()
  })
})
