import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ChangePasswordForm } from './ChangePasswordForm'
import { authAdapter } from '../adapters/authAdapter'

vi.mock('../adapters/authAdapter', () => ({
  authAdapter: { changePassword: vi.fn() },
}))

const changePassword = vi.mocked(authAdapter.changePassword)
const CURRENT = 'Old-Password#2026'
const NEW = 'Fresh9Grape#Tower42'

const fill = (current: string, password: string, confirmation: string) => {
  fireEvent.change(screen.getByLabelText('Current password'), { target: { value: current } })
  fireEvent.change(screen.getByLabelText('New password'), { target: { value: password } })
  fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: confirmation } })
  fireEvent.click(screen.getByRole('button', { name: 'Change password' }))
}

describe('ChangePasswordForm', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('has a titled section with the three password fields', () => {
    render(<ChangePasswordForm />)

    expect(screen.getByRole('heading', { level: 2, name: 'Change password' })).toBeInTheDocument()
    expect(screen.getByLabelText('Current password')).toBeInTheDocument()
    expect(screen.getByLabelText('New password')).toBeInTheDocument()
    expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument()
  })

  it('sends the passwords, confirms, and empties the fields', async () => {
    changePassword.mockResolvedValue({ success: true })
    render(<ChangePasswordForm />)

    fill(CURRENT, NEW, NEW)

    expect(await screen.findByRole('status')).toHaveTextContent('Your password was changed.')
    expect(changePassword).toHaveBeenCalledWith({ current_password: CURRENT, password: NEW, password_confirm: NEW })
    expect(screen.getByLabelText('Current password')).toHaveValue('')
    expect(screen.getByLabelText('New password')).toHaveValue('')
  })

  it('shows the server message for a wrong current password and keeps what was typed', async () => {
    changePassword.mockResolvedValue({ success: false, error: 'Current password: The current password is incorrect.' })
    render(<ChangePasswordForm />)

    fill('wrong-current-1', NEW, NEW)

    expect(await screen.findByRole('alert')).toHaveTextContent('The current password is incorrect.')
    expect(screen.getByLabelText('New password')).toHaveValue(NEW)
  })

  it('an empty field is reported by the site, not by the browser, and nothing is sent', () => {
    render(<ChangePasswordForm />)

    fireEvent.click(screen.getByRole('button', { name: 'Change password' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Current password is required.')
    expect(screen.getByLabelText('Current password')).toHaveFocus()
    expect(changePassword).not.toHaveBeenCalled()
  })

  it('does not call the server for a mismatch or a short password', () => {
    render(<ChangePasswordForm />)

    fill(CURRENT, NEW, 'something else')
    expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match')

    fill(CURRENT, 'Short#1abc', 'Short#1abc')
    expect(screen.getByRole('alert')).toHaveTextContent('at least 12 characters')
    expect(changePassword).not.toHaveBeenCalled()
  })

  it('shows progress and disables the fields while saving', async () => {
    let finish: (value: { success: boolean }) => void = () => {}
    changePassword.mockReturnValue(new Promise((resolve) => { finish = resolve }))
    render(<ChangePasswordForm />)

    fill(CURRENT, NEW, NEW)

    expect(await screen.findByRole('button', { name: 'Saving...' })).toBeDisabled()
    expect(screen.getByLabelText('Current password')).toBeDisabled()
    finish({ success: true })
    expect(await screen.findByRole('status')).toBeInTheDocument()
  })
})
