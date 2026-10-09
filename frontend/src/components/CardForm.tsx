import { useEffect, useState } from 'react'
import { FlaskConical } from 'lucide-react'
import {
  formatCardNumber, formatExpiry, isCardNumberValid, isCardholderValid, isCvvValid, isExpiryValid,
} from '../utils/card'

type Field = 'number' | 'expiry' | 'cvv' | 'holder'

interface CardFormProps {
  /** Only whether the card looks complete is reported; the values never leave this component */
  onValidityChange: (valid: boolean) => void
  disabled?: boolean
}

const ERRORS: Record<Field, string> = {
  number: 'Enter a valid card number.',
  expiry: 'Enter a valid expiry date (MM/YY).',
  cvv: 'Enter the 3 digit security code.',
  holder: 'Enter the name as printed on the card.',
}

const CHECKS: Record<Field, (value: string) => boolean> = {
  number: isCardNumberValid,
  expiry: (value) => isExpiryValid(value),
  cvv: isCvvValid,
  holder: isCardholderValid,
}

/** Card details for the TEST payment mode. Nothing typed here is sent, stored or logged. */
export function CardForm({ onValidityChange, disabled }: CardFormProps) {
  const [values, setValues] = useState<Record<Field, string>>({ number: '', expiry: '', cvv: '', holder: '' })
  const [touched, setTouched] = useState<Record<Field, boolean>>({ number: false, expiry: false, cvv: false, holder: false })

  const valid = (Object.keys(CHECKS) as Field[]).every((field) => CHECKS[field](values[field]))
  useEffect(() => {
    onValidityChange(valid)
  }, [valid, onValidityChange])

  const set = (field: Field, value: string) => setValues((current) => ({ ...current, [field]: value }))
  const touch = (field: Field) => setTouched((current) => ({ ...current, [field]: true }))
  const showError = (field: Field) => touched[field] && !CHECKS[field](values[field])

  const fieldProps = (field: Field) => ({
    id: `card-${field}`,
    value: values[field],
    disabled,
    onBlur: () => touch(field),
    className: `booking-form-input ${showError(field) ? 'booking-form-input--error' : ''}`.trim(),
    'aria-invalid': showError(field),
    'aria-describedby': showError(field) ? `card-${field}-error` : undefined,
  })

  const error = (field: Field) =>
    showError(field) && (
      <span id={`card-${field}-error`} className="booking-form-error" role="alert">{ERRORS[field]}</span>
    )

  return (
    <div className="card-form">
      <div className="card-form-notice" role="note">
        <FlaskConical size={18} aria-hidden="true" />
        <span>
          <strong>Test mode.</strong> Card details are not sent or stored. Real payments are made on the
          Payme, Click or Visa page.
        </span>
      </div>

      <div className="booking-form-field">
        <label htmlFor="card-number" className="booking-form-label">Card number</label>
        <input
          {...fieldProps('number')}
          type="text"
          inputMode="numeric"
          autoComplete="cc-number"
          placeholder="1234 5678 9012 3456"
          onChange={(e) => set('number', formatCardNumber(e.target.value))}
        />
        {error('number')}
      </div>

      <div className="card-form-row">
        <div className="booking-form-field">
          <label htmlFor="card-expiry" className="booking-form-label">Expiry (MM/YY)</label>
          <input
            {...fieldProps('expiry')}
            type="text"
            inputMode="numeric"
            autoComplete="cc-exp"
            placeholder="MM/YY"
            onChange={(e) => set('expiry', formatExpiry(e.target.value))}
          />
          {error('expiry')}
        </div>
        <div className="booking-form-field">
          <label htmlFor="card-cvv" className="booking-form-label">CVV</label>
          <input
            {...fieldProps('cvv')}
            type="password"
            inputMode="numeric"
            autoComplete="cc-csc"
            maxLength={3}
            placeholder="123"
            onChange={(e) => set('cvv', e.target.value.replace(/\D/g, '').slice(0, 3))}
          />
          {error('cvv')}
        </div>
      </div>

      <div className="booking-form-field">
        <label htmlFor="card-holder" className="booking-form-label">Name on card</label>
        <input
          {...fieldProps('holder')}
          type="text"
          autoComplete="cc-name"
          placeholder="NAME SURNAME"
          onChange={(e) => set('holder', e.target.value)}
        />
        {error('holder')}
      </div>
    </div>
  )
}
