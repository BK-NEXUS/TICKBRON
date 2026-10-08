import { useState, useEffect } from 'react'
import { useDialogFocus } from '../hooks/useDialogFocus'

interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
  className?: string
  isAuthenticated?: boolean
}

interface NavLink {
  label: string
  href: string
}

const NAV_LINKS: NavLink[] = [
  { label: 'Home', href: '/' },
  { label: 'Properties', href: '/search' },
  { label: 'About', href: '/about' },
  { label: 'Help', href: '/help' },
]

export function MobileMenu({ isOpen, onClose, className = '', isAuthenticated = false }: MobileMenuProps) {
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
        aria-label="Navigation menu"
      >
        <div className="mobile-menu-header">
          <h2 className="mobile-menu-title">Menu</h2>
          <button
            className="mobile-menu-close"
            onClick={onClose}
            aria-label="Close menu"
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
                  {link.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>

        {!isAuthenticated && (
          <div className="mobile-menu-footer">
            <a href="/login" className="btn btn-secondary btn-full" onClick={onClose}>Login</a>
            <a href="/register" className="btn btn-primary btn-full" onClick={onClose}>Sign Up</a>
          </div>
        )}
      </div>
    </>
  )
}
