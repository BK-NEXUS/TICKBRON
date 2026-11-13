import { useI18n } from '../i18n/I18nContext'
import { Outlet } from 'react-router'
import { useAuth } from '../contexts/AuthContext'
import type { User } from '../adapters/authAdapter'
import { AccessDeniedPage } from '../pages/AccessDeniedPage'

interface RequireAccessProps {
  allow: (user: User | null) => boolean
  /** Ruxsat berilmegen xabarda paydalanıladı */
  area: 'partner' | 'admin'
}

/**
 * Route qorǵawshı: ishki route larǵı tek `allow` dan ótken paydalanıwshılarǵa kórsetedi.
 * Backend ele hár sorawdı tekseredi; bul panellerdiń kórsetiliwiniń aldın aladı.
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
