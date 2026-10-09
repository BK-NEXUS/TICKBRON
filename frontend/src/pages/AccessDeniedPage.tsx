import { useI18n } from '../i18n/I18nContext'
import { Link } from 'react-router-dom'
import { Lock } from 'lucide-react'

interface AccessDeniedPageProps {
  /** What the visitor tried to open */
  area: 'partner' | 'admin'
  /** Anonymous visitors also get a sign-in link */
  signedIn: boolean
}

export function AccessDeniedPage({ area, signedIn }: AccessDeniedPageProps) {
  const { t } = useI18n()
  return (
    <div className="access-denied-page">
      <div className="container">
        <div className="access-denied-card" role="alert">
          <div className="access-denied-icon" aria-hidden="true"><Lock size={40} /></div>
          <h1 className="access-denied-title">{t('denied.title')}</h1>
          <p className="access-denied-message">
            {signedIn
              ? t('denied.signedIn', { area: t(`denied.${area}`) })
              : t('denied.signedOut', { area: t(`denied.${area}`) })}
          </p>
          <div className="access-denied-actions">
            <Link to="/" className="btn btn-primary">{t('common.backHome')}</Link>
            {!signedIn && <Link to="/login" className="btn btn-secondary">{t('auth.signIn')}</Link>}
          </div>
        </div>
      </div>
    </div>
  )
}

export default AccessDeniedPage
