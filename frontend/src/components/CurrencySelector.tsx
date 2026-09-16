import { useState } from 'react'

// TODO: Currency data will come from backend API when available
// For now, this is a UI foundation with placeholder data
const CURRENCIES = [
  { code: 'USD', symbol: '$', name: 'US Dollar' },
  { code: 'EUR', symbol: '€', name: 'Euro' },
  { code: 'GBP', symbol: '£', name: 'British Pound' },
  { code: 'JPY', symbol: '¥', name: 'Japanese Yen' },
  { code: 'CAD', symbol: 'C$', name: 'Canadian Dollar' },
  { code: 'AUD', symbol: 'A$', name: 'Australian Dollar' },
  { code: 'CHF', symbol: 'Fr', name: 'Swiss Franc' },
  { code: 'CNY', symbol: '¥', name: 'Chinese Yuan' },
]

interface CurrencySelectorProps {
  currentCurrency?: string
  onCurrencyChange?: (currencyCode: string) => void
  className?: string
}

export function CurrencySelector({ 
  currentCurrency = 'USD', 
  onCurrencyChange,
  className = '' 
}: CurrencySelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const currentCurr = CURRENCIES.find(curr => curr.code === currentCurrency) || CURRENCIES[0]

  const handleSelect = (currencyCode: string) => {
    if (onCurrencyChange) {
      onCurrencyChange(currencyCode)
    }
    setIsOpen(false)
  }

  return (
    <div className={`currency-selector ${className}`}>
      <button
        className="currency-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <span className="currency-symbol">{currentCurr.symbol}</span>
        <span className="currency-code">{currentCurr.code}</span>
        <span className="currency-chevron">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="currency-dropdown">
          <div className="currency-dropdown-list">
            {CURRENCIES.map((currency) => (
              <button
                key={currency.code}
                className={`currency-option ${currency.code === currentCurrency ? 'currency-option-active' : ''}`}
                onClick={() => handleSelect(currency.code)}
              >
                <span className="currency-symbol">{currency.symbol}</span>
                <span className="currency-name">{currency.name}</span>
                <span className="currency-code">{currency.code}</span>
                {currency.code === currentCurrency && (
                  <span className="currency-check">✓</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
