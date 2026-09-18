import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LanguageSelector } from './LanguageSelector'
import { CurrencySelector } from './CurrencySelector'
import { MobileMenu } from './MobileMenu'
import { useAuth } from '../contexts/AuthContext'

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
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()

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

  const handleLogout = async () => {
    const response = await logout()
    if (response.success) {
      navigate('/')
    }
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
              <Link key={link.href} to={link.href} className="nav-link">
                {link.label}
              </Link>
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
              {isAuthenticated ? (
                <div className="header-user-menu">
                  <button
                    className="header-user-button"
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    aria-expanded={isUserMenuOpen}
                    aria-haspopup="true"
                  >
                    <span className="header-user-avatar">
                      {user?.first_name?.[0]?.toUpperCase() || 'U'}
                    </span>
                    <span className="header-user-name">
                      {user?.first_name || 'User'}
                    </span>
                  </button>
                  {isUserMenuOpen && (
                    <div className="header-user-dropdown">
                      <Link to="/profile" className="header-user-dropdown-item">
                        My Profile
                      </Link>
                      <Link to="/bookings" className="header-user-dropdown-item">
                        My Bookings
                      </Link>
                      <Link to="/favorites" className="header-user-dropdown-item">
                        Favorites
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="header-user-dropdown-item header-user-dropdown-item--logout"
                      >
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <Link to="/login" className="btn btn-secondary btn-small">
                    Login
                  </Link>
                  <Link to="/register" className="btn btn-primary btn-small">
                    Sign Up
                  </Link>
                </>
              )}
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
