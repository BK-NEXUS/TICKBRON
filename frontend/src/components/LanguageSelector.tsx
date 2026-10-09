import { useState } from 'react'
import { Check, ChevronDown } from 'lucide-react'
import { FlagIcon } from './FlagIcon'
import { useI18n } from '../i18n/I18nContext'
import { LANGUAGES, isLanguage, type Language } from '../i18n/options'

interface LanguageSelectorProps {
  currentLanguage?: Language
  onLanguageChange?: (language: Language) => void
  className?: string
}

export function LanguageSelector({
  currentLanguage = 'uz',
  onLanguageChange,
  className = '',
}: LanguageSelectorProps) {
  const { t } = useI18n()
  const [isOpen, setIsOpen] = useState(false)
  const current = LANGUAGES.find((language) => language.code === currentLanguage) ?? LANGUAGES[0]

  const handleSelect = (code: string) => {
    if (isLanguage(code)) onLanguageChange?.(code)
    setIsOpen(false)
  }

  return (
    <div className={`language-selector ${className}`}>
      <button
        type="button"
        className="language-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label={t('language.label', { name: current.name })}
      >
        <FlagIcon language={current.code} />
        <span className="language-code" aria-hidden="true">{current.code.toUpperCase()}</span>
        <ChevronDown className="language-chevron" size={14} aria-hidden="true" />
      </button>

      {isOpen && (
        <div className="language-dropdown">
          <div className="language-dropdown-list">
            {LANGUAGES.map((language) => (
              <button
                type="button"
                key={language.code}
                className={`language-option ${language.code === current.code ? 'language-option-active' : ''}`}
                aria-current={language.code === current.code ? 'true' : undefined}
                onClick={() => handleSelect(language.code)}
              >
                <FlagIcon language={language.code} />
                <span className="language-name">{language.name}</span>
                {language.code === current.code && <Check className="language-check" size={16} aria-hidden="true" />}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
