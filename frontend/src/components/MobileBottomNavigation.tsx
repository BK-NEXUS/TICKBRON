import { useI18n } from '../i18n/I18nContext'
import { Link, useLocation } from 'react-router-dom'
import { CalendarDays, Heart, Search, User } from 'lucide-react'

export function MobileBottomNavigation() {
  const location = useLocation()
  const { t } = useI18n()

  const navItems = [
    { path: '/', label: t('nav.mobile.search'), icon: Search },
    { path: '/bookings', label: t('nav.mobile.bookings'), icon: CalendarDays },
    { path: '/favorites', label: t('nav.mobile.favorites'), icon: Heart },
    { path: '/profile', label: t('nav.mobile.profile'), icon: User },
  ]

  return (
    <nav className="mobile-bottom-navigation" role="navigation" aria-label={t('nav.mobile.main')}>
      <ul className="mobile-bottom-nav-list">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || 
                          (item.path !== '/' && location.pathname.startsWith(item.path))
          return (
            <li key={item.path} className="mobile-bottom-nav-item">
              <Link
                to={item.path}
                className={`mobile-bottom-nav-link ${isActive ? 'mobile-bottom-nav-link--active' : ''}`}
                aria-current={isActive ? 'page' : undefined}
              >
                <span className="mobile-bottom-nav-icon" aria-hidden="true"><item.icon size={22} /></span>
                <span className="mobile-bottom-nav-label">{item.label}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
