import { useState } from 'react'
import { Link } from 'react-router-dom'
import { authAdapter } from '../adapters/authAdapter'
import { BrandLogo } from '../components/BrandLogo'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { Button } from '../components/Button'
import { useI18n } from '../i18n/I18nContext'

export function ForgotPasswordPage() {
  const { t } = useI18n()
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [linkSent, setLinkSent] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    setIsLoading(true)

    const response = await authAdapter.requestPasswordReset(email)

    setIsLoading(false)
    if (response.success) {
      setLinkSent(true)
    } else {
      setError(response.error || t('auth.errorResetRequest'))
    }
  }

  return (
    <div className="auth-page">
      <Breadcrumbs />
      <div className="container">
        <BrandLogo variant="auth" />
        <div className="auth-container">
          <div className="auth-header">
            <h1 className="auth-title">{t('auth.forgotTitle')}</h1>
            <p className="auth-subtitle">{t('auth.forgotSubtitle')}</p>
          </div>

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          {linkSent ? (
            <div className="auth-notice" role="status">
              {t('auth.resetLinkSent')}
            </div>
          ) : (
            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="auth-field">
                <label htmlFor="email" className="auth-label">
                  {t('auth.email')}
                </label>
                <input
                  id="email"
                  type="email"
                  className="auth-input"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="email"
                />
              </div>

              <Button type="submit" size="lg" fullWidth className="auth-submit" loading={isLoading} disabled={isLoading}>
                {isLoading ? t('auth.sendingResetLink') : t('auth.sendResetLink')}
              </Button>
            </form>
          )}

          <div className="auth-footer">
            <p className="auth-footer-text">
              <Link to="/login" className="auth-link">
                {t('auth.backToSignIn')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ForgotPasswordPage
