import { describe, it, expect, afterEach, vi } from 'vitest'
import { act, fireEvent, render, screen } from '@testing-library/react'
import { PasswordField } from './PasswordField'

function renderField() {
  return render(
    <>
      <label htmlFor="pw">Password</label>
      <PasswordField id="pw" value="secret" onChange={() => {}} autoComplete="current-password" />
    </>,
  )
}

describe('PasswordField', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows and hides the password with the eye button', () => {
    renderField()
    const input = screen.getByLabelText('Password')
    expect(input).toHaveAttribute('type', 'password')

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }))
    expect(input).toHaveAttribute('type', 'text')
    expect(screen.getByRole('button', { name: 'Hide password' })).toHaveAttribute('aria-pressed', 'true')

    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }))
    expect(input).toHaveAttribute('type', 'password')
  })

  it('hides a shown password again after 30 seconds', () => {
    vi.useFakeTimers()
    renderField()
    const input = screen.getByLabelText('Password')

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }))
    act(() => { vi.advanceTimersByTime(29_000) })
    expect(input).toHaveAttribute('type', 'text')

    act(() => { vi.advanceTimersByTime(1_000) })
    expect(input).toHaveAttribute('type', 'password')
  })

  it('does not hide early when the password was shown again', () => {
    vi.useFakeTimers()
    renderField()
    const input = screen.getByLabelText('Password')

    fireEvent.click(screen.getByRole('button', { name: 'Show password' }))
    act(() => { vi.advanceTimersByTime(20_000) })
    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }))
    fireEvent.click(screen.getByRole('button', { name: 'Show password' }))
    act(() => { vi.advanceTimersByTime(20_000) })

    expect(input).toHaveAttribute('type', 'text')
  })

  it('warns while Caps Lock is on and stops warning when it is off or the field loses focus', () => {
    renderField()
    const input = screen.getByLabelText('Password')
    const capsOn = { modifierCapsLock: true }
    const capsOff = { modifierCapsLock: false }

    expect(screen.queryByText('Caps Lock is on')).not.toBeInTheDocument()

    fireEvent.keyDown(input, { key: 'A', ...capsOn })
    expect(screen.getByText('Caps Lock is on')).toBeInTheDocument()
    expect(input).toHaveAccessibleDescription('Caps Lock is on')

    fireEvent.keyUp(input, { key: 'CapsLock', ...capsOff })
    expect(screen.queryByText('Caps Lock is on')).not.toBeInTheDocument()

    fireEvent.keyDown(input, { key: 'A', ...capsOn })
    fireEvent.blur(input)
    expect(screen.queryByText('Caps Lock is on')).not.toBeInTheDocument()
  })
})
