import { useState } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { useI18n } from '../i18n/I18nContext'
import { CURRENCIES, isCurrency, type Currency } from '../i18n/options'

interface CurrencySelectorProps {
  currentCurrency?: Currency
  onCurrencyChange?: (currency: Currency) => void
  className?: string
}

export function CurrencySelector({
  currentCurrency = 'UZS',
  onCurrencyChange,
  className = '',
}: CurrencySelectorProps) {
  const { t } = useI18n()
  const [isOpen, setIsOpen] = useState(false)
  const current = CURRENCIES.find((currency) => currency.code === currentCurrency) ?? CURRENCIES[0]

  const handleSelect = (code: string) => {
    if (isCurrency(code)) onCurrencyChange?.(code)
    setIsOpen(false)
  }

  return (
    <div className={`currency-selector ${className}`}>
      <button
        type="button"
        className="currency-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label={t('currency.label', { name: t(`currency.${current.code}`) })}
      >
        <span className="currency-code" aria-hidden="true">{current.code}</span>
        <ChevronDown className="currency-chevron" size={14} aria-hidden="true" />
      </button>

      {isOpen && (
        <div className="currency-dropdown">
          <div className="currency-dropdown-list">
            {CURRENCIES.map((currency) => (
              <button
                type="button"
                key={currency.code}
                className={`currency-option ${currency.code === current.code ? 'currency-option-active' : ''}`}
                aria-current={currency.code === current.code ? 'true' : undefined}
                onClick={() => handleSelect(currency.code)}
              >
                <span className="currency-symbol">{currency.symbol}</span>
                <span className="currency-name">{t(`currency.${currency.code}`)}</span>
                <span className="currency-code">{currency.code}</span>
                {currency.code === current.code && <Check className="currency-check" size={16} aria-hidden="true" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
