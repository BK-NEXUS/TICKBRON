import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PhoneVerifyDialog } from './PhoneVerifyDialog'
import { I18nProvider } from '../i18n/I18nContext'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { requestPhoneVerification: vi.fn(), confirmPhoneVerification: vi.fn() },
}))

const adapter = vi.mocked(authAdapter)

function renderDialog() {
  const onVerified = vi.fn()
  const onClose = vi.fn()
  render(
    <I18nProvider>
      <PhoneVerifyDialog phone="+998901112233" onVerified={onVerified} onClose={onClose} />
    </I18nProvider>,
  )
  return { onVerified, onClose }
}

const codeBox = () => screen.findByLabelText('SMS code') as Promise<HTMLInputElement>
const verifyButton = () => screen.getByRole('button', { name: 'Verify' })

describe('PhoneVerifyDialog', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    adapter.requestPhoneVerification.mockResolvedValue({ success: true, otp_code: '123456' })
  })

  it('is a labelled dialog that sends one code to the account number on open', async () => {
    renderDialog()

    expect(screen.getByRole('dialog', { name: 'Verify your phone number' })).toHaveTextContent('+998901112233')
    await codeBox()
    expect(adapter.requestPhoneVerification).toHaveBeenCalledTimes(1)
  })

  it('cannot be submitted until six digits are entered', async () => {
    renderDialog()
    const box = await codeBox()

    expect(verifyButton()).toBeDisabled()
    fireEvent.change(box, { target: { value: '12345' } })
    expect(verifyButton()).toBeDisabled()
    fireEvent.change(box, { target: { value: '123456' } })
    expect(verifyButton()).toBeEnabled()
  })

  it('confirms the code and tells the screen the phone is verified', async () => {
    adapter.confirmPhoneVerification.mockResolvedValue({ success: true, user: { id: 1, phone_verified: true } as never })
    const { onVerified } = renderDialog()

    fireEvent.change(await codeBox(), { target: { value: '123456' } })
    fireEvent.click(verifyButton())

    await waitFor(() => expect(onVerified).toHaveBeenCalledTimes(1))
    expect(adapter.confirmPhoneVerification).toHaveBeenCalledWith('123456')
  })

  it('shows a wrong-code error and stays open', async () => {
    adapter.confirmPhoneVerification.mockResolvedValue({ success: false, error: 'x', code: 'otp_invalid' })
    const { onVerified } = renderDialog()

    fireEvent.change(await codeBox(), { target: { value: '000000' } })
    fireEvent.click(verifyButton())

    expect(await screen.findByRole('alert')).toHaveTextContent('The code is wrong or has expired.')
    expect(onVerified).not.toHaveBeenCalled()
  })

  it('shows an error when the code could not be sent and lets the user try again', async () => {
    adapter.requestPhoneVerification.mockResolvedValueOnce({ success: false, error: 'x', code: 'throttled' })
    renderDialog()

    expect(await screen.findByRole('alert')).toHaveTextContent('We could not send the code.')
    adapter.requestPhoneVerification.mockResolvedValueOnce({ success: true, otp_code: '654321' })
    fireEvent.click(screen.getByRole('button', { name: 'Send a new code' }))

    await codeBox()
    expect(adapter.requestPhoneVerification).toHaveBeenCalledTimes(2)
  })

  it('closes from the close button', async () => {
    const { onClose } = renderDialog()
    await codeBox()

    fireEvent.click(screen.getByRole('button', { name: 'Close' }))

    expect(onClose).toHaveBeenCalled()
  })
})
