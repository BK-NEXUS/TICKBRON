import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LanguageSelector } from './LanguageSelector'
import { CurrencySelector } from './CurrencySelector'
import { MobileMenu } from './MobileMenu'
import { BrandLogo } from './BrandLogo'
import { useAuth } from '../contexts/AuthContext'
import type { MessageKey } from '../i18n/messages/en'
import { useI18n } from '../i18n/I18nContext'
import { canUseAdminPanel, canUsePartnerPanel } from '../utils/roles'

interface NavLink {
  labelKey: MessageKey
  href: string
}

const NAV_LINKS: NavLink[] = [
  { labelKey: 'nav.home', href: '/' },
  { labelKey: 'nav.properties', href: '/search' },
  { labelKey: 'nav.about', href: '/about' },
  { labelKey: 'nav.help', href: '/help' },
]

export function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)
  
  const { user, isAuthenticated, logout } = useAuth()
  const { t, language, setLanguage, currency, setCurrency } = useI18n()
  // Most profiles only have full_name since checkpoint 21
  const displayName =
    user?.full_name?.trim() ||
    [user?.first_name, user?.last_name].filter(Boolean).join(' ') ||
    user?.email ||
    t('header.account')
  const navigate = useNavigate()

  const handleLogout = async () => {
    const response = await logout()
    if (response.success) {
      navigate('/')
    }
  }

  return (
    <>
      <header className="header">
        <div className="container header-container">
          {/* Mobile Menu Button */}
          <button
            className="header-mobile-toggle"
            onClick={() => setIsMobileMenuOpen(true)}
            aria-label={t('header.openMenu')}
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
            <BrandLogo variant="header" decorative />
            <h1>TICKBRON</h1>
          </div>

          {/* Desktop Navigation */}
          <nav className="header-nav">
            {NAV_LINKS.map((link) => (
              <Link key={link.href} to={link.href} className="nav-link">
                {t(link.labelKey)}
              </Link>
            ))}
          </nav>

          {/* Actions */}
          <div className="header-actions">
            <LanguageSelector
              currentLanguage={language}
              onLanguageChange={setLanguage}
              className="header-language-selector"
            />
            <CurrencySelector
              currentCurrency={currency}
              onCurrencyChange={setCurrency}
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
                      {displayName[0]?.toUpperCase() || 'U'}
                    </span>
                    <span className="header-user-name">
                      {displayName}
                    </span>
                  </button>
                  {isUserMenuOpen && (
                    <div className="header-user-dropdown">
                      <Link to="/profile" className="header-user-dropdown-item">
                        {t('header.myProfile')}
                      </Link>
                      <Link to="/bookings" className="header-user-dropdown-item">
                        {t('header.myBookings')}
                      </Link>
                      <Link to="/favorites" className="header-user-dropdown-item">
                        {t('header.favorites')}
                      </Link>
                      {canUsePartnerPanel(user) && (
                        <Link to="/partner" className="header-user-dropdown-item">
                          {t('header.partnerDashboard')}
                        </Link>
                      )}
                      {canUseAdminPanel(user) && (
                        <Link to="/admin" className="header-user-dropdown-item header-user-dropdown-item--admin">
                          {t('header.adminDashboard')}
                        </Link>
                      )}
                      <button
                        onClick={handleLogout}
                        className="header-user-dropdown-item header-user-dropdown-item--logout"
                      >
                        {t('header.signOut')}
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <>
                  <Link to="/login" className="btn btn-secondary btn-small">
                    {t('header.login')}
                  </Link>
                  <Link to="/register" className="btn btn-tonal btn-small">
                    {t('header.signUp')}
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
        isAuthenticated={isAuthenticated}
      />
    </>
  )
}
