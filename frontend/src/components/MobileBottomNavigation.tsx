import { Link, useLocation } from 'react-router-dom'
import { Icon } from './Icon'
import { getIcon } from './icons'

export function MobileBottomNavigation() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Search', icon: getIcon('search') },
    { path: '/bookings', label: 'My Bookings', icon: getIcon('calendar') },
    { path: '/favorites', label: 'Favorites', icon: getIcon('heart') },
    { path: '/profile', label: 'Profile', icon: getIcon('user') },
  ]

  return (
    <nav className="mobile-bottom-navigation" role="navigation" aria-label="Main navigation">
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
                <span className="mobile-bottom-nav-icon" aria-hidden="true"><Icon icon={item.icon} size={22} /></span>
                <span className="mobile-bottom-nav-label">{item.label}</span>
              </Link>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
