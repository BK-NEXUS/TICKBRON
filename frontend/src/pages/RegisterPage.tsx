import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { BrandLogo } from '../components/BrandLogo'
import { PhoneInput } from '../components/PhoneInput'
import { isValidPhone, phoneErrorMessage } from '../utils/phone'
import { Breadcrumbs } from '../components/Breadcrumbs'

export function RegisterPage() {
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
    const from = (location.state as any)?.from?.pathname || '/'
    navigate(from, { replace: true })
    return null
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Basic validation
    if (!isValidPhone(formData.phone_number)) {
      setError(phoneErrorMessage())
      return
    }

    if (formData.password !== formData.password_confirm) {
      setError('Passwords do not match')
      return
    }

    if (formData.password.length < 12) {
      setError('Password must be at least 12 characters')
      return
    }

    setIsLoading(true)

    const response = await register(formData)
    
    setIsLoading(false)
    
    if (response.success) {
      const from = (location.state as any)?.from?.pathname || '/'
      navigate(from, { replace: true })
    } else {
      setError(response.error || 'Registration failed. Please try again.')
    }
  }

  return (
    <div className="auth-page">
      <Breadcrumbs />
      <div className="container">
        <BrandLogo variant="auth" />
        <div className="auth-container">
          <div className="auth-header">
            <h1 className="auth-title">Create Account</h1>
            <p className="auth-subtitle">Join TICKBRON to book amazing properties</p>
          </div>

          {error && (
            <div className="auth-error" role="alert">
              {error}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit}>
            <div className="auth-field">
              <label htmlFor="full_name" className="auth-label">
                Full Name
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
              <label htmlFor="email" className="auth-label">
                Email
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
              <label htmlFor="phone_number" className="auth-label">
                Phone Number
              </label>
              <PhoneInput
                id="phone_number"
                name="phone_number"
                className="auth-input"
                value={formData.phone_number}
                onChange={(phone_number) => setFormData(prev => ({ ...prev, phone_number }))}
                required
                disabled={isLoading}
              />
            </div>

            <div className="auth-field">
              <label htmlFor="password" className="auth-label">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                className="auth-input"
                value={formData.password}
                onChange={handleChange}
                required
                disabled={isLoading}
                autoComplete="new-password"
              />
              <p className="auth-hint">Must be at least 12 characters</p>
            </div>

            <div className="auth-field">
              <label htmlFor="password_confirm" className="auth-label">
                Confirm Password
              </label>
              <input
                id="password_confirm"
                name="password_confirm"
                type="password"
                className="auth-input"
                value={formData.password_confirm}
                onChange={handleChange}
                required
                disabled={isLoading}
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary btn-full auth-submit"
              disabled={isLoading}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div className="auth-footer">
            <p className="auth-footer-text">
              Already have an account?{' '}
              <Link to="/login" className="auth-link">
                Sign in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
