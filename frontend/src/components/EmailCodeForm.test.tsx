import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import { EmailCodeForm } from './EmailCodeForm'
import { I18nProvider } from '../i18n/I18nContext'
import type { AuthResponse } from '../adapters/authAdapter'

const ok: AuthResponse = { success: true }

function show(overrides: Partial<React.ComponentProps<typeof EmailCodeForm>> = {}) {
  const props = {
    sentTo: 'o***@gmail.com', purpose: 'login' as const, resendAfter: 60,
    onSubmit: vi.fn().mockResolvedValue(ok), onResend: vi.fn().mockResolvedValue({ success: true, resendAfter: 60 }),
    onSuccess: vi.fn(), onBack: vi.fn(), ...overrides,
  }
  localStorage.setItem('tickbron.language', 'en')
  render(<I18nProvider><EmailCodeForm {...props} /></I18nProvider>)
  return props
}

const typeCode = (value: string) => fireEvent.change(screen.getByLabelText('6-digit code'), { target: { value } })
const submit = () => fireEvent.click(screen.getByRole('button', { name: /Confirm and/ }))

describe('EmailCodeForm', () => {
  beforeEach(() => { vi.clearAllMocks() })
  afterEach(() => { vi.useRealTimers() })

  it('says where the code went and asks for six digits', () => {
    show()
    expect(screen.getByText(/o\*\*\*@gmail.com/)).toBeInTheDocument()
    const field = screen.getByLabelText('6-digit code')
    expect(field).toHaveAttribute('inputmode', 'numeric')
    expect(field).toHaveAttribute('autocomplete', 'one-time-code')
    expect(field).toHaveAttribute('maxlength', '6')
  })

  it('uses the words of sign-up and of sign-in', () => {
    show({ purpose: 'register', sentTo: 'new@example.com' })
    expect(screen.getByRole('button', { name: 'Confirm and create account' })).toBeInTheDocument()
    expect(screen.getByText(/create your account/)).toBeInTheDocument()
  })

  it('keeps only digits and at most six of them', () => {
    show()
    typeCode('12a3 4-5678')
    expect(screen.getByLabelText('6-digit code')).toHaveValue('123456')
  })

  it('refuses a short code without asking the server', async () => {
    const props = show()
    typeCode('123')
    submit()
    expect(await screen.findByRole('alert')).toHaveTextContent('Enter the 6 digits from the e-mail.')
    expect(props.onSubmit).not.toHaveBeenCalled()
  })

  it('sends the six digits and calls onSuccess when the server accepts them', async () => {
    const props = show()
    typeCode('123456')
    submit()
    await waitFor(() => expect(props.onSubmit).toHaveBeenCalledWith('123456'))
    await waitFor(() => expect(props.onSuccess).toHaveBeenCalled())
  })

  it('shows the server answer for a wrong code and stays on the step', async () => {
    const props = show({ onSubmit: vi.fn().mockResolvedValue({ success: false, error: 'The code is wrong or has expired.' }) })
    typeCode('123456')
    submit()
    expect(await screen.findByRole('alert')).toHaveTextContent('The code is wrong or has expired.')
    expect(props.onSuccess).not.toHaveBeenCalled()
  })

  it('falls back to its own words when the server gives no text', async () => {
    show({ onSubmit: vi.fn().mockResolvedValue({ success: false }) })
    typeCode('123456')
    submit()
    expect(await screen.findByRole('alert')).toHaveTextContent('The code is wrong or has expired.')
  })

  it('does not let a new code be asked for before the wait is over, then counts down to it', async () => {
    vi.useFakeTimers()
    const props = show({ resendAfter: 3 })
    const resend = () => screen.getByRole('button', { name: /new code/i })
    expect(resend()).toBeDisabled()
    expect(resend()).toHaveTextContent('Send a new code in 3 s')
    for (let second = 0; second < 4; second += 1) {
      await act(async () => { await vi.advanceTimersByTimeAsync(1000) })
    }
    expect(resend()).toBeEnabled()
    expect(resend()).toHaveTextContent('Send a new code')
    expect(props.onResend).not.toHaveBeenCalled()
  })

  it('asks for a new code, clears the field, says so and starts the wait again', async () => {
    const props = show({ resendAfter: 0 })
    typeCode('123456')
    fireEvent.click(screen.getByRole('button', { name: 'Send a new code' }))
    await waitFor(() => expect(props.onResend).toHaveBeenCalled())
    expect(await screen.findByRole('status')).toHaveTextContent('A new code was sent.')
    expect(screen.getByLabelText('6-digit code')).toHaveValue('')
    expect(screen.getByRole('button', { name: /Send a new code in 60 s/ })).toBeDisabled()
  })

  it('shows why a new code could not be sent', async () => {
    show({ resendAfter: 0, onResend: vi.fn().mockResolvedValue({ success: false, error: 'Please wait before asking for another code.' }) })
    fireEvent.click(screen.getByRole('button', { name: 'Send a new code' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Please wait before asking for another code.')
  })

  it('goes back', () => {
    const props = show()
    fireEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(props.onBack).toHaveBeenCalled()
  })
})
