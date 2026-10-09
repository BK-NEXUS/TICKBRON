import { describe, it, expect, vi } from 'vitest'
import { useState } from 'react'
import { render, screen, fireEvent, within } from '@testing-library/react'
import { PhoneInput } from './PhoneInput'
import { PHONE_COUNTRIES, countryFromPhone, formatPhone, isValidPhone, toPhoneValue } from '../utils/phone'

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

describe('phone utils for other countries', () => {
  it('lists more than 40 countries, Uzbekistan first, none with an emoji flag', () => {
    const list = Object.values(PHONE_COUNTRIES)
    expect(list.length).toBeGreaterThan(40)
    expect(list[0].code).toBe('UZ')
    expect(new Set(list.map(country => country.code)).size).toBe(list.length)
  })

  it('formats and validates a Kazakhstan, Turkey and Germany number', () => {
    expect(toPhoneValue('7011234567', 'KZ')).toBe('+77011234567')
    expect(formatPhone('+77011234567', 'KZ')).toBe('+7 701 123 45 67')
    expect(isValidPhone('+77011234567', 'KZ')).toBe(true)
    expect(isValidPhone('+905321234567', 'TR')).toBe(true)
    expect(isValidPhone('+4915112345678', 'DE')).toBe(true)
    expect(isValidPhone('+491511234', 'DE')).toBe(false)
  })

  it('without a country, accepts a complete number of any listed country', () => {
    expect(isValidPhone('+77011234567')).toBe(true)
    expect(isValidPhone('+905321234567')).toBe(true)
    expect(isValidPhone('+9989012345')).toBe(false)
  })

  it('finds the country of a stored number by its dial code', () => {
    expect(countryFromPhone('+998901234567')).toBe('UZ')
    expect(countryFromPhone('+905321234567')).toBe('TR')
    expect(countryFromPhone('+9999')).toBeNull()
    expect(countryFromPhone('')).toBeNull()
  })

  it('shows digits beyond the usual groups instead of hiding them', () => {
    expect(formatPhone('+4915112345678', 'DE')).toBe('+49 151 1234 5678')
  })
})

describe('PhoneInput country selector', () => {
  const open = () => fireEvent.click(screen.getByRole('button', { name: /Country: / }))

  it('shows the selected country as an SVG flag, not an emoji', () => {
    render(<Harness />)
    const button = screen.getByRole('button', { name: 'Country: Uzbekistan (+998)' })
    expect(button.querySelector('svg')).not.toBeNull()
  })

  it('lists countries with SVG flags and searches them by name or dial code', () => {
    render(<Harness />)
    open()
    const list = screen.getByRole('listbox')
    expect(within(list).getAllByRole('option').length).toBeGreaterThan(40)
    expect(list.querySelectorAll('svg').length).toBeGreaterThan(40)

    fireEvent.change(screen.getByRole('searchbox', { name: 'Search country' }), { target: { value: 'turk' } })
    expect(within(screen.getByRole('listbox')).getAllByRole('option').map(o => o.textContent)).toEqual([
      expect.stringContaining('Turkmenistan'),
      expect.stringContaining('Turkey'),
    ])

    fireEvent.change(screen.getByRole('searchbox', { name: 'Search country' }), { target: { value: '+995' } })
    expect(within(screen.getByRole('listbox')).getAllByRole('option')).toHaveLength(1)
  })

  it('switches the country: placeholder, format and E.164 value follow', () => {
    const onValue = vi.fn()
    render(<Harness onValue={onValue} />)
    open()
    fireEvent.click(screen.getByRole('option', { name: /Kazakhstan/ }))

    const input = screen.getByLabelText('Phone Number')
    expect(input).toHaveAttribute('placeholder', '+7 901 234 56 78')
    type(input, '7011234567')
    expect(input).toHaveValue('+7 701 123 45 67')
    expect(onValue).toHaveBeenLastCalledWith('+77011234567')
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  })

  it('picks the country of a number that is pasted in full', () => {
    render(<Harness />)
    type(screen.getByLabelText('Phone Number'), '+90 532 123 45 67')
    expect(screen.getByRole('button', { name: /Country: Turkey/ })).toBeInTheDocument()
    expect(screen.getByLabelText('Phone Number')).toHaveValue('+90 532 123 45 67')
  })

  it('closes on Escape and returns focus to the button', () => {
    render(<Harness />)
    open()
    fireEvent.keyDown(screen.getByRole('searchbox', { name: 'Search country' }), { key: 'Escape' })
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Country: / })).toHaveFocus()
  })

  it('keeps the selector out of the way when the field is disabled', () => {
    render(<PhoneInput id="p" value="" onChange={() => {}} disabled />)
    expect(screen.getByRole('button', { name: /Country: / })).toBeDisabled()
  })
})
