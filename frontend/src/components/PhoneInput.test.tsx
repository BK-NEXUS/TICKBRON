import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { PhoneInput } from './PhoneInput'
import { formatPhone, isValidPhone, toPhoneValue } from '../utils/phone'

function Harness({ onValue }: { onValue?: (value: string) => void }) {
  const [value, setValue] = useState('')
  return (
    <>
      <label htmlFor="phone">Phone Number</label>
      <PhoneInput
        id="phone"
        value={value}
        onChange={(next) => {
          setValue(next)
          onValue?.(next)
        }}
      />
    </>
  )
}

const type = (input: HTMLElement, text: string) => fireEvent.change(input, { target: { value: text } })

describe('phone utils', () => {
  it('keeps only the digits that fit a +998 number', () => {
    expect(toPhoneValue('901234567')).toBe('+998901234567')
    expect(toPhoneValue('+998 90 123 45 67')).toBe('+998901234567')
    expect(toPhoneValue('998901234567')).toBe('+998901234567')
    expect(toPhoneValue('+998 90 123 45 67 89 00')).toBe('+998901234567')
    expect(toPhoneValue('+998 (90) 123-45-67')).toBe('+998901234567')
    expect(toPhoneValue('90abc12')).toBe('+9989012')
    expect(toPhoneValue('')).toBe('')
    expect(toPhoneValue('+998 ')).toBe('')
  })

  it('formats as +998 90 123 45 67, also while typing', () => {
    expect(formatPhone('+998901234567')).toBe('+998 90 123 45 67')
    expect(formatPhone('+9989012')).toBe('+998 90 12')
    expect(formatPhone('+9989')).toBe('+998 9')
    expect(formatPhone('')).toBe('')
  })

  it('accepts only complete numbers', () => {
    expect(isValidPhone('+998901234567')).toBe(true)
    expect(isValidPhone('+99890123456')).toBe(false)
    expect(isValidPhone('+9989012345678')).toBe(false)
    expect(isValidPhone('+1234567890')).toBe(false)
    expect(isValidPhone('')).toBe(false)
  })
})

describe('PhoneInput', () => {
  it('shows the number formatted and reports it in E.164', () => {
    const onValue = vi.fn()
    render(<Harness onValue={onValue} />)
    const input = screen.getByLabelText('Phone Number')

    type(input, '901234567')

    expect(input).toHaveValue('+998 90 123 45 67')
    expect(onValue).toHaveBeenLastCalledWith('+998901234567')
  })

  it('stops accepting digits beyond a complete number', () => {
    const onValue = vi.fn()
    render(<Harness onValue={onValue} />)
    const input = screen.getByLabelText('Phone Number')

    type(input, '+998 90 123 45 67')
    type(input, '+998 90 123 45 678')

    expect(input).toHaveValue('+998 90 123 45 67')
    expect(onValue).toHaveBeenLastCalledWith('+998901234567')
  })

  it('ignores letters', () => {
    render(<Harness />)
    const input = screen.getByLabelText('Phone Number')
    type(input, 'abc')
    expect(input).toHaveValue('')
  })

  it('is a tel input with a +998 example placeholder and the country shown', () => {
    render(<Harness />)
    const input = screen.getByLabelText('Phone Number')
    expect(input).toHaveAttribute('type', 'tel')
    expect(input).toHaveAttribute('placeholder', '+998 90 123 45 67')
    expect(screen.getByTitle('Uzbekistan (+998)')).toBeInTheDocument()
  })
})
