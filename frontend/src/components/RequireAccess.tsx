import { Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import type { User } from '../adapters/authAdapter'
import { AccessDeniedPage } from '../pages/AccessDeniedPage'

interface RequireAccessProps {
  allow: (user: User | null) => boolean
  /** Used in the denial message, e.g. "the admin dashboard" */
  area: string
}

/**
 * Route guard: renders the child routes only for users that pass `allow`.
 * The backend still checks every request; this keeps the panels from rendering at all.
 */
export function RequireAccess({ allow, area }: RequireAccessProps) {
  const { user, isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="access-check-loading" role="status" aria-live="polite">
        Checking access...
      </div>
    )
  }

  if (!isAuthenticated || !allow(user)) {
    return <AccessDeniedPage area={area} signedIn={isAuthenticated} />
  }

  return <Outlet />
}
