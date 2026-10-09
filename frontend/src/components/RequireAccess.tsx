import { useI18n } from '../i18n/I18nContext'
import { Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import type { User } from '../adapters/authAdapter'
import { AccessDeniedPage } from '../pages/AccessDeniedPage'

interface RequireAccessProps {
  allow: (user: User | null) => boolean
  /** Used in the denial message */
  area: 'partner' | 'admin'
}

/**
 * Route guard: renders the child routes only for users that pass `allow`.
 * The backend still checks every request; this keeps the panels from rendering at all.
 */
export function RequireAccess({ allow, area }: RequireAccessProps) {
  const { t } = useI18n()
  const { user, isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="access-check-loading" role="status" aria-live="polite">
        {t('denied.checking')}
      </div>
    )
  }

  if (!isAuthenticated || !allow(user)) {
    return <AccessDeniedPage area={area} signedIn={isAuthenticated} />
  }

  return <Outlet />
}
