import { useState } from 'react'
import { Link, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { BrandLogo } from '../components/BrandLogo'
import { redirectPathFrom } from '../utils/redirect'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { Button } from '../components/Button'
import { PasswordField } from '../components/PasswordField'
import { AuthModeSwitch } from '../components/AuthModeSwitch'
import { authFormProblem } from '../utils/authForm'
import { useI18n } from '../i18n/I18nContext'

export function LoginPage() {
  const { t } = useI18n()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const { login, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to={redirectPathFrom(location.state)} replace />
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    const problem = authFormProblem([email, password], email)
    if (problem) {
      setError(t(problem === 'required' ? 'auth.errRequired' : 'auth.errEmail'))
      return
    }
    setIsLoading(true)

    const response = await login(email, password)
    
    setIsLoading(false)
    
    if (response.success) {
      const from = redirectPathFrom(location.state)
      navigate(from, { replace: true })
    } else {
      setError(response.error || t('auth.errorLogin'))
    }
  }

  return (
    <div className="auth-page">
      <Breadcrumbs />
      <div className="container">
        <BrandLogo variant="auth" />
        <div className="auth-container">
          <AuthModeSwitch mode="login" disabled={isLoading} />

          <div className="auth-header">
            <h1 className="auth-title">{t('auth.welcomeBack')}</h1>
            <p className="auth-subtitle">{t('auth.signInSubtitle')}</p>
          </div>

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-field">
              <label htmlFor="email" className="auth-label">
                {t('auth.email')}
              </label>
              <input
                id="email"
                type="email"
                className="auth-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="email"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="password" className="auth-label">
                {t('auth.password')}
              </label>
              <PasswordField
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="current-password"
              />
              <Link to="/forgot-password" className="auth-link auth-forgot-link">
                {t('auth.forgotPassword')}
              </Link>
            </div>

            <Button type="submit" size="lg" fullWidth className="auth-submit" loading={isLoading} disabled={isLoading}>
              {isLoading ? t('auth.signingIn') : t('auth.signIn')}
            </Button>
          </form>

          <div className="auth-footer">
            <p className="auth-footer-text">
              {t('auth.noAccount')}{' '}
              <Link to="/register" className="auth-link">
                {t('auth.signUp')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
