import { useState } from 'react'
import { LanguageSelector } from './LanguageSelector'
import { CurrencySelector } from './CurrencySelector'
import { MobileMenu } from './MobileMenu'

interface NavLink {
  label: string
  href: string
}

const NAV_LINKS: NavLink[] = [
  { label: 'Home', href: '/' },
  { label: 'Properties', href: '/properties' },
  { label: 'About', href: '/about' },
  { label: 'Help', href: '/help' },
]

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [currentLanguage, setCurrentLanguage] = useState('en')
  const [currentCurrency, setCurrentCurrency] = useState('USD')

  const handleLanguageChange = (languageCode: string) => {
    setCurrentLanguage(languageCode)
    // TODO: Integrate with backend API when available
    console.log('Language changed to:', languageCode)
  }

  const handleCurrencyChange = (currencyCode: string) => {
    setCurrentCurrency(currencyCode)
    // TODO: Integrate with backend API when available
    console.log('Currency changed to:', currencyCode)
  }

  return (
    <>
      <header className="header">
        <div className="header-container">
          {/* Mobile Menu Button */}
          <button
            className="header-mobile-toggle"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label="Open menu"
            aria-expanded={isMobileMenuOpen}
          >
            <span className="hamburger-icon">
              <span></span>
              <span></span>
              <span></span>
            </span>
          </button>

          {/* Logo */}
          <div className="header-logo">
            <h1>TICKBRON</h1>
          </div>

          {/* Desktop Navigation */}
          <nav className="header-nav">
            {NAV_LINKS.map((link) => (
              <a key={link.href} href={link.href} className="nav-link">
                {link.label}
              </a>
            ))}
          </nav>

          {/* Actions */}
          <div className="header-actions">
            <LanguageSelector
              currentLanguage={currentLanguage}
              onLanguageChange={handleLanguageChange}
              className="header-language-selector"
            />
            <CurrencySelector
              currentCurrency={currentCurrency}
              onCurrencyChange={handleCurrencyChange}
              className="header-currency-selector"
            />
            <div className="header-auth-buttons">
              <button className="btn btn-secondary btn-small">Login</button>
              <button className="btn btn-primary btn-small">Sign Up</button>
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      <MobileMenu
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
      />
    </>
  )
}
