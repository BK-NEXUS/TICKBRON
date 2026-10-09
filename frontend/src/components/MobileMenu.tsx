import { useState, useEffect } from 'react'
import { useDialogFocus } from '../hooks/useDialogFocus'
import { ThemeToggle } from './ThemeToggle'
import { SegmentedControl } from './SegmentedControl'
import { useI18n } from '../i18n/I18nContext'
import type { MessageKey } from '../i18n/messages/en'
import { CURRENCIES, LANGUAGES } from '../i18n/options'

interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
  className?: string
  isAuthenticated?: boolean
}

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

export function MobileMenu({ isOpen, onClose, className = '', isAuthenticated = false }: MobileMenuProps) {
  const { t, language, setLanguage, currency, setCurrency } = useI18n()
  const [isAnimating, setIsAnimating] = useState(false)

  useEffect(() => {
    if (isOpen) {
      setIsAnimating(true)
      // Prevent body scroll when menu is open
      document.body.style.overflow = 'hidden'
    } else {
      const timer = setTimeout(() => setIsAnimating(false), 300)
      return () => clearTimeout(timer)
    }

    return () => {
      document.body.style.overflow = ''
    }
  }, [isOpen])

  const menuRef = useDialogFocus<HTMLDivElement>(isOpen, onClose)

  if (!isOpen && !isAnimating) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className={`mobile-menu-backdrop ${isAnimating ? 'mobile-menu-backdrop-visible' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Menu */}
      <div
        className={`mobile-menu ${isAnimating ? 'mobile-menu-open' : ''} ${className}`}
        ref={menuRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={t('menu.navigation')}
      >
        <div className="mobile-menu-header">
          <h2 className="mobile-menu-title">{t('menu.title')}</h2>
          <button
            className="mobile-menu-close"
            onClick={onClose}
            aria-label={t('menu.close')}
          >
            ✕
          </button>
        </div>

        <nav className="mobile-menu-nav">
          <ul className="mobile-menu-list">
            {NAV_LINKS.map((link) => (
              <li key={link.href}>
                <a
                  href={link.href}
                  className="mobile-menu-link"
                  onClick={onClose}
                >
                  {t(link.labelKey)}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        <div className="mobile-menu-preferences">
          <SegmentedControl
            aria-label={t('menu.language')}
            value={language}
            onChange={setLanguage}
            fullWidth
            options={LANGUAGES.map(({ code, name }) => ({ value: code, label: code.toUpperCase(), ariaLabel: name }))}
          />
          <SegmentedControl
            aria-label={t('menu.currency')}
            value={currency}
            onChange={setCurrency}
            fullWidth
            options={CURRENCIES.map(({ code }) => ({ value: code, label: code }))}
          />
          <ThemeToggle className="mobile-menu-theme-toggle" />
        </div>

        {!isAuthenticated && (
          <div className="mobile-menu-footer">
            <a href="/login" className="btn btn-secondary btn-full" onClick={onClose}>{t('header.login')}</a>
            <a href="/register" className="btn btn-primary btn-full" onClick={onClose}>{t('header.signUp')}</a>
          </div>
        )}
      </div>
    </>
  )
}
