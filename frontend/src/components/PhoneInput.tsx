import { DEFAULT_PHONE_COUNTRY, PHONE_COUNTRIES, PhoneCountryCode, formatPhone, phoneExample, toPhoneValue } from '../utils/phone'

interface PhoneInputProps {
  id: string
  name?: string
  /** E.164 ("+998901234567"), or '' when empty */
  value: string
  onChange: (value: string) => void
  /** Only 'UZ' for now; a country selector will set this */
  country?: PhoneCountryCode
  className?: string
  required?: boolean
  disabled?: boolean
  autoComplete?: string
  'aria-invalid'?: boolean
  'aria-describedby'?: string
}

/**
 * Phone field used by every form. Shows "+998 90 123 45 67", reports E.164,
 * and does not take more digits than a complete number has. The label and
 * error message stay in the form, so each form keeps its own layout.
 */
export function PhoneInput({
  id,
  name,
  value,
  onChange,
  country = DEFAULT_PHONE_COUNTRY,
  className = '',
  required,
  disabled,
  autoComplete = 'tel',
  ...aria
}: PhoneInputProps) {
  const selected = PHONE_COUNTRIES[country]

  return (
    <div className="phone-input">
      <span className="phone-input-country" title={`${selected.name} (+${selected.dialCode})`} aria-hidden="true">
        {selected.flag}
      </span>
      <input
        id={id}
        name={name}
        type="tel"
        inputMode="tel"
        className={`phone-input-field ${className}`.trim()}
        value={formatPhone(value, country)}
        onChange={(e) => onChange(toPhoneValue(e.target.value, country))}
        placeholder={phoneExample(country)}
        required={required}
        disabled={disabled}
        autoComplete={autoComplete}
        {...aria}
      />
    </div>
  )
}
