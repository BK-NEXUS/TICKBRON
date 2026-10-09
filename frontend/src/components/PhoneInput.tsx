import { useI18n } from '../i18n/I18nContext'
import { useEffect, useRef, useState } from 'react'
import { ChevronDown, Search } from 'lucide-react'
import { CountryFlag } from './CountryFlag'
import {
  DEFAULT_PHONE_COUNTRY, PHONE_COUNTRIES, PhoneCountryCode, countryFromPhone, formatPhone, phoneExample, toPhoneValue,
} from '../utils/phone'

interface PhoneInputProps {
  id: string
  name?: string
  /** E.164 ("+998901234567"), or '' when empty */
  value: string
  onChange: (value: string) => void
  /** Country selected first when the value does not say; Uzbekistan by default */
  country?: PhoneCountryCode
  className?: string
  required?: boolean
  disabled?: boolean
  autoComplete?: string
  'aria-invalid'?: boolean
  'aria-describedby'?: string
}

const COUNTRIES = Object.values(PHONE_COUNTRIES)

function searchCountries(query: string, nameOf: (item: (typeof COUNTRIES)[number]) => string) {
  const text = query.trim().toLowerCase()
  const digits = text.replace(/\D/g, '')
  if (!text) return COUNTRIES
  return COUNTRIES.filter(item =>
    nameOf(item).toLowerCase().includes(text) || item.name.toLowerCase().includes(text)
      || (digits !== '' && item.dialCode.startsWith(digits)),
  )
}

/**
 * Phone field used by every form. A country selector (SVG flags, searchable) sets the dial code and the
 * format; the field shows "+998 90 123 45 67", reports E.164, and does not take more digits than a complete
 * number has. The label and error message stay in the form, so each form keeps its own layout.
 */
export function PhoneInput({
  id,
  name,
  value,
  onChange,
  country: initialCountry = DEFAULT_PHONE_COUNTRY,
  className = '',
  required,
  disabled,
  autoComplete = 'tel',
  ...aria
}: PhoneInputProps) {
  const { t, regionName } = useI18n()
  const [country, setCountry] = useState<PhoneCountryCode>(() => countryFromPhone(value) ?? initialCountry)
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const rootRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)
  const selected = PHONE_COUNTRIES[country]
  const nameOf = (item: (typeof COUNTRIES)[number]) => regionName(item.code, item.name)
  const label = `${nameOf(selected)} (+${selected.dialCode})`

  // A number that arrives from outside (a saved profile) brings its own country
  useEffect(() => {
    if (value && !value.startsWith(`+${PHONE_COUNTRIES[country].dialCode}`)) {
      const detected = countryFromPhone(value)
      if (detected) setCountry(detected)
    }
  }, [value, country])

  useEffect(() => {
    if (!isOpen) return
    const close = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setIsOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [isOpen])

  const closeList = () => {
    setIsOpen(false)
    setQuery('')
  }

  const choose = (next: PhoneCountryCode) => {
    // A number typed for another country would be wrong here, so it is cleared
    if (next !== country && value) onChange('')
    setCountry(next)
    closeList()
    buttonRef.current?.focus()
  }

  const handleInput = (text: string) => {
    // A full number with "+" (pasted or typed) says which country it is
    const detected = text.trim().startsWith('+') ? countryFromPhone(text) : null
    const target = detected ?? country
    if (detected && detected !== country && !text.replace(/\D/g, '').startsWith(selected.dialCode)) setCountry(detected)
    onChange(toPhoneValue(text, target))
  }

  const results = searchCountries(query, nameOf)

  return (
    <div className="phone-input" ref={rootRef}>
      <button
        type="button"
        ref={buttonRef}
        className="phone-input-country"
        title={label}
        aria-label={t('phone.countryLabel', { name: label })}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        disabled={disabled}
        onClick={() => setIsOpen(open => !open)}
      >
        <CountryFlag code={country} />
        <ChevronDown size={14} aria-hidden="true" />
      </button>
      <input
        id={id}
        name={name}
        type="tel"
        inputMode="tel"
        className={`phone-input-field ${className}`.trim()}
        value={formatPhone(value, country)}
        onChange={(e) => handleInput(e.target.value)}
        placeholder={phoneExample(country)}
        required={required}
        disabled={disabled}
        autoComplete={autoComplete}
        {...aria}
      />

      {isOpen && (
        <div className="phone-country-panel">
          <div className="phone-country-search">
            <Search size={16} aria-hidden="true" />
            <input
              type="search"
              autoFocus
              aria-label={t('phone.search')}
              placeholder={t('phone.search')}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  e.stopPropagation()
                  closeList()
                  buttonRef.current?.focus()
                }
              }}
            />
          </div>
          <ul className="phone-country-list" role="listbox" aria-label={t('phone.countries')}>
            {results.map(item => (
              <li key={item.code} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={item.code === country}
                  className={`phone-country-option ${item.code === country ? 'phone-country-option--active' : ''}`}
                  onClick={() => choose(item.code as PhoneCountryCode)}
                >
                  <CountryFlag code={item.code as PhoneCountryCode} />
                  <span className="phone-country-name">{nameOf(item)}</span>
                  <span className="phone-country-dial">+{item.dialCode}</span>
                </button>
              </li>
            ))}
            {results.length === 0 && <li className="phone-country-empty">{t('phone.none')}</li>}
          </ul>
        </div>
      )}
    </div>
  )
}
