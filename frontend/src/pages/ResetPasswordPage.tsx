import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { authAdapter } from '../adapters/authAdapter'
import { BrandLogo } from '../components/BrandLogo'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { Button } from '../components/Button'
import { NewPasswordFields } from '../components/NewPasswordFields'
import { useI18n } from '../i18n/I18nContext'
import { formAccepts } from '../utils/formProblem'
import { newPasswordProblem } from '../utils/passwordRules'

const INVALID_LINK_CODE = 'invalid_reset_link'

/** The page the e-mailed link opens: /reset-password?uid=...&token=... */
export function ResetPasswordPage() {
  const { t } = useI18n()
  const [searchParams] = useSearchParams()
  const uid = searchParams.get('uid') ?? ''
  const token = searchParams.get('token') ?? ''

  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [linkRejected, setLinkRejected] = useState(false)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    if (!formAccepts(event.currentTarget, t, setError)) return

    const problem = newPasswordProblem(password, confirmation)
    if (problem) {
      setError(t(problem === 'mismatch' ? 'auth.errorPasswordMismatch' : 'auth.errorPasswordShort'))
      return
    }

    setIsLoading(true)
    const response = await authAdapter.confirmPasswordReset({ uid, token, password, password_confirm: confirmation })
    setIsLoading(false)

    if (response.success) {
      setDone(true)
    } else if (response.code === INVALID_LINK_CODE) {
      setLinkRejected(true)
    } else {
      setError(response.error || t('auth.errorResetConfirm'))
    }
  }

  const linkIsUnusable = linkRejected || !uid || !token

  return (
    <div className="auth-page">
      <Breadcrumbs />
      <div className="container">
        <BrandLogo variant="auth" />
        <div className="auth-container">
          <div className="auth-header">
            <h1 className="auth-title">{t('auth.resetTitle')}</h1>
            {!done && !linkIsUnusable && <p className="auth-subtitle">{t('auth.resetSubtitle')}</p>}
          </div>

          {done ? (
            <>
              <div className="auth-notice" role="status">
                {t('auth.passwordChanged')}
              </div>
              <Link to="/login" className="auth-link">
                {t('auth.signInLink')}
              </Link>
            </>
          ) : linkIsUnusable ? (
            <>
              <div className="auth-error" role="alert">
                {t('auth.resetLinkInvalid')}
              </div>
              <Link to="/forgot-password" className="auth-link">
                {t('auth.requestNewLink')}
              </Link>
            </>
          ) : (
            <>
              {error && (
                <div className="auth-error" role="alert">
                  {error}
                </div>
              )}
              <form className="auth-form" onSubmit={handleSubmit} noValidate>
                <NewPasswordFields
                  password={password}
                  confirmation={confirmation}
                  onPasswordChange={setPassword}
                  onConfirmationChange={setConfirmation}
                  disabled={isLoading}
                />
                <Button type="submit" size="lg" fullWidth className="auth-submit" loading={isLoading} disabled={isLoading}>
                  {isLoading ? t('auth.savingPassword') : t('auth.savePassword')}
                </Button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ResetPasswordPage
