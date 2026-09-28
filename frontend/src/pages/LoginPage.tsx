import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { BrandLogo } from '../components/BrandLogo'
import { PhoneInput } from '../components/PhoneInput'
import { isValidPhone, phoneErrorMessage } from '../utils/phone'
import { Breadcrumbs } from '../components/Breadcrumbs'

type LoginMethod = 'password' | 'phone'

export function LoginPage() {
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
    const from = (location.state as any)?.from?.pathname || '/'
    navigate(from, { replace: true })
    return null
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const response = await login(email, password)
    
    setIsLoading(false)
    
    if (response.success) {
      const from = (location.state as any)?.from?.pathname || '/'
      navigate(from, { replace: true })
    } else {
      setError(response.error || 'Login failed. Please try again.')
    }
  }

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!isValidPhone(phoneNumber)) {
      setError(phoneErrorMessage())
      return
    }
    setIsLoading(true)

    const otpResponse = await requestOTP(phoneNumber)
    
    setIsLoading(false)
    
    if (otpResponse.success) {
      setOtpRequested(true)
      setTestOtpCode(otpResponse.otp_code)
    } else {
      setError(otpResponse.error || 'Failed to send code. Please try again.')
    }
  }

  const handleOTPSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const response = await loginWithPhoneOTP(phoneNumber, otpCode)
    
    setIsLoading(false)
    
    if (response.success) {
      const from = (location.state as any)?.from?.pathname || '/'
      navigate(from, { replace: true })
    } else {
      setError(response.error || 'Invalid code. Please try again.')
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
      setError(response.error || 'Failed to resend code. Please try again.')
    }
  }

  return (
    <div className="auth-page">
      <Breadcrumbs />
      <div className="container">
        <BrandLogo variant="auth" />
        <div className="auth-container">
          <div className="auth-header">
            <h1 className="auth-title">Welcome Back</h1>
            <p className="auth-subtitle">Sign in to your TICKBRON account</p>
          </div>

          <div className="auth-tabs">
            <button
              type="button"
              className={`auth-tab ${loginMethod === 'password' ? 'active' : ''}`}
              onClick={() => setLoginMethod('password')}
              aria-pressed={loginMethod === 'password'}
              disabled={isLoading}
            >
              Email & Password
            </button>
            <button
              type="button"
              className={`auth-tab ${loginMethod === 'phone' ? 'active' : ''}`}
              onClick={() => setLoginMethod('phone')}
              aria-pressed={loginMethod === 'phone'}
              disabled={isLoading}
            >
              Phone & SMS Code
            </button>
          </div>

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          {loginMethod === 'password' ? (
            <form className="auth-form" onSubmit={handlePasswordSubmit}>
              <div className="auth-field">
                <label htmlFor="email" className="auth-label">
                  Email
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
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  className="auth-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                  autoComplete="current-password"
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-full auth-submit"
                disabled={isLoading}
              >
                {isLoading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          ) : (
            <form className="auth-form" onSubmit={otpRequested ? handleOTPSubmit : handleRequestOTP}>
              <div className="auth-field">
                <label htmlFor="phone_number" className="auth-label">
                  Phone Number
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
                <button
                  type="submit"
                  className="btn btn-primary btn-full auth-submit"
                  disabled={isLoading}
                >
                  {isLoading ? 'Sending code...' : 'Send Code'}
                </button>
              ) : (
                <>
                  <div className="auth-field">
                    <label htmlFor="otp_code" className="auth-label">
                      Enter 6-digit Code
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
                      <small>Test mode code: <strong>{testOtpCode}</strong></small>
                    </div>
                  )}

                  <button
                    type="submit"
                    className="btn btn-primary btn-full auth-submit"
                    disabled={isLoading}
                  >
                    {isLoading ? 'Verifying...' : 'Verify & Sign In'}
                  </button>

                  <button
                    type="button"
                    className="btn btn-link auth-resend"
                    onClick={handleResendOTP}
                    disabled={isLoading}
                  >
                    Resend Code
                  </button>
                </>
              )}
            </form>
          )}

          <div className="auth-footer">
            <p className="auth-footer-text">
              Don't have an account?{' '}
              <Link to="/register" className="auth-link">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
