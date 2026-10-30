import { cleanField, isPhoneValid } from '../utils/inputFilters'
import { useState } from 'react'
import { Link, Navigate, useNavigate, useLocation } from 'react-router'
import { useAuth } from '../contexts/AuthContext'
import { BrandLogo } from '../components/BrandLogo'
import { redirectPathFrom } from '../utils/redirect'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { Button } from '../components/Button'
import { PasswordField } from '../components/PasswordField'
import { AuthModeSwitch } from '../components/AuthModeSwitch'
import { authFormProblem } from '../utils/authForm'
import { passwordFormatProblem, PASSWORD_PROBLEM_MESSAGE } from '../utils/passwordRules'
import { useI18n } from '../i18n/I18nContext'

export function RegisterPage() {
  const { t } = useI18n()
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    phone_number: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const { register, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to={redirectPathFrom(location.state)} replace />
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: cleanField(e.target.name, e.target.value),
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Basic validation
    const problem = authFormProblem([formData.full_name, formData.email, formData.phone_number, formData.password, formData.password_confirm], formData.email)
    if (problem) {
      setError(t(problem === 'required' ? 'auth.errRequired' : 'auth.errEmail'))
      return
    }

    if (!isPhoneValid(formData.phone_number)) {
      setError(t('auth.errPhone'))
      return
    }

    if (formData.password !== formData.password_confirm) {
      setError(t('auth.errorPasswordMismatch'))
      return
    }

    const passwordProblem = passwordFormatProblem(formData.password)
    if (passwordProblem) {
      setError(t(PASSWORD_PROBLEM_MESSAGE[passwordProblem]))
      return
    }

    setIsLoading(true)

    const response = await register(formData)
    
    setIsLoading(false)
    
    if (response.success) {
      const from = redirectPathFrom(location.state)
      navigate(from, { replace: true })
    } else {
      setError(response.error || t('auth.errorRegister'))
    }
  }

  return (
    <div className="auth-page">
      <Breadcrumbs />
      <div className="container">
        <BrandLogo variant="auth" />
        <div className="auth-container">
          <AuthModeSwitch mode="register" disabled={isLoading} />

          <div className="auth-header">
            <h1 className="auth-title">{t('auth.createAccount')}</h1>
            <p className="auth-subtitle">{t('auth.registerSubtitle')}</p>
          </div>

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="auth-field">
              <label htmlFor="full_name" className="auth-label">
                {t('auth.fullName')}
              </label>
              <input
                id="full_name"
                name="full_name"
                type="text"
                className="auth-input"
                value={formData.full_name}
                onChange={handleChange}
                required
                disabled={isLoading}
                autoComplete="name"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="phone_number" className="auth-label">
                {t('auth.phone')}
              </label>
              <input
                id="phone_number"
                name="phone_number"
                type="tel"
                inputMode="tel"
                className="auth-input"
                value={formData.phone_number}
                onChange={handleChange}
                required
                disabled={isLoading}
                autoComplete="tel"
                placeholder="+998 90 123 45 67"
                aria-describedby="phone_number-hint"
              />
              <span id="phone_number-hint" className="auth-hint">{t('auth.phoneHint')}</span>
            </div>

            <div className="auth-field">
              <label htmlFor="email" className="auth-label">
                {t('auth.email')}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                className="auth-input"
                value={formData.email}
                onChange={handleChange}
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
                name="password"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={isLoading}
                autoComplete="new-password"
              />
              <p className="auth-hint">{t('auth.passwordHint')}</p>
            </div>

            <div className="auth-field">
              <label htmlFor="password_confirm" className="auth-label">
                {t('auth.confirmPassword')}
              </label>
              <PasswordField
                id="password_confirm"
                name="password_confirm"
                value={formData.password_confirm}
                onChange={handleChange}
                required
                disabled={isLoading}
                autoComplete="new-password"
                showLabel={t('auth.showConfirmPassword')}
                hideLabel={t('auth.hideConfirmPassword')}
              />
            </div>

            <Button type="submit" size="lg" fullWidth className="auth-submit" loading={isLoading} disabled={isLoading}>
              {isLoading ? t('auth.creatingAccount') : t('auth.createAccount')}
            </Button>
          </form>

          <div className="auth-footer">
            <p className="auth-footer-text">
              {t('auth.haveAccount')}{' '}
              <Link to="/login" className="auth-link">
                {t('auth.signInLink')}
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
