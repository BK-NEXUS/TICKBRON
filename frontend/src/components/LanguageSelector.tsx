import { useState } from 'react'

// TODO: Language data will come from backend API when available
// For now, this is a UI foundation with placeholder data
const LANGUAGES = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'pt', name: 'Português', flag: '🇧🇷' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
]

interface LanguageSelectorProps {
  currentLanguage?: string
  onLanguageChange?: (languageCode: string) => void
  className?: string
}

export function LanguageSelector({ 
  currentLanguage = 'en', 
  onLanguageChange,
  className = '' 
}: LanguageSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const currentLang = LANGUAGES.find(lang => lang.code === currentLanguage) || LANGUAGES[0]

  const handleSelect = (languageCode: string) => {
    if (onLanguageChange) {
      onLanguageChange(languageCode)
    }
    setIsOpen(false)
  }

  return (
    <div className={`language-selector ${className}`}>
      <button
        className="language-selector-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <span className="language-flag">{currentLang.flag}</span>
        <span className="language-code">{currentLang.code.toUpperCase()}</span>
        <span className="language-chevron">{isOpen ? '▲' : '▼'}</span>
      </button>

      {isOpen && (
        <div className="language-dropdown">
          <div className="language-dropdown-list">
            {LANGUAGES.map((language) => (
              <button
                key={language.code}
                className={`language-option ${language.code === currentLanguage ? 'language-option-active' : ''}`}
                onClick={() => handleSelect(language.code)}
              >
                <span className="language-flag">{language.flag}</span>
                <span className="language-name">{language.name}</span>
                {language.code === currentLanguage && (
                  <span className="language-check">✓</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
