import { useState } from 'react'
import { Link, Navigate, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { BrandLogo } from '../components/BrandLogo'
import { PhoneInput } from '../components/PhoneInput'
import { isValidPhone, phoneExample } from '../utils/phone'
import { redirectPathFrom } from '../utils/redirect'
import { Breadcrumbs } from '../components/Breadcrumbs'
import { Button } from '../components/Button'
import { PasswordField } from '../components/PasswordField'
import { SegmentedControl, type SegmentedOption } from '../components/SegmentedControl'
import { AuthModeSwitch } from '../components/AuthModeSwitch'
import { useI18n } from '../i18n/I18nContext'

type LoginMethod = 'password' | 'phone'

export function LoginPage() {
  const { t } = useI18n()
  const loginMethods: SegmentedOption<LoginMethod>[] = [
    { value: 'password', label: t('auth.methodPassword') },
    { value: 'phone', label: t('auth.methodPhone') },
  ]
  const [loginMethod, setLoginMethod] = useState<LoginMethod>('password')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [phoneNumber, setPhoneNumber] = useState('')
  const [otpCode, setOtpCode] = useState('')
  const [otpRequested, setOtpRequested] = useState(false)
  const [testOtpCode, setTestOtpCode] = useState<string | undefined>(undefined)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  const { login, loginWithPhoneOTP, requestOTP, isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to={redirectPathFrom(location.state)} replace />
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
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

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!isValidPhone(phoneNumber)) {
      setError(t('phone.invalid', { example: phoneExample() }))
      return
    }
    setIsLoading(true)

    const otpResponse = await requestOTP(phoneNumber)
    
    setIsLoading(false)
    
    if (otpResponse.success) {
      setOtpRequested(true)
      setTestOtpCode(otpResponse.otp_code)
    } else {
      setError(otpResponse.error || t('auth.errorSendCode'))
    }
  }

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const response = await loginWithPhoneOTP(phoneNumber, otpCode)
    
    setIsLoading(false)
    
    if (response.success) {
      const from = redirectPathFrom(location.state)
      navigate(from, { replace: true })
    } else {
      setError(response.error || t('auth.errorInvalidCode'))
    }
  }

  const handleResendOTP = async () => {
    setError('')
    setIsLoading(true)

    const response = await requestOTP(phoneNumber)
    
    setIsLoading(false)
    
    if (response.success) {
      setTestOtpCode(response.otp_code)
    } else {
      setError(response.error || t('auth.errorResend'))
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

          <SegmentedControl<LoginMethod>
            fullWidth
            disabled={isLoading}
            aria-label={t('auth.loginMethod')}
            options={loginMethods}
            value={loginMethod}
            onChange={setLoginMethod}
          />

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          {loginMethod === 'password' ? (
            <form className="auth-form" onSubmit={handlePasswordSubmit}>
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
              </div>

              <Button type="submit" size="lg" fullWidth className="auth-submit" loading={isLoading} disabled={isLoading}>
                {isLoading ? t('auth.signingIn') : t('auth.signIn')}
              </Button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={otpRequested ? handleOTPSubmit : handleRequestOTP}>
              <p className="auth-hint">{t('auth.smsNeedsVerifiedPhone')}</p>
              <div className="auth-field">
                <label htmlFor="phone_number" className="auth-label">
                  {t('auth.phone')}
                </label>
                <PhoneInput
                  id="phone_number"
                  className="auth-input"
                  value={phoneNumber}
                  onChange={setPhoneNumber}
                  required
                  disabled={isLoading || otpRequested}
                />
              </div>

              {!otpRequested ? (
                <Button type="submit" size="lg" fullWidth className="auth-submit" loading={isLoading} disabled={isLoading}>
                  {isLoading ? t('auth.sendingCode') : t('auth.sendCode')}
                </Button>
              ) : (
                <>
                  <div className="auth-field">
                    <label htmlFor="otp_code" className="auth-label">
                      {t('auth.enterCode')}
                    </label>
                    <input
                      id="otp_code"
                      type="text"
                      className="auth-input"
                      value={otpCode}
                      onChange={(e) => setOtpCode(e.target.value)}
                      required
                      disabled={isLoading}
                      maxLength={6}
                      pattern="[0-9]{6}"
                      placeholder="123456"
                      autoComplete="one-time-code"
                    />
                  </div>

                  {testOtpCode && import.meta.env.MODE !== 'production' && (
                    <div className="auth-test-mode">
                      <small>{t('auth.testCode')} <strong>{testOtpCode}</strong></small>
                    </div>
                  )}

                  <Button type="submit" size="lg" fullWidth className="auth-submit" loading={isLoading} disabled={isLoading}>
                    {isLoading ? t('auth.verifying') : t('auth.verifyAndSignIn')}
                  </Button>

                  <Button variant="link" className="auth-resend" onClick={handleResendOTP} disabled={isLoading}>
                    {t('auth.resendCode')}
                  </Button>
                </>
              )}
            </form>
          )}

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
